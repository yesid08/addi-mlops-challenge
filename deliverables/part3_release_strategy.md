# Part 3 — Release Strategy

Answer each section with specific, practical details. Reference the Emporyum Tech bot architecture where relevant.

---

## 3.1 — Canary Release

_Describe step-by-step how you would perform a canary release for a new version of the chatbot API._

**Your answer:**

The canary rollout starts at **5% of traffic** routed to the new version, with the remaining 95% staying on the stable version. Each step advances by 5 percentage points. Before advancing, two conditions must both be satisfied: at least **2 hours** have elapsed since the last change, and at least **200 requests** have been served by the canary — the time gate alone is insufficient at low traffic volumes since you would be making decisions on a statistically insignificant sample.

The following metrics are monitored during each window:

- **Exceptions per conversation turn** — normalised by turn rather than by raw request count, because multi-turn sessions inflate raw numbers without reflecting a real degradation in per-interaction quality.
- **Time to first token (TTFT)** — the most sensitive latency signal for an LLM-backed service. Prompt regressions and upstream throttling surface here before they show up in total response time.
- **Total response time (p50 and p95)** — end-to-end wall-clock time per request.
- **Container-level memory** — measured at the pod/container level via the infrastructure agent (e.g., cAdvisor, CloudWatch Container Insights). RAM is not attributable to individual conversation turns in a reliable way; per-turn attribution requires custom instrumentation that rarely pays for itself.
- **Tokens per turn and estimated cost per turn** — a poorly designed prompt can silently triple OpenAI costs before any latency signal moves. These metrics are mandatory in an LLM context.
- **LLM API error rate** — upstream 5xx responses from OpenAI or Gemini, tracked separately from application exceptions. The Gemini fallback implemented in this service may mask these errors at the application layer, so they must be captured before the fallback logic runs.

Each metric is evaluated independently against a **three-tier alert threshold**:

| Tier | Degradation | Action |
|---|---|---|
| **Light** | 5–10% | Log the event, continue advancing on schedule |
| **Moderate** | 10–20% | Freeze the rollout; do not advance in this cycle; keep monitoring |
| **Strong** | >20% | Immediate rollback to 0% canary traffic |

The rollout is triggered by the strongest alert reached across any metric. Full promotion to 100% is only approved if no moderate or strong alert fires across all cycles.

---

## 3.2 — Rollback Strategy

_How would you implement instant rollback? How do you handle state/data consistency during rollback?_

**Your answer:**

**Traffic control belongs to the load balancer, not the application.**

In the prototype implemented in Part 1, the API exposes a router endpoint that can modify the traffic split at runtime without a restart. This is a useful development and testing tool, but in a production environment the authoritative source of traffic routing is the **load balancer** — whether that is an AWS ALB with weighted target groups, Nginx with upstream weights, or a service mesh like Istio with VirtualService traffic policies. The application-level router should have no role in production traffic decisions; it is too easy for a misconfigured API call to affect routing while the load balancer configuration remains unchanged.

**The monitoring service as a decision engine.**

A dedicated monitoring service runs as its own container, separate from the API containers. Every 2 hours it queries the observability stack for the metrics defined in 3.1, reads the current traffic split from the load balancer API, and issues one of three decisions:

- **Advance**: increment canary traffic by 5% via a load balancer API call.
- **Freeze**: leave the current split unchanged; re-evaluate in the next cycle.
- **Rollback**: set canary traffic to 0% immediately.

This separation means the rollback path does not involve redeploying any container — it is a single load balancer configuration update. If the monitoring service itself crashes, the safe default is to leave traffic frozen at its current split until the service recovers.

**Automated promotion and rollback criteria.**

The monitoring service makes decisions based on explicit, pre-agreed thresholds — not human judgment at decision time. Criteria are evaluated at each cycle boundary (every 2 hours, minimum 200 requests served):

| Decision | Conditions (ALL must be true for promotion; ANY triggers rollback) |
|---|---|
| **Promote** (+5% traffic) | Error rate < 1% over window AND p95 latency ≤ 110% of baseline AND tokens/turn ≤ 120% of baseline AND ≥ 200 requests served AND ≥ 2 h elapsed since last change |
| **Freeze** (hold current split) | Any metric in Light or Moderate degradation tier (5–20% regression) but no Critical breach |
| **Rollback** (0% canary immediately) | Error rate > 20% regression OR p95 latency > 20% regression OR explicit negative feedback rate > 15% OR any LLM API error rate spike > 3× baseline |

Baselines are computed from the last 7 days of stable Version A traffic. The `AB_TREATMENT_TRAFFIC_PCT` environment variable is updated by the monitoring service via the container orchestration API — no redeployment required, consistent with the configurable split design from Part 2. Automated promotion decisions are logged as audit events with the metric snapshot that triggered them, so every traffic change is traceable without manual intervention.

**Version-agnostic state schema.**

With weighted load balancing, a single user's conversation can cross versions between turns — turn 1 is handled by Version A, turn 2 by Version B, depending on which container the load balancer selects. This is not a hypothetical edge case; it will happen in any stateless routing setup.

To make this safe, both versions must share an identical `GraphState` TypedDict: same field names, same types, no fields that exist in one version but not the other. The LangGraph checkpointer serialises and replays state from the checkpoint store; if the schema diverges between versions, a turn processed by the wrong version will either raise a `KeyError` or silently discard state. Treating the state schema as a shared contract — not an internal implementation detail of each version — eliminates this entire class of production error.

During a rollback, in-flight conversations are allowed to complete on their current version before the load balancer change propagates (standard connection draining). No in-progress turn is interrupted mid-execution.

---

## 3.3 — Incident Response

_Scenario: You deploy a new version at 2:00 PM Tuesday. By 2:30 PM, error rate spikes from 0.1% to 15%. Walk us through your response._

**Your answer:**

**0–5 minutes — Contain**

The first and only priority is to stop error propagation. Users must not continue to be affected while an investigation is being prepared. The canary traffic is set to **0% immediately via the load balancer configuration** — not through the application-level router — routing 100% of traffic back to Version A. The engineering team is notified in the incident channel at the same moment as the rollback is executed, not after.

Speed matters here more than diagnosis. A rollback based on incomplete information is always preferable to keeping a degraded version live while waiting for certainty.

**5–60 minutes — Investigate**

The investigation uses the `correlation_id`, `conversation_id`, and `user_id` fields that are captured on every request (implemented in Part 1). These identifiers are the backbone of the analysis — they make it possible to reconstruct exactly which conversations failed, in what order, and with what upstream context.

A Claude Code skill — a defined prompt that walks through a specific sequence of commands — is used to query the log aggregation layer (CloudWatch, Loki, or ELK) for the 2:00–2:30 PM window. The skill produces a structured report for each failed conversation: the main error observed, the most likely proximate cause, and the error group it belongs to. The report is pushed directly to a Confluence page via MCP, eliminating manual copy-paste and ensuring the investigation record is available to the whole team immediately.

This skill is approximately one day of work to define well — the prompt needs to encode exactly which commands to run, what fields to extract, and how to cluster errors — but once built, it can be reused for any future incident in minutes.

Note that this approach requires logs to be collected by a log aggregation service. Container stdout is not queryable in a structured way; the aggregation layer is a prerequisite, not an optional enhancement.

**60 minutes–24 hours — Post-mortem**

The error clusters from the investigation are used to classify the root cause into one of three categories, each with a distinct remediation path:

- **Transient upstream failure** (OpenAI or Gemini crash, network partition): the service itself was not at fault. Remediation is improved retry logic, a circuit breaker pattern, and re-enabling the canary once the upstream recovers.
- **Traffic surge**: request volume doubled or tripled and the canary containers ran out of capacity. Remediation is an autoscaling policy and a load test against the canary before the next rollout cycle.
- **Code or design issue**: a bad prompt, an inefficient graph node, or a memory leak that only manifests under production load. Remediation requires a fix, a staging reproduction of the failure to confirm the fix holds, and then re-running the canary from the beginning.

Before any decision is made to re-enable the canary, the failure must be reproduced in a staging environment. A diagnosis that cannot be reproduced is not a diagnosis.

**Communication**

Three separate communications go to three distinct audiences:

- **End users (immediate)**: the primary channel is a status page (Statuspage.io or equivalent), which is what users actively check during a service disruption. Social media is supplementary — it reaches passive audiences but should not be the first or only channel. The message is factual: a degradation was detected, a fix is in progress, updates will follow.
- **Engineering team (immediate)**: Slack incident channel with the rollback confirmation, initial error rate data, and the link to the investigation report as it is built. The goal is to get the right people working on the right information as fast as possible.
- **Stakeholders and leadership (post-mortem)**: a full written report covering root cause, user impact, timeline, and — critically — the decision on experiment B. The outcome of that decision is one of three: fix and re-run the canary with the corrected version, redesign the experiment if the architecture itself is unsound, or abort experiment B entirely if the root cause reveals a fundamental problem that cannot be addressed incrementally.

The preliminary report is delivered within **24 hours**; the full blameless post-mortem within **72 hours**.

---
