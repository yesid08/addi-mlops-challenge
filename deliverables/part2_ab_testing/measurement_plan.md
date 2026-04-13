# A/B Testing — Measurement Plan

---

## 1. Experiment Design

**Version A — control**

The current `handle_general` implementation:
- Model: `gpt-4o-mini`, `temperature=0`
- System prompt written in English
- Knowledge Base passed as a raw Python dict repr (`str(SCENARIO_KNOWLEDGE_BASE)`)

**Version B — treatment**

A modified `handle_general_b` with three coordinated changes:
- Model: `gpt-4o-mini`, `temperature=0.3`
- System prompt written entirely in Colombian Spanish
- Knowledge Base formatted as concise per-topic bullet points (lower token noise)

**Hypothesis**

Aligning the instruction language with the output language (Spanish → Spanish) eliminates
the model's need to code-switch between English rules and Spanish responses.  Combined with
a slightly warmer temperature (0.3), we expect Version B to produce more natural-sounding
conversational replies, measurable as higher user adoption (good-rate) and lower token usage.

**Traffic split**

50 % A / 50 % B by default (`AB_TREATMENT_TRAFFIC_PCT=50`).
Assignment is deterministic per `user_id` (SHA-256 hash bucketing) so a user always receives
the same version throughout the experiment.  Changing `AB_TREATMENT_TRAFFIC_PCT` or
`AB_EXPERIMENT_SALT` requires only an environment-variable update — no code redeploy.

---

## 2. Metrics

| Metric | Type | How Measured | Why It Matters |
|--------|------|-------------|----------------|
| **User adoption (good-rate)** | Primary | `POST /chat/conversations/{id}/feedback` → `GET /ab/feedback/summary` | Direct satisfaction signal; two-proportion z-test available live |
| Response latency p50 / p90 / p99 | Primary | `time.monotonic()` delta in chat router, logged per request | Core UX; higher latency degrades experience |
| LLM token count (prompt + completion) | Primary | OpenAI `usage` field logged per request | Direct cost proxy; hypothesis: B uses fewer tokens due to cleaner prompt |
| Error rate (non-200 responses) | Guardrail | Count of 5xx responses per variant | B must not degrade reliability |
| Timeout rate (HTTP 504) | Guardrail | Count of 504 responses per variant | Hard ceiling — any increase is unacceptable |
| Response character count | Proxy | `len(generation)` logged per request | Shorter, focused replies are a proxy for Version B's brevity rule |
| User retry rate | Proxy | Same `conversation_id` follow-up within 60 s with a similar question | Implicit dissatisfaction signal |

---

## 3. Statistical Methodology

### Primary metric: user adoption (good-rate)

**Test**: two-proportion z-test on `p_A = good_A / total_A` vs `p_B = good_B / total_B`.

Results are available live at `GET /ab/feedback/summary` — the response includes
`statistical_test.significant: true` when p < 0.05.

**Power analysis** (adoption metric):
- Baseline good-rate assumption: 70 % (p_A = 0.70)
- Minimum Detectable Effect: +5 pp (p_B = 0.75 would be meaningful in production)
- α = 0.05 (two-tailed), power = 0.80
- Required n ≈ **620 feedback entries per variant**

**Secondary metrics** (latency, token count):
- Test: two-sample Welch's t-test
- MDE: 200 ms (≈ 10 % of expected 2 000 ms baseline), σ ≈ 600 ms
- Required n ≈ 350 conversations per variant

The **binding sample size** is 620 (adoption), because it is the larger requirement.

**Multiple comparisons**

Four primary metrics are evaluated. Bonferroni correction: α / 4 = **0.0125 per metric**.

**Experiment duration**

- Minimum: **2 weeks** regardless of sample-size attainment (to capture day-of-week effects).
- At 100 daily conversations with a 50/50 split and ≈ 30 % feedback rate:
  - Conversations per variant per day: 50
  - Feedback entries per variant per day: ≈ 15
  - Days to reach 620 feedback entries: ≈ 41 days (≈ 6 weeks)
- In production with higher traffic, revisit daily and stop early only when both the
  sample-size floor and the 2-week minimum are met.

---

## 4. Guardrails

Guardrails are checked daily (or after every 500 requests, whichever comes first).
The stop action is always an environment-variable change — no code redeploy required.

| # | Condition | Threshold | Action |
|---|-----------|-----------|--------|
| 1 | **Adoption collapse** | B good-rate drops > 10 pp below A, p < 0.01 (`GET /ab/feedback/summary`) | Set `AB_TREATMENT_TRAFFIC_PCT=0` immediately |
| 2 | **Error rate spike** | B error rate exceeds A by > 2 pp with p < 0.01 | Set `AB_TREATMENT_TRAFFIC_PCT=0` immediately |
| 3 | **Latency degradation** | B p99 latency > A p99 latency by > 30 % for 3 consecutive daily check windows | Set `AB_TREATMENT_TRAFFIC_PCT=0` |
| 4 | **Timeout ceiling** | B produces > 1 % HTTP 504 over any 24 h window | Set `AB_TREATMENT_TRAFFIC_PCT=0` immediately |

Guardrails are intentionally one-sided (they only stop the experiment if B is **worse**).
If B is significantly **better** on a primary metric before the planned end date, the
experiment may be stopped early and B promoted — but only after the 2-week minimum
and with sign-off from the product team.

---
