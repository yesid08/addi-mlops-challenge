# Part 1 — API, Containerization & CI/CD

FastAPI REST API wrapping the Emporyum Tech LangGraph chatbot.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Send a message, receive a bot response in Colombian Spanish |
| `GET` | `/health` | Health check — graph compilation status and API key presence |
| `GET` | `/chat/conversations/{id}/history` | Retrieve stored message history for a conversation |
| `DELETE` | `/chat/conversations/{id}/history` | Reset conversation history |

Interactive docs available at `http://localhost:8000/docs` once the server is running.

## Design Decisions

- **Server-side conversation history**: The server maintains message history per `conversation_id` in memory. Callers only send the latest message — no need to re-send the full history each turn. History resets on process restart (production should use Redis or a database).
- **Correlation IDs**: `user_id` and `conversation_id` are business identifiers. `correlation_id` is an infrastructure identifier — it is scoped to a single HTTP request, not a conversation. One conversation produces many correlation IDs (one per turn). It is used to link every log line (FastAPI → LangGraph → OpenAI) for a single request across all systems. Pass `X-Correlation-ID` in the request to propagate your own trace ID from an upstream gateway; one is generated automatically if absent.
- **Timeouts**: LLM calls are wrapped with `asyncio.wait_for` (default 30s). Returns `504` on timeout.
- **Validation**: `user_id` is validated against the known set (`user_001`–`user_008`) before any LLM call.

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/)
- `OPENAI_API_KEY` in `.env` at the project root

## Running Locally

The `app/` package uses bare imports (`from app.config import ...`), so uvicorn must be launched from the `part1_api_and_containerization/` directory. `PYTHONPATH` is set to the project root so that `source/` (the LangGraph core) remains importable.

```bash
# From the project root — install dependencies
poetry install

# Copy and populate environment variables (only needed once)
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...

# Start the dev server (auto-reloads on file changes)
cd deliverables/part1_api_and_containerization && \
  PYTHONPATH=../.. poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running, interactive API docs are available at `http://localhost:8000/docs`.

```bash
# Health check
curl http://localhost:8000/health

# Send a chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "conversation_id": "my-session-1", "message": "Hola, ¿cuál es el estado de mi pedido?"}'

# Continue the conversation (server keeps history per conversation_id)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "conversation_id": "my-session-1", "message": "¿Y cuándo llega?"}'

# Pass a correlation ID to propagate your own trace from an upstream system
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: my-trace-123" \
  -d '{"user_id": "user_001", "conversation_id": "s1", "message": "Hola"}'
```

### VS Code Debugging

A `launch.json` is included at `.vscode/launch.json`. Select **"Python Debugger: FastAPI"** and press `F5`. It handles the path setup automatically:

- `cwd` is set to `deliverables/part1_api_and_containerization/` so `app.*` imports resolve.
- `PYTHONPATH` is set to the workspace root so `source.*` imports (LangGraph core) also resolve.

No manual `cd` or environment variable export is needed when using the VS Code debugger.

## Running with Docker

```bash
# From the project root — build the image and start the container
docker-compose -f deliverables/part1_api_and_containerization/docker-compose.yml up --build

# OPENAI_API_KEY is read automatically from .env at the project root
# Verify the container is healthy
curl http://localhost:8000/health
```

The multi-stage Dockerfile (`lint` → `production`) runs `ruff` and `mypy` as a build gate before producing the final image. The build will fail if linting or type-checking does not pass.

To build the production image standalone (without docker-compose):

```bash
# From the project root
docker build \
  -f deliverables/part1_api_and_containerization/Dockerfile \
  -t emporyum-api:latest \
  .

docker run --rm -p 8000:8000 --env-file .env emporyum-api:latest
```

## Running Tests

Tests use a mocked LLM — no real OpenAI key needed.

```bash
# From the project root — run the full suite
OPENAI_API_KEY=sk-fake poetry run pytest deliverables/part1_api_and_containerization/tests/ -v

# Run a specific layer
OPENAI_API_KEY=sk-fake poetry run pytest deliverables/part1_api_and_containerization/tests/test_domain.py -v
OPENAI_API_KEY=sk-fake poetry run pytest deliverables/part1_api_and_containerization/tests/test_integration.py -v
OPENAI_API_KEY=sk-fake poetry run pytest deliverables/part1_api_and_containerization/tests/test_concurrent.py -v
```

### Testing strategy

| File | Layer | What it verifies |
|------|-------|-----------------|
| `test_schemas.py` | Unit | Pydantic request/response validation (user_id whitelist, message length, conversation_id format) |
| `test_domain.py` | Unit | `fetch_user_data` node, `handle_general` node (chain mocked), `filter_user_data` util — no LLM, no HTTP |
| `test_integration.py` | Integration | Full compiled LangGraph workflow (`fetch_user_data → handle_general → END`) with chain mocked; verifies node order, state population, and error fallback |
| `test_health.py` | API | `GET /health` schema and status logic |
| `test_chat.py` | API | `POST /chat` happy path, error codes (422/504/502), conversation history endpoints |
| `test_concurrent.py` | Concurrency | `asyncio.gather` fires four simultaneous requests for `user_001`–`user_004`; checks routing correctness, unique correlation IDs, and per-conversation history isolation |

## Request / Response Schema

### `POST /chat`

Request:
```json
{
  "user_id": "user_001",
  "conversation_id": "my-session-1",
  "message": "¿Cuál es el estado de mi pedido?"
}
```

Response:
```json
{
  "conversation_id": "my-session-1",
  "user_id": "user_001",
  "response": "Hola Carlos! Tu pedido ORD-2025-001 fue entregado el 18 de noviembre...",
  "correlation_id": "a1b2c3d4-...",
  "flow": ["fetch_user_data", "handle_general"]
}
```

### Error Responses

| Status | Cause |
|--------|-------|
| `422` | Invalid `user_id`, empty message, or missing required fields |
| `504` | LLM did not respond within 30 seconds |
| `502` | Upstream LLM/OpenAI error |
| `500` | Unexpected internal error |

All error responses include a `correlation_id` for tracing.

## File Structure

```
deliverables/part1_api_and_containerization/
├── app/
│   ├── main.py                  # FastAPI factory + lifespan (graph compile)
│   ├── config.py                # Settings via pydantic-settings
│   ├── schemas.py               # Request/response Pydantic models
│   ├── exception_handlers.py    # 422 + 500 handlers
│   ├── routers/
│   │   ├── chat.py              # POST /chat and conversation history endpoints
│   │   └── health.py            # GET /health
│   ├── middleware/
│   │   ├── correlation.py       # X-Correlation-ID injection
│   │   └── logging.py           # Request logging
│   └── store/
│       └── conversation_history.py  # In-memory history store
├── tests/
│   ├── conftest.py
│   ├── test_schemas.py       # Unit — Pydantic validation
│   ├── test_domain.py        # Unit — domain nodes + data_filter
│   ├── test_integration.py   # Integration — full compiled graph
│   ├── test_health.py        # API — /health endpoint
│   ├── test_chat.py          # API — /chat + history endpoints
│   └── test_concurrent.py    # Concurrency — asyncio.gather, 4 users
├── Dockerfile
├── docker-compose.yml
└── README.md
```

CI/CD pipeline is at `.github/workflows/ci.yml` (project root).
