# Part 4 — Observability & Monitoring

---

## 4.1 — Instrumentation Implementation

### What was implemented

Three layers of observability were added to the live codebase with no new runtime dependencies (stdlib `json`, `logging`, `contextvars`, `time` only).

#### Structured JSON logging

**Problem:** `logging.basicConfig()` emitted plain strings that cannot be parsed or aggregated by log tooling (Loki, CloudWatch Insights, Datadog, etc.).

**Solution:** A custom `JsonFormatter` (`app/logging_config.py`) serialises every `LogRecord` to a single-line JSON object. All callers pass structured fields via `extra={}` instead of string interpolation.

Every log line now contains:

```json
{
  "timestamp": "2026-04-15T14:32:01.123Z",
  "level": "INFO",
  "logger": "app.routers.chat",
  "message": "chat_ok",
  "correlation_id": "a1b2-c3d4-...",
  "user_id": "user_001",
  "conversation_id": "conv-42",
  "variant": "A",
  "flow": ["fetch_user_data", "handle_general"]
}
```

The `correlation_id` is propagated automatically via a `ContextVar` (`app/context.py`) set by `CorrelationIdMiddleware` — no manual threading through function signatures required.

#### Token usage capture

**Problem:** `chain.ainvoke()` discards the OpenAI response metadata, so prompt/completion token counts were invisible.

**Solution:** `TokenUsageCallback` (`source/adapters/chains/callbacks.py`) implements LangChain's `BaseCallbackHandler.on_llm_end()`, which receives the full `LLMResult` including `token_usage`. It is passed per-call via `config={"callbacks": [cb]}`, keeping it stateless and safe for concurrent requests.

The `handle_general` node (`source/domain/handle_general.py`) now emits:

```json
{
  "message": "llm_call",
  "node": "handle_general",
  "llm_duration_ms": 1240.5,
  "prompt_tokens": 842,
  "completion_tokens": 97,
  "total_tokens": 939,
  "model": "gpt-4o-mini",
  "user_id": "user_001",
  "conversation_id": "conv-42"
}
```

#### Per-request HTTP log

`RequestLoggingMiddleware` now emits a structured entry per request:

```json
{
  "message": "http_request",
  "method": "POST",
  "path": "/chat",
  "status": 200,
  "duration_ms": 1312.8,
  "correlation_id": "a1b2-c3d4-..."
}
```

### Files changed / created

| File | Change |
|------|--------|
| `app/context.py` | **new** — `correlation_id_var` ContextVar |
| `app/logging_config.py` | **new** — `JsonFormatter` + `setup_logging()` |
| `source/adapters/chains/callbacks.py` | **new** — `TokenUsageCallback` |
| `app/main.py` | `basicConfig` → `setup_logging()` |
| `app/middleware/correlation.py` | Sets `correlation_id_var` on every request |
| `app/middleware/logging.py` | Structured `extra={}` dict instead of `%s` string |
| `app/routers/chat.py` | Structured entries for `chat_ok`, `chat_timeout`, `chat_error` |
| `source/domain/handle_general.py` | Token callback, per-call timing, `logger.exception` replaces `print()` |

### Metrics now available from logs

| Metric | Source log message | Fields |
|--------|--------------------|--------|
| Request latency (P50/P95/P99) | `http_request` | `duration_ms` |
| LLM call latency | `llm_call` | `llm_duration_ms` |
| Token usage per turn | `llm_call` | `prompt_tokens`, `completion_tokens`, `total_tokens` |
| Cost proxy per conversation | aggregate `total_tokens` by `conversation_id` | — |
| Error rate by type | `chat_timeout`, `chat_error`, `handle_general_error` | — |
| A/B variant per request | `chat_ok` | `variant` |

---

## 4.2 — Monitoring Dashboard Design

Three dashboard layers, each with its own time granularity and audience.

### System Health — operational (1-min rolling to daily)

| Panel | Description |
|-------|-------------|
| Request success rate | HTTP 2xx / total requests — primary availability signal |
| HTTP 5xx error rate | Broken down by source: LLM API, internal app, infra |
| P50 / P95 / P99 latency | Per-endpoint (`/chat`, `/health`); percentiles expose tail latency averages hide |
| Concurrent active conversations | Real-time concurrency; predicts saturation before errors appear |
| Service health status | `GET /health` probe result — `ok` vs `degraded` |
| Container restarts | Memory leaks and crash loops show here first |
| CPU / Memory usage | Resource saturation leading indicator |

### Business Metrics — strategic (weekly to quarterly)

| Panel | Description |
|-------|-------------|
| Explicit satisfaction rate | Good / (good + bad) ratings per variant (A vs B comparison panel) |
| Implicit sentiment trend | BERT-based sentiment score averaged per day over full conversations |
| Topic distribution | Which of the 7 KB topics (PEDIDOS, PAGOS, DEVOLUCIONES, etc.) are most requested — informs roadmap |
| Payment support rate | Conversations with at least one PAGOS/DEVOLUCIONES turn — operational load signal |
| Purchase intent conversion | Conversations with at least one credit/product intent turn / total conversations |
| Average turns per conversation | Proxy for resolution quality; high turn counts signal bot is not resolving |
| A/B variant comparison | Side-by-side: satisfaction, average turns, topic distribution, sentiment — primary experiment readout |

### LLM-Specific Metrics — ML/cost (daily to weekly)

| Panel | Description |
|-------|-------------|
| Daily LLM cost (USD) | Dollar amount over time — more actionable than raw token counts |
| Tokens per conversation (histogram) | Distribution view; outliers indicate runaway loops or injection attempts |
| Tokens per turn (P50/P95) | Per-turn cost trend per variant |
| Time to first token (P95) | User-perceived latency; tracks LLM provider health |
| BERT sentiment score trend | Rolling average — downward drift without deployment = model degradation signal |
| Prompt injection attempt count | Classifier output aggregated per hour |
| LLM error rate | Rate limit hits and timeouts from OpenAI specifically — separate from app error rate |

> **Note on data stores:** Operational metrics → Prometheus (short retention, high write throughput). Business and LLM quality metrics → data warehouse / BI tool (Metabase, Looker) for aggregation and stakeholder access.

---

## 4.3 — Alert Rules

| # | Metric | Threshold | Severity | Action |
|---|--------|-----------|----------|--------|
| 1 | HTTP 5xx error rate | > 5% over 5 min | Critical | Page on-call; inspect app logs; check OpenAI status page |
| 2 | `GET /health` response | Non-200 for > 1 min | Critical | PagerDuty; if recent deployment → rollback to previous stable tag |
| 3 | P95 time to first token | > 3 000 ms = Warning / > 4 000 ms = Critical | Warning / Critical | Warning: monitor; Critical: check OpenAI status, reduce `MAX_CONVERSATION_HISTORY` as a temporary relief |
| 4 | Tokens per conversation | > 35 000 = Warning / > 45 000 = Critical | Warning / Critical | Pull top-10 conversations by token count; investigate for loops or unusually long histories |
| 5 | Daily LLM cost | > 2× 7-day rolling average | Critical | Page on-call; inspect token distribution per conversation; identify outlier `conversation_id`s |
| 6 | BERT negative sentiment rate | > 10% in last 24 h = Warning / > 15% = Critical | Warning / Critical | Warning: generate automated root-cause report (see §4.5); Critical: set `AB_TREATMENT_TRAFFIC_PCT=0`, open ML incident |
| 7 | Explicit negative feedback rate | > 10% = Warning / > 15% = Critical | Warning / Critical | Warning: automated report; Critical: rollback + pull sample of flagged conversations for manual review |
| 8 | Prompt injection attempts | 1–5 per hour = Warning / > 5 per hour = Critical | Warning / Critical | Flag `user_id`s involved; review flagged inputs; consider temporary rate limiting on affected IPs |

> **Severity policy:** Warning = Slack notification, reviewed next business day. Critical = PagerDuty, on-call engineer responds within 15 min regardless of hour.

---

## 4.4 — LLM-Specific Monitoring

| Concern | Detection approach |
|---------|--------------------|
| **Model degradation** | BERT sentiment score trend (daily rolling average) + explicit feedback rate. A downward drift in both without a recent deployment is the primary signal. Validated against positive conversation samples for RAGAS/Phoenix/DeepEval regression testing. |
| **Cost anomalies** | Daily cost vs 7-day rolling average (Alert #5). Token distribution histogram surfaces outlier conversations. Token count per turn tracked per variant to attribute cost to Version A vs B. |
| **Latency degradation** | P95 time to first token tracked over time (Alert #3). Separate panel for LLM-specific errors (rate limits, timeouts) isolates provider-side issues from app-side. |
| **Prompt injection attempts** | Dedicated classifier model outputs attempt count per hour (Alert #8). Tokens wasted per flagged turn tracked to quantify cost impact. `user_id`s and input patterns logged for forensic review. |

---

## 4.5 — LLM Output Drift Detection

Model degradation in production LLM systems rarely announces itself with a spike in HTTP 5xx errors. The more common pattern is **silent drift**: the model begins producing subtly shorter, less specific, or tonally different responses over days or weeks — invisible to latency and error rate monitors, but eroding user experience. The following signals detect drift independently of explicit user feedback.

**What to measure**

| Signal | Method | Alert threshold |
|---|---|---|
| Response length distribution | Track p50 and p95 of `completion_tokens` per turn as a 7-day rolling window | Warning if p50 shifts > 20% from baseline; Critical if > 40% |
| Semantic similarity to baseline | Embed `respuesta_final` outputs with a lightweight model (e.g., `text-embedding-3-small`). Compute cosine similarity between each response and the centroid of the first 7-day baseline window | Warning if 7-day rolling mean similarity drops below 0.80; Critical below 0.70 |
| Topic distribution drift | Expected KB topic distribution (PEDIDOS, PAGOS, DEVOLUCIONES, etc.) computed from first 30 days of production traffic. Compare weekly observed distribution using KL divergence | Warning if KL divergence > 0.1; investigate if > 0.2 |
| Vocabulary shift | Track the top-50 token n-grams in `respuesta_final` weekly. Sudden appearance of new high-frequency tokens (e.g., English phrases in a Spanish-language bot) signals prompt contamination or model update | Manual review triggered on any top-10 token change |
| RAGAS quality metrics | Sample 1% of production turns; evaluate faithfulness, answer relevance, and context precision against the knowledge base using RAGAS or DeepEval in an async batch job | Alert if faithfulness drops below 0.80 on weekly sample |

**Baseline and rebase policy**

The reference distribution is established from the first 7 days of stable production traffic after a clean deployment. When a new version is promoted to 100%, the baseline is frozen at that point — not updated continuously — so drift is always measured against the last known-good behavior, not against a moving average that silently absorbs degradation.

After a deliberate model change (e.g., a prompt update or temperature change), the baseline is explicitly rebased: the old baseline is archived with a timestamp, and the new 7-day window begins. This ensures drift alerts are not suppressed by intentional changes and that historical baselines remain available for post-mortem analysis.

**Integration with alert rules**

Drift signals feed directly into Alert #6 (BERT negative sentiment) and the quality SLO track in Section 4.5. A sustained drop in semantic similarity without a recent deployment is escalated as an ML incident — not an operational one — and triggers the investigation-first response track: automated root-cause report, sampling of affected conversations, comparison against the frozen baseline.

---

## 4.6 — SLOs and SLIs

| SLI | Target SLO | Measurement Method |
|-----|------------|--------------------|
| P90 response time per `/chat` turn | < 2 000 ms | Prometheus histogram on `/chat` endpoint |
| Service availability | ≥ 99% | Synthetic probe on `GET /health` every 30 s |
| Request success rate | ≥ 99% HTTP 2xx | Prometheus counter on `/chat` endpoint |
| Conversation length | ≤ 15 turns in 90% of `conversation_id`s | Turn count queried from `ConversationHistoryStore` daily |
| BERT sentiment (positive) | ≥ 90% of conversations | Async BERT pipeline output, aggregated daily |
| Explicit satisfaction rate | ≥ 85% good ratings | `GET /ab/feedback/summary` — `good / (good + bad)` |

**Error budget policy:**

Two response tracks based on SLI type:

1. **Operational SLOs** (latency, availability, success rate) — automated canary rollback: set `AB_TREATMENT_TRAFFIC_PCT=0` to route 100% traffic to Version A immediately. If a recent deployment is the likely cause, roll back to the previous stable image tag.

2. **Quality SLOs** (sentiment, satisfaction, cost) — investigation-first: an automated report is generated via LLM analysis (Claude Code) over system logs and captured metrics. Findings are grouped into categories (e.g., topic cluster, user segment, time window). Each group is investigated to determine root cause. Action depends on findings: rollback / extended 24–48 h analysis / targeted patch.

**Cross-cutting rules:**
- If > 50% of the monthly error budget is consumed within the first 15 days → freeze all non-critical deployments until the next budget period.
- If root cause is not identified within 4 hours of a quality SLO breach → escalate to senior engineer and freeze deployments regardless of investigation status.
- Positive conversation examples (high satisfaction, low turns, clear resolution) are stored as a golden dataset for future evaluation with RAGAS, Phoenix, or DeepEval.
