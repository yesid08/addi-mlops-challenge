# Part 7 — Clarification for Reviewers: What We Didn't Build (and Why It Matters)

> **"The best architecture is the one you can explain — including what you chose not to build."**

---

## 7.1 — What Was Delivered and Why

The API delivered across Parts 1–6 is a **fully synchronous HTTP REST API**. Every endpoint (`POST /chat`, `GET /health`, feedback, history) follows the standard request-response cycle over HTTP.

This was **intentional**, not an oversight:

- HTTP REST is synchronous, making it easy to test with `pytest`, `curl`, and standard CI/CD pipelines.
- The challenge scope was operationalization — containerization, A/B testing, observability, release strategy — not transport-layer design.
- A working, tested, containerized HTTP API demonstrates all required MLOps concepts cleanly.

However, for a **conversational AI messaging service** like Emporyum Tech's assistant, HTTP REST is not the ideal transport at scale. This document explains what the ideal architecture looks like, why it was not implemented in this challenge, and — most importantly — the precise reasoning behind the trade-offs.

---

## 7.2 — Why WebSocket Is the Ideal Transport for Conversational AI

A conversational AI assistant is fundamentally a **long-lived, interactive session**. The user sends messages and expects a response — then continues the conversation. This pattern maps naturally to a **persistent, bidirectional WebSocket connection**.

### The connection IS the session

In the HTTP model, every turn requires:
1. Client opens a TCP+TLS connection.
2. Client sends HTTP request.
3. Server processes and responds.
4. Connection closes (or is returned to a pool).

The `conversation_id` is just a header — it reconstructs context that already existed. In the WebSocket model:

1. Client opens a WebSocket once (one TCP+TLS handshake).
2. Every subsequent message is a lightweight frame over the existing connection.
3. The server can push responses as they are generated — token by token, without the client polling.
4. The connection itself IS the session identifier. `conversation_id` is set at handshake time and never repeated.

### Comparison: HTTP REST vs. WebSocket

| Dimension | HTTP REST (delivered) | WebSocket (ideal) |
|-----------|----------------------|-------------------|
| Latency per turn | Full TCP + TLS handshake per request | Reused connection, ~0 ms connection overhead |
| Streaming | Not native — requires SSE workaround | Native frame-by-frame, token streaming |
| Connection state | Stateless — session rebuilt from header | Stateful — session lives in the open socket |
| Back-pressure | None — clients can send arbitrarily fast | Connection count is a natural load cap |
| Testing complexity | Low — curl/pytest works out of the box | Higher — requires a WebSocket client |
| CI/CD suitability | High — standard HTTP contracts | Lower — connection lifecycle adds complexity |
| Challenge fit | High | Lower for demonstrating operationalization concepts |

---

## 7.3 — Why SQS Is Not the Right Choice Either

An SQS-backed architecture would look like:

```
Client → HTTP POST /chat → API (202 Accepted + job_id) → SQS FIFO → Worker → SSE/polling for result
```

This solves the synchronous blocking problem, but it creates a different set of issues for real-time conversation:

| Problem | Detail |
|---------|--------|
| **Polling latency** | SQS long-polling adds 100–500 ms baseline latency before the worker even sees the message |
| **job_id indirection** | The client must track a `job_id` and either poll or subscribe to a separate SSE stream — a worse UX than a single socket |
| **Visibility timeout management** | If the worker crashes mid-processing, the message reappears after the visibility timeout. For idempotent LLM calls this is manageable but adds complexity |
| **Dead-letter queue overhead** | Poison-pill messages need DLQ handling, alerting, and replay logic |
| **Conversation ordering** | SQS FIFO maintains order per `MessageGroupId`, but the client must deduplicate out-of-order delivery on retry |

SQS is the right tool for **fire-and-forget batch workloads** — nightly re-embedding, analytics pipelines, async report generation. For an interactive messaging service, it adds latency and complexity where WebSocket removes both.

---

## 7.4 — Redis as the Central Coordination Layer

The ideal architecture uses Redis for **all coordination** — the same Redis instance already present for conversation history (Part 5) now serves five roles:

### Role 1 — Connection Registry

When a client opens a WebSocket connection, the receiving Fargate task writes:

```
ws:registry:{conversation_id}  →  fargate_task_id   (TTL = session duration)
```

Any task can look up which task holds a given conversation's socket, enabling cross-task response delivery.

### Role 2 — Pub/Sub Result Delivery

After running LangGraph, the processing task publishes the result:

```
PUBLISH ws:channel:{conversation_id}  "{response payload}"
```

Every Fargate task subscribes to channels for connections it owns. The correct task receives the message and pushes it to the open socket — even if processing happened on a different task. No polling, no job_id.

### Role 3 — Conversation History (hot cache)

Same two-tier design from Part 5: Redis for the last N turns (fast reads), DynamoDB for durable persistence. Unchanged.

### Role 4 — A/B Bucketing Cache

The SHA-256 hash assignment (Part 2) is computed once and cached:

```
ab:bucket:{user_id}  →  "A" | "B"   (TTL = experiment lifetime)
```

No recomputation per request.

### Role 5 — Bucket Ticketing (Token Bucket Rate Limiter)

This is the **real scaling problem** at 10 000 concurrent users.

**The math:** 10 000 users, each sending one message every 5 seconds = **2 000 LLM requests/second**. OpenAI enforces strict TPM (tokens per minute) and RPM (requests per minute) limits. Exceeding them returns HTTP 429 errors, breaking conversations.

**Solution — Redis token bucket:**

```
INCR  rate:global:openai      # atomic increment
EXPIRE rate:global:openai 60  # sliding 60-second window
```

Before each LangGraph call, the Fargate task draws a token from the bucket. If the counter exceeds the configured RPM ceiling, the request is held.

**Exponential backoff when the bucket is empty:**

Instead of immediately retrying (which would cause a thundering-herd — all 2 000 waiting tasks hammering Redis simultaneously), the Fargate task backs off exponentially:

```
attempt 1: wait  100 ms
attempt 2: wait  200 ms
attempt 3: wait  400 ms
attempt 4: wait  800 ms
attempt 5: wait 1600 ms
cap:        4000 ms
```

This is critical. Without backoff, rate-limited tasks all retry at the same millisecond, creating a burst that overwhelms both Redis and the next available RPM window. With exponential backoff, retries are spread across time — throughput is maintained at the maximum sustainable rate rather than oscillating between saturation and starvation.

While the task waits, the client receives a WebSocket frame:

```json
{"type": "wait", "retry_after_ms": 400, "message": "procesando..."}
```

The user sees a loading indicator — no silent timeout, no dropped message.

Redis solves this in **O(1) per request** with atomic `INCR` operations, distributed across all Fargate tasks with zero coordination overhead beyond the single Redis write.

---

## 7.5 — Fargate Auto-scaling Based on Alive Connections

With WebSockets, the natural scaling signal is **the number of alive connections per task** — not CPU or memory, which are lagging indicators for I/O-bound async workloads.

### Scaling architecture

Each Fargate task exposes a custom CloudWatch metric:

```
Namespace: EmporyumTech/WebSocket
MetricName: ActiveWebSocketConnections
Dimension: TaskId = <fargate-task-id>
```

Published every 30 seconds via a background coroutine inside each task.

**AWS ECS Application Auto Scaling policy (target tracking):**

| Condition | Action |
|-----------|--------|
| Average `ActiveWebSocketConnections` > 400 | Add tasks (scale out) |
| Average `ActiveWebSocketConnections` < 200 | Remove tasks (scale in) |
| Target steady-state | ~500 connections/task |

**Why 500 connections/task?**

Each LangGraph turn is async but CPU+memory-bound during the OpenAI call (~1–3 s). At ~500 simultaneous in-flight requests per task you approach typical container resource saturation. The 400/200 thresholds provide headroom to absorb traffic spikes before new tasks are ready (ECS task startup is ~30–60 s).

**Scale-in (graceful drain):**

Before a task is terminated, it:
1. Broadcasts `{"type": "reconnect", "reason": "scale_in"}` to all open sockets.
2. Waits up to 30 s for clients to reconnect to other tasks.
3. Deregisters from the ALB target group.
4. Exits cleanly.

Clients implement exponential backoff on reconnect — same pattern as the token bucket, same thundering-herd prevention.

**No Kubernetes required.** ECS + ALB + CloudWatch Application Auto Scaling is the fully managed, serverless-friendly path on AWS. It handles the same scaling problem with zero cluster management overhead.

---

## Summary

| Decision | What Was Built | What Would Be Ideal |
|----------|---------------|---------------------|
| Transport | HTTP REST | WebSocket (persistent, bidirectional) |
| Async backbone | Synchronous (blocking) | Redis Pub/Sub (push-based) |
| Session model | `conversation_id` header | WebSocket connection = session |
| Rate limiting | Per-user token bucket in `FeedbackStore` | Redis global token bucket + exponential backoff |
| Scaling signal | N/A (single process) | `ActiveWebSocketConnections` → ECS auto-scale |
| Queueing | None (sync) | No queue needed — WebSocket + Redis replaces SQS |

The HTTP REST API delivered in this challenge is production-quality within its design constraints. The WebSocket + Redis architecture described here is the natural evolution for a messaging service operating at scale — and the reasoning behind both choices is what matters most in production MLOps.
