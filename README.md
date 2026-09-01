# FastAPI Workshop — Building an AI Agent API

This project is a hands-on setup for learning FastAPI. The goal isn't a clever agent — the agent is intentionally simple — the goal is FastAPI: routing, request/response validation, dependency injection, config/secrets handling, streaming, and auto-generated docs.

Two stages, one folder each:

- **`hello-fastapi/`** — the smallest possible API, used to teach the core loop: define routes → run with `uvicorn` → hit them → read the auto-generated docs.
- **`agent-api/`** — a real, working AI agent (calls the OpenAI API) exposed over HTTP, wrapped the way you'd actually ship it: typed request/response models, settings loaded from `.env`, error handling, and a streaming endpoint.

`commands.md` has the exact terminal commands to run, in order.

---

## `hello-fastapi/`

### `app.py`
Three routes, each teaching one FastAPI concept:
- `GET /` — the simplest possible route, returns a JSON dict.
- `GET /greet/{name}` — a **path parameter** (`name`) plus a **query parameter** (`loud`, with a default), both type-validated automatically.
- `POST /items` — a **request body** validated against a Pydantic model (`Item`). Send bad JSON and FastAPI rejects it with a 422 before your code even runs.

Run it and open `/docs` — FastAPI generates an interactive Swagger UI from your route signatures and Pydantic models, with zero extra code.

---

## `agent-api/`

The real agent — same OpenAI-backed logic as before, now behind an HTTP API instead of a CLI.

### `config.py`
A `Settings` class (via `pydantic-settings`) that reads `OPENAI_API_KEY` and `MODEL` from environment variables / a `.env` file. This is FastAPI's version of "secrets injected at runtime, never hardcoded" — `.env` is gitignored, `.env.example` is the safe-to-share template.

### `models.py`
Pydantic models (`ChatRequest`, `ChatResponse`, `Message`) that define the API's request/response shape. FastAPI uses these to validate incoming JSON, serialize outgoing JSON, and generate the OpenAPI schema — one source of truth for all three.

### `main.py`
- **`lifespan`** — an async context manager that builds the `AsyncOpenAI` client once at startup (`app.state.client`) instead of on every request.
- **`Depends(get_settings)`** — dependency injection: FastAPI calls `get_settings()` and hands the result to the route function. `get_settings` is `@lru_cache`d, so settings are parsed from the environment once, not on every request.
- **`GET /health`** — a plain liveness check, useful once this is running behind a load balancer or orchestrator.
- **`POST /chat`** — takes a `ChatRequest`, calls OpenAI, returns a `ChatResponse`. OpenAI errors (`AuthenticationError`, `RateLimitError`, `APIError`) are caught and turned into proper `HTTPException`s with meaningful status codes (401 / 429 / 502) instead of a raw traceback.
- **`POST /chat/stream`** — the same logic, but returns a `StreamingResponse` that yields tokens as OpenAI generates them, so the client sees text arrive incrementally instead of waiting for the full reply.

### `.env.example` / `.gitignore`
`.env.example` holds a placeholder key and is safe to commit. `.env` holds your real key and is gitignored — same secret-handling lesson as before, just via environment variables instead of `docker run --env-file`.

### `static/index.html`
A small chat UI — message bubbles, streaming replies, an online/offline health indicator. It's served by FastAPI itself: `main.py` mounts `StaticFiles(directory="static", html=True)` at `/`, *after* all the API routes are declared, so `/health`, `/chat`, and `/docs` still resolve first and only unmatched paths fall through to the static files. That keeps the frontend same-origin with the API — no CORS setup needed. It calls `/chat/stream` with `fetch`, reads the response body as a stream, and appends each chunk to the message as it arrives.

---

## `commands.md`

Step-by-step terminal commands: create a virtual environment, install dependencies, run each app with `uvicorn`, and exercise the endpoints via `/docs` and `curl`.

---

## The one-sentence version

`hello-fastapi/` teaches *how FastAPI works*; `agent-api/` teaches *how to run something real behind it* — with the validation, config, and error-handling practices that make the difference between a toy and something you'd actually deploy.
