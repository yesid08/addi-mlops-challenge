# ML Ops Technical Challenge — Emporyum Tech Assistant

## Overview

**Emporyum Tech** is a Colombian e-commerce platform that offers buy-now-pay-later installment plans. The AI & ML Ops team has built a **conversational AI assistant** powered by LangGraph and OpenAI. The assistant is functional — it answers questions using a Knowledge Base, personalizes responses with user data, and handles basic conversation flows.

**Your job is not to improve the bot's AI quality.** Your job is to make this bot **production-ready**: serve it as an API, containerize it, implement observability, design a safe release strategy with A/B testing, and reason about the architecture from an operational perspective.

## Time Estimate

**5 calendar days** from the date you receive this assessment. We expect you to use AI tools (ChatGPT, Claude, Copilot, Cursor, etc.) — AI maturity is part of the evaluation. Include a short note with each deliverable mentioning which tools you used and how.

**Important:** After submission, we will schedule a **technical conversation** where you walk us through your decisions — why you chose a particular approach, what trade-offs you considered, and the reasoning behind your design. You must be able to explain and defend every decision.

## Prerequisites

- Python 3.10 or higher
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management
- [Docker](https://docs.docker.com/get-docker/) installed
- An LLM API key — we will contact you to provide one (or use your own; GPT-4o-mini is sufficient)
- Familiarity with: FastAPI, Docker, CI/CD concepts, monitoring/observability

## Quick Start

Before doing anything else, run the bot locally and verify it works:

```bash
# 1. Install dependencies
poetry install

# 2. Create your .env file and add the LLM API key
cp .env.example .env

# 3. Run the assistant interactively
poetry run python tests/inline.py
```

Try a few conversations — the bot should respond to greetings, order queries, payment questions, etc. **Spend some time understanding the codebase before you start building.** Read `source/application/graph.py` to see the workflow, `source/domain/handle_general.py` to see how the agent works, and `source/adapters/chains/general_chain.py` to see the LLM chain.

> **Having trouble setting up?** Don't hesitate to reach out — we'd rather help you get running so you can focus on the challenge itself.

## Project Structure

```
ml_ops_challenge/
|
|-- README.md                            # <-- YOU ARE HERE
|-- pyproject.toml                       # Project dependencies
|-- .env.example                         # Template for your API key
|
|-- docs/
|   |-- stakeholder_interviews/          # Business context (read for context, not required to modify)
|       |-- team_product.md
|       |-- team_payments.md
|       |-- team_operations.md
|       |-- team_platform.md
|
|-- source/
|   |-- application/
|   |   |-- state.py                     # GraphState TypedDict
|   |   |-- graph.py                     # LangGraph workflow definition
|   |
|   |-- domain/
|   |   |-- fetch_user_data.py           # Fetches user data from mock profiles
|   |   |-- handle_general.py            # Generic agent handler (read this carefully for Part 2)
|   |
|   |-- adapters/
|   |   |-- chains/
|   |   |   |-- general_chain.py         # LLM chain with system prompt (OpenAI)
|   |   |-- utils/
|   |       |-- mock_data.py             # 8 mock user profiles
|   |       |-- data_filter.py           # Utility to filter user data
|   |       |-- knowledge_base.py        # Knowledge Base definitions
|   |
|   |-- examples/                        # LangGraph pattern references
|
|-- tests/
|   |-- inline.py                        # Interactive testing script
|
|-- deliverables/                        # >>> YOUR WORK GOES HERE <<<
    |-- part1_api_and_containerization/  # API, Docker, CI/CD, tests
    |-- part2_ab_testing/               # Agent split, feature toggle, measurement plan
    |-- part3_release_strategy.md       # Canary, rollback, incident response
    |-- part4_observability.md          # Monitoring, alerts, SLOs
    |-- part5_production_readiness.md   # State, security, cost, scaling
    |-- part6_architecture_reasoning.md # Cognitive architecture & latency analysis
```

---

## The Challenge

### Part 1 — API, Containerization & CI/CD (hands-on)

The bot currently runs as a CLI script (`tests/inline.py`). Make it deployable as a service.

**1.1 — REST API**

Build a FastAPI application that exposes the chatbot. At minimum:

- `POST /chat` — Accepts a user message and returns the bot's response. Think about the request/response schema: what fields are needed (user_id, message, conversation_id)? What does a good response look like?
- `GET /health` — Health check endpoint.
- Handle errors gracefully (LLM timeouts, invalid inputs, rate limiting).
- Think about: async handling, request validation, timeouts, structured response format, correlation IDs.

**1.2 — Containerization**

- Write a `Dockerfile` that builds a production-ready image.
- Include a `docker-compose.yml` if you need additional services.
- The container should start the API server and be ready to receive requests.
- Think about: image size, multi-stage builds, security (non-root user), environment variables, `.dockerignore`.

**1.3 — Testing strategy**

Implement and/or document how you would test this service locally:

- Unit tests for individual components (domain functions, chains — consider mocking the LLM).
- Integration tests for the full graph flow.
- API-level tests (endpoint contracts, error responses).
- How would you verify it handles concurrent requests?

**1.4 — CI/CD pipeline**

Design a CI/CD pipeline (GitHub Actions or similar). Provide the YAML configuration. It should cover:

- Linting and static analysis.
- Running your test suite.
- Building and pushing the Docker image.
- Describe (no need to implement) how the pipeline triggers deployment to staging/production.

**Deliverables:** Place all files in `deliverables/part1_api_and_containerization/` with a `README.md` explaining how to run everything.

---

### Part 2 — A/B Testing (hands-on + design)

We want to experiment with different versions of the `handle_general` agent. **Read the code carefully first** — understand what `handle_general` does, what chain it calls, what data it uses, and how it fits into the graph.

**Important:** We are evaluating your **MLOps ability to set up the experiment**, not the AI quality of the variants. The split has to make technical sense (e.g., different prompt strategies, different temperature, different model), but don't spend time fine-tuning the model outputs — that's not what we're testing here.

**2.1 — Create two agent versions**

- **Version A (control):** The current `handle_general` implementation.
- **Version B (treatment):** A modified version. You decide what to change — different system prompt, different temperature, a different model, restructured chain, etc. The change should be meaningful enough that you could realistically expect different behavior, but don't over-invest in tuning the AI quality.

**2.2 — Feature toggle / traffic split**

Build a mechanism that routes each request to Version A or B based on a configurable percentage:

- The split should be **configurable without redeploying** (environment variable, config file, or external service).
- The assignment must be **deterministic per user** — the same `user_id` always gets the same version within an experiment (consistency).
- Log which version was used for each request.

**2.3 — Measurement plan**

Write `deliverables/part2_ab_testing/measurement_plan.md` explaining:

- What metrics would you track to compare the versions? (Latency, error rate, token usage, user satisfaction proxy, etc.)
- How do you determine statistical significance? What sample size?
- How long should the experiment run?
- What guardrails would automatically stop the experiment if Version B is significantly worse?

**Deliverables:** Place all files in `deliverables/part2_ab_testing/`.

---

### Part 3 — Release Strategy (written)

Answer in `deliverables/part3_release_strategy.md`. Be specific — reference the Emporyum Tech bot architecture.

**3.1 — Canary Release**

Describe step-by-step how you would do a canary release for a new chatbot API version:

- What percentage of traffic to start with, and how to ramp up?
- What metrics to monitor during the canary phase?
- Criteria for promoting to full production vs. rolling back?
- How is this different from the A/B testing in Part 2?

**3.2 — Rollback Strategy**

- How would you implement instant rollback?
- What infrastructure components enable fast rollback (containers, load balancers, DNS)?
- How do you handle conversations that started on the new version during rollback?

**3.3 — Incident Response**

Scenario: You deploy a new version at 2:00 PM Tuesday. By 2:30 PM, error rate spikes from 0.1% to 15%. Walk us through:

- Immediate response (first 5 minutes).
- Investigation process (next 30 minutes).
- Communication plan (who, what, when).
- Post-mortem process after resolution.

---

### Part 4 — Observability & Monitoring (hands-on + written)

**4.1 — Structured logging (hands-on)**

Add structured logging to the chatbot. Every request should produce a log entry (JSON format recommended) with at least:

- Timestamp, request_id, user_id, conversation_id
- Selected topic/agent, graph flow path
- Response latency (end-to-end and LLM call time separately)
- Token usage (prompt tokens, completion tokens) if available
- Error details (if any)
- A/B test version used

You can add logging to the existing source code or to your FastAPI wrapper.

**4.2 — Monitoring design (written)**

In `deliverables/part4_observability.md`:

- **Dashboard:** What panels/graphs would you include? Organize by: system health, business metrics, LLM-specific metrics.
- **Alerts:** Define at least 5 alerts with: metric, threshold, severity (warning/critical), action.
- **LLM-specific monitoring:** How would you detect model degradation, cost anomalies, latency issues, prompt injection attempts?

**4.3 — SLOs and SLIs**

- Define at least 3 SLIs you would track.
- Set target SLOs for each (e.g., "99.5% of requests complete in < 5s").
- Describe your error budget policy — what happens when the SLO is breached?

---

### Part 5 — Production Readiness (written)

Answer in `deliverables/part5_production_readiness.md`:

**5.1 — State Management** — The bot uses `MemorySaver` (in-memory). With thousands of concurrent users, what backend would you use? Trade-offs between Redis, PostgreSQL, DynamoDB? Session expiry and cleanup?

**5.2 — Security** — Secrets management, prompt injection prevention, data leakage prevention, PII handling in logs.

**5.3 — Cost Optimization** — LLM cost monitoring, caching strategies, request throttling.

**5.4 — Scaling Architecture** — Describe the target architecture for 10,000 concurrent conversations. Identify bottlenecks. How would you handle LLM API rate limits?

---

### Part 6 — Architecture Reasoning (written + design)

This part evaluates how you think about the **operational implications of AI agent architecture**.

Answer in `deliverables/part6_architecture_reasoning.md`:

**6.1 — Understanding the current architecture**

Look at the bot's current graph: `fetch_user_data → handle_general → END`. This is simple and sequential.

Now imagine the Data Science team improves the bot and introduces a **router** that classifies each question and sends it to a specialized agent (e.g., `handle_payments`, `handle_orders`, `handle_products`, `handle_returns`). The new graph looks like:

```
fetch_user_data → route_question → [specialized_agent] → END
```

From an **MLOps perspective**, what are the implications of this change? Consider: latency (more LLM calls per request), monitoring complexity, failure modes, testing strategy, and deployment.

**6.2 — Latency vs. quality trade-off**

Each LLM call adds ~1-3 seconds of latency. If the architecture grows to include a router + specialized agent + a quality-check step (3 sequential LLM calls), the response time could reach 5-9 seconds.

- How would you approach this problem?
- What architectural patterns could reduce latency without sacrificing the benefits of routing? (Think about: parallelization, caching, model selection, async patterns, streaming.)
- What SLO would you set for response time, and how would you enforce it?

**6.3 — Propose an architecture optimization**

The bot currently processes everything synchronously and sequentially. Propose a concrete change to the architecture (code-level or infrastructure-level) that would improve operational performance. This could be:

- Parallelizing independent graph nodes
- Implementing response streaming
- Adding a caching layer for repeated questions
- Splitting the graph into lightweight and heavyweight paths
- Any other approach you think is valuable

Describe the change, draw the modified graph (text/ASCII/Mermaid is fine), explain the trade-offs, and estimate the expected improvement.

---

## Evaluation Criteria

| Criterion | Weight | What We Look For |
|-----------|--------|-----------------|
| **API, containerization & CI/CD** | 20% | Working API, clean Dockerfile, sensible CI/CD pipeline |
| **A/B testing implementation** | 20% | Deterministic split, configurable without redeploy, clean code |
| **Observability & monitoring** | 15% | Structured logging in code, practical alert design, SLOs |
| **Release strategy & incident response** | 15% | Practical canary/rollback plan, realistic incident walkthrough |
| **Architecture reasoning** | 15% | Shows understanding of latency/quality trade-offs, practical optimization proposal |
| **Production readiness** | 10% | State management, security, scaling — shows real production experience |
| **Code quality & documentation** | 5% | Clean code, clear docs, reproducible setup |

### What differentiates good from great:

- **Good:** Working API + Docker, basic logging, reasonable written answers.
- **Great:** Async FastAPI with error handling, deterministic A/B split, structured JSON logging with correlation IDs, specific SLO numbers with rationale, architecture reasoning that shows real understanding of LLM operational challenges.
- **Outstanding:** All of the above, plus: circuit breakers, health checks with dependency verification, automated canary criteria, LLM-specific drift detection, practical latency optimization with clear trade-off analysis.

## Tips

1. **Run the bot first** — verify it works before wrapping it in anything.
2. **Read the source code** — especially `graph.py`, `handle_general.py`, and `general_chain.py`. Understanding the architecture is critical for Parts 2 and 6.
3. **Start with Part 1** — everything else builds on having a working API.
4. **Working code > perfect documentation.** But good documentation on top of working code is ideal.
5. **Show your thinking.** If you make a trade-off (e.g., chose Redis over DynamoDB), explain why.
6. **Be practical.** We want production-tested approaches, not theoretical designs.
7. **Simple and working is better than complex and broken.**

## Submission

1. Ensure the bot still runs with `poetry run python tests/inline.py`.
2. Ensure your API starts with Docker (`docker-compose up` or equivalent).
3. Verify your test suite passes.
4. Zip the entire `ml_ops_challenge/` folder.
5. Send it back to us.

Good luck!
