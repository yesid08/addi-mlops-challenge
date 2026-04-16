# Part 5 — Production Readiness

---

## 5.1 — State Management

The current `MemorySaver` is single-process and in-memory — it cannot survive a restart, be shared across API instances, or scale horizontally. The production architecture replaces it with a two-tier store: **Redis Cluster** as the hot cache for active conversations and **DynamoDB** as the durable persistence layer. Redis holds the last 10 turns per conversation (sufficient for LLM context continuity), with a TTL of 24 hours of inactivity to bound memory consumption and automatically evict cold sessions. This replacement is transparent to the LangGraph graph because LangGraph abstracts all checkpoint access behind the `BaseCheckpointSaver` interface; the swap from `MemorySaver` to `langgraph-checkpoint-redis` at startup requires no changes to node logic.

Rather than writing every turn to DynamoDB synchronously (which would couple user-facing latency to persistence I/O), a **write-behind batch strategy** is used: every 5 turns or a maximum of 1 hour per conversation, a background worker flushes the Redis buffer to DynamoDB asynchronously. This decouples latency from persistence and reduces DynamoDB write throughput demand significantly. The tradeoff is explicit and acceptable: if a Redis instance dies between flush cycles, up to 5 turns of history may be lost. For a commercial e-commerce chatbot — not a financial transaction system — this consistency tradeoff is reasonable.

Redis is horizontally scaled using **Redis Cluster**, which distributes conversation keys across shards via consistent hashing. Each `conversation_id` maps deterministically to a shard, ensuring all reads and writes for a given conversation route to the same node without cross-shard coordination. Redis Cluster also supports primary-replica replication and automatic failover with AOF persistence enabled, which means Redis durability is opt-in and deliberately configured rather than absent by design. Redis is not the source of truth — DynamoDB is — but it is highly available.

For analytics workloads — turn-level metrics, topic distribution, drop-off rates, A/B experiment signals — DynamoDB is treated as a raw event log, not a query target. Mixing analytical aggregations against the production conversation store would degrade OLTP performance. Instead, a separate data engineering pipeline (medallion architecture: bronze raw events → silver cleaned turns → gold aggregated metrics) ingests from DynamoDB into a columnar store such as Redshift or Athena on S3. This keeps production latency isolated from OLAP queries entirely.

---

## 5.2 — Security

Prompt injection prevention is implemented in two phases integrated directly into the LangGraph pipeline. **Phase 1** adds a rule-based pre-filter at the API boundary before the graph executes: incoming messages are scanned against regex patterns for common injection phrases (`"ignore previous instructions"`, `"you are now"`, `"forget your system prompt"`). This is zero-cost, adds negligible latency, and catches the majority of off-the-shelf attacks. On top of this, a dedicated LangGraph node evaluates the sanitized message with a tightly-scoped LLM prompt designed exclusively to classify injection attempts before the main `fetch_user_data → handle_general` flow runs. **Phase 2**, as the system matures, replaces or augments the LLM node with a fine-tuned transformer classifier — either a custom BERT trained on labeled examples from this domain or an existing production tool such as Meta's `PromptGuard` or `llm-guard`. The build-vs-buy decision depends on whether Colombian e-commerce-specific injection patterns are poorly covered by general-purpose models.

If injection is detected at any phase, the request is aborted before the knowledge base or user data is ever queried. This is the critical control: the most dangerous injection outcome is an attacker exploiting the retrieval step to exfiltrate internal product, pricing, or user data. The existing `data_filter.py` already enforces topic-scoped field access (only fields relevant to the selected topic are passed to the LLM); this is extended with user-level authorization checks — payment and order details for a given transaction are only included in the LLM context if the authenticated user owns that transaction. Sensitive data is never speculatively included.

Authentication is enforced at the API boundary via **JWT tokens**. The current implementation accepts any `user_id` in any `/chat` or `/history` request without verification, which allows full identity impersonation. Every request must carry a valid signed token; `user_id` is extracted from the token, not from the request body. Per-user rate limiting (e.g., 10 requests per minute) is enforced via a **Redis sliding window counter** (`INCR` + `EXPIRE`) — distributed across all FastAPI instances, unlike an in-memory counter which would be ineffective with horizontal scaling.

Secrets management moves the `OPENAI_API_KEY` out of the `.env` file currently mounted via `docker-compose.yml` and into **AWS Secrets Manager**, injected as environment variables at container runtime. Keys are never baked into the Docker image at build time or committed to the repository. Secrets rotation is automated with rolling restarts to propagate changes with zero downtime. PII in logs is controlled in two layers: first, structured logging ensures message content is never written to log fields — the existing `RequestLoggingMiddleware` logs only `method`, `path`, `status`, and `duration`, never the user's message text. As a second layer for indirect leakage, a BERT-based NER model masks any PII reaching logs by replacing entity values with `[PII]` tokens before emission.

---

## 5.3 — Cost Optimization

LLM token consumption is monitored at three granularities: **per turn**, **per conversation**, and **per user**. LangChain's callback system (`on_llm_end`) captures input and output token counts from every OpenAI API response and emits them as structured log events tagged with `user_id`, `conversation_id`, and `ab_variant`. These events feed a cost dashboard with daily spend totals, per-user token consumption rankings, and threshold alerts — for example, alerting when a single user exceeds 5× the daily average (likely abuse or a runaway client loop). Per-user token caps can enforce hard cutoffs before they become budget incidents.

The highest-leverage cost reduction is **OpenAI prompt caching**. The system prompt in this application — knowledge base content, behavioral instructions, topic definitions — is static across every request. Structuring the prompt so this static prefix always appears first and is byte-identical across calls enables OpenAI's prefix caching, which can reduce token costs by up to 50% on cached tokens with no change to response quality. **Semantic caching** is the second major lever: incoming user messages are embedded and compared via cosine similarity against a vector index of previously answered questions (implemented with Redis + embeddings or a tool like `GPTCache`). If similarity exceeds a threshold, the cached response is returned without an LLM call at all. For a Colombian e-commerce bot, a large fraction of messages are predictable (`"¿cuándo llega mi pedido?"`, `"¿cómo hago una devolución?"`); semantic cache hit rates of 20–40% are realistic and eliminate those LLM calls entirely.

Outbound rate control to the OpenAI API uses a **token bucket algorithm** rather than a simple semaphore. A semaphore limits concurrency (how many coroutines run simultaneously) but does not control throughput over time; a token bucket controls the rate of requests per second, which is what OpenAI's RPM and TPM limits actually enforce. When the bucket is exhausted, requests queue briefly rather than failing, and retries apply exponential backoff with jitter to avoid thundering-herd reconvergence. Request batching in the traditional sense does not apply to real-time conversational AI — users expect sub-second acknowledgement — but batch processing is used for offline workloads: embedding generation for the semantic cache, analytics preprocessing, and bulk user data preloading for cold-start optimization.

---

## 5.4 — Scaling Architecture

The target architecture for 10,000 concurrent conversations decouples request intake from LLM processing through an asynchronous queue. At 10,000 concurrent sessions with an average activity rate of 2 turns per minute, steady-state demand is approximately 333 LLM requests per second — well beyond what a synchronous request-per-thread model can handle within OpenAI's rate limits. The solution is to make every `/chat` call non-blocking: the intake layer is a set of **horizontally scaled FastAPI instances** behind an Application Load Balancer, auto-scaled by Kubernetes HPA on CPU and queue depth. When a user sends a message, the intake FastAPI validates the request, publishes it to an **SQS FIFO queue** (using `conversation_id` as the message group ID to guarantee per-conversation ordering), and immediately returns `202 Accepted` with a `job_id`. The client holds a **WebSocket or SSE connection** open to receive the result asynchronously once processing completes.

The SQS queue triggers **Lambda functions** (or ECS Fargate tasks for workloads requiring longer execution or sustained throughput beyond Lambda's concurrency ceiling) which act as the LangGraph workers. Each worker executes the following sequence: (1) acquires a **per-conversation distributed lock** from Redis to prevent two workers from processing overlapping messages for the same conversation simultaneously — a race condition that would corrupt the checkpoint state; (2) fetches the last 10 turns of conversation history from **Redis Cluster**; (3) executes the LangGraph `fetch_user_data → handle_general` graph, calling the OpenAI API; (4) writes the completed turn and LLM result back to Redis and schedules a batch flush to **DynamoDB**; (5) publishes the response to the client's WebSocket/SSE channel; (6) deletes the message from the SQS queue to acknowledge completion. Lambda concurrency limits act as a natural global rate control on outbound LLM calls, complementing the token bucket throttler.

The primary bottlenecks at this scale and their mitigations are: **LLM API latency** (2–5 seconds average per call) is the dominant source of user-perceived latency — mitigated by the async queue so users receive immediate acknowledgement and wait only for their specific turn to be processed, not behind other users' turns; **DynamoDB write throughput** under burst load is mitigated by write-behind batching and on-demand capacity provisioning; **Redis memory** is bounded by the 24-hour TTL and 10-turn cap per conversation, making memory consumption predictable and linearly proportional to active session count. The overall architecture is summarized below:

```
User
 │
 ▼
ALB → FastAPI (N instances, HPA)
         │  202 + job_id
         ▼
      SQS FIFO Queue (grouped by conversation_id)
         │
         ▼
      Lambda / ECS Workers
         │  ① Redis lock
         │  ② Redis → fetch last 10 turns
         │  ③ LangGraph graph → OpenAI API
         │  ④ Redis write + async DynamoDB batch
         │  ⑤ WebSocket/SSE → response to user
         │  ⑥ SQS delete
         ▼
      Redis Cluster (hot cache, 24h TTL)
      DynamoDB (durable store, write-behind)
```
