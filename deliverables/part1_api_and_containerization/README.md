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
- **Correlation IDs**: Each request receives a `X-Correlation-ID` response header. Pass your own in the request to propagate distributed traces.
- **Timeouts**: LLM calls are wrapped with `asyncio.wait_for` (default 30s). Returns `504` on timeout.
- **Validation**: `user_id` is validated against the known set (`user_001`–`user_008`) before any LLM call.

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/)
- `OPENAI_API_KEY` in `.env` at the project root

## Running Locally

```bash
# From the project root — install dependencies
poetry install

# Start the dev server (auto-reloads on file changes)
poetry run uvicorn deliverables.part1_api_and_containerization.app.main:app --reload

# Health check
curl http://localhost:8000/health

# Send a chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "conversation_id": "my-session-1", "message": "Hola, ¿cuál es el estado de mi pedido?"}'

# Continue the conversation (server remembers context)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "conversation_id": "my-session-1", "message": "¿Y cuándo llega?"}'

# Pass a correlation ID for distributed tracing
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: my-trace-123" \
  -d '{"user_id": "user_001", "conversation_id": "s1", "message": "Hola"}'
```

## Running with Docker

```bash
# From the project root — build and start
docker-compose -f deliverables/part1_api_and_containerization/docker-compose.yml up --build

# The service reads OPENAI_API_KEY from the .env file at the project root
curl http://localhost:8000/health
```

## Running Tests

Tests use a mocked graph — no real OpenAI key needed.

```bash
# From the project root
OPENAI_API_KEY=sk-fake poetry run pytest deliverables/part1_api_and_containerization/tests/ -v
```

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
│   ├── test_schemas.py
│   ├── test_health.py
│   └── test_chat.py
├── Dockerfile
├── docker-compose.yml
└── README.md
```

CI/CD pipeline is at `.github/workflows/ci.yml` (project root).
