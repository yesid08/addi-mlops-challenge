# Part 2 — A/B Testing

## Files

| File | Description |
|------|-------------|
| `ab_config.py` | `ABSettings` (Pydantic BaseSettings) reads `AB_TREATMENT_TRAFFIC_PCT` and `AB_EXPERIMENT_SALT` from environment; no redeploy needed to change split |
| `ab_router.py` | `assign_variant(user_id)` — deterministic SHA-256 bucketing; `get_graph_for_variant()` — selects compiled graph; `log_assignment()` — structured log per request |
| `agent_versions/version_a.py` | Thin re-export of the control chain and graph from `source/` |
| `agent_versions/version_b.py` | Treatment: Spanish system prompt, `temperature=0.3`, bullet-formatted KB, `handle_general_b` domain function, `workflow_b` graph |
| `source/adapters/chains/llm_factory.py` | Shared chain factory used by both versions — builds `(prompt \| OpenAI).with_fallbacks([(prompt \| Gemini)])` so both variants are resilient to OpenAI outages |
| `measurement_plan.md` | Experiment hypothesis, metrics, sample-size analysis, guardrails |
| `tests/test_ab_router.py` | Determinism, distribution, boundary, salt-isolation tests |
| `tests/test_version_b.py` | Unit tests for `handle_general_b`, `get_treatment_chain`, and the KB formatter |

## How the split works

Every `POST /chat` request:
1. Calls `assign_variant(user_id)` → SHA-256 hash of `"<salt>:<user_id>"` → bucket mod 100 → "A" or "B"
2. Selects `app.state.graph_a` or `app.state.graph_b` (compiled at startup)
3. Logs `ab_variant=A|B user_id=... correlation_id=...`
4. Returns `ab_variant` in the response body

## User feedback (adoption signal)

```
POST /chat/conversations/{conversation_id}/feedback
Body: {"rating": "good" | "bad"}

GET /ab/feedback/summary
→ per-variant good/bad counts, good-rate, live two-proportion z-test
```

## Provider fallback and A/B integrity

Both Version A and Version B use `build_chain_with_fallback` from `source/adapters/chains/llm_factory.py`. Each variant builds its own `prompt | llm.with_structured_output(schema)` chain for both the primary (OpenAI) and the fallback (Gemini), then wires them with LangChain's `RunnableWithFallbacks`.

The fallback preserves the temperature of each variant — Version A's fallback runs at `temperature=0` and Version B's at `temperature=0.3` — so the experiment variable is maintained even when Gemini is serving the request. This means a fallback event does not invalidate A/B measurements.

## Configuration

| Environment variable | Default | Effect |
|---------------------|---------|--------|
| `AB_TREATMENT_TRAFFIC_PCT` | `50` | % of users routed to Version B (0 = kill switch) |
| `AB_EXPERIMENT_SALT` | `emporyum-ab-v1` | Change to reassign all users to new buckets |
| `OPENAI_API_KEY` | — | Required — primary LLM provider |
| `GOOGLE_API_KEY` | — | Required — Gemini 2.0 Flash fallback provider |

## Running tests

Both `OPENAI_API_KEY` and `GOOGLE_API_KEY` are set to fake values automatically by `conftest.py` — no real credentials needed.

```bash
# Part 2 unit tests only
OPENAI_API_KEY=sk-fake poetry run pytest deliverables/part2_ab_testing/tests/ -v

# All tests including Part 1 (feedback endpoints)
OPENAI_API_KEY=sk-fake poetry run pytest deliverables/ -v
```
