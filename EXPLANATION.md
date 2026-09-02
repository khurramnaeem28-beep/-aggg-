

- **`hello-fastapi/`** — one file, no external API calls, nothing that can fail for reasons unrelated to FastAPI itself. Just routes.
- **`agent-api/`** — the real thing: config, validation, error handling, streaming, all wrapped around an actual OpenAI call.

If you only have time for one, read `hello-fastapi/` first — everything in `agent-api/` builds on it.

---

## 3. `hello-fastapi/app.py` — the core loop

Three routes, each isolating one idea:

| Route | Concept | Why it matters |
|---|---|---|
| `GET /` | The minimum viable route | A function, a decorator, a dict — FastAPI turns the dict into JSON automatically. |
| `GET /greet/{name}` | Path params + query params | `{name}` in the URL becomes a function argument. `loud: bool = False` is a query param (`?loud=true`) with a default — FastAPI parses and type-checks it before your code runs. |
| `POST /items` | Request body validation via Pydantic | `Item` is a Pydantic model. Send it valid JSON, it becomes a typed Python object. Send it garbage, FastAPI returns a 422 with a field-level error — your function body never executes. |

The point of this file is: **FastAPI's job is turning HTTP into typed Python function calls, and back into HTTP.** You almost never parse a request body or query string by hand.

Run it and open `/docs` — that page isn't hand-written. FastAPI reads your function signatures and Pydantic models and generates a full interactive API explorer from them. That's the payoff for typing everything.

---

## 4. `agent-api/` — the same idea, for real

### `config.py` — secrets, the FastAPI way

The Docker version's lesson was "secrets are injected at runtime, never baked into the image" (`docker run --env-file`). The FastAPI equivalent is `pydantic-settings`: a `Settings` class declares what environment variables it needs (`OPENAI_API_KEY`, `MODEL`), and reads them from `.env` at startup. Same principle, different mechanism — the secret lives outside the code, `.env` is gitignored, `.env.example` is the safe placeholder.

`@lru_cache` on `get_settings()` means the `.env` file is parsed once, not on every request — a small but real performance detail.

### `models.py` — one schema, three jobs

`ChatRequest` and `ChatResponse` aren't just type hints — FastAPI uses the same class to:
1. **Validate** incoming JSON (reject malformed requests automatically),
2. **Serialize** the outgoing response,
3. **Document** the API in `/docs` (the schema shown there is generated from these classes).

That's why there's no manual `if "message" not in body` check anywhere — the model *is* the check.

### `main.py` — the parts that only show up in a "real" app

- **`lifespan`** — an async function that runs once at startup (before `yield`) and once at shutdown (after). I used it to create the `AsyncOpenAI` client a single time and stash it on `app.state`, instead of creating a new HTTP client on every incoming request, which would be wasteful and slow.
- **`Depends(get_settings)`** — FastAPI's dependency injection. Instead of calling `get_settings()` inside the route, the route *declares* that it needs a `Settings` object, and FastAPI supplies it. This looks like overkill for one dependency, but it's the pattern that scales — swapping in a test config, a database session, or an auth check later means changing the dependency, not every route that uses it.
- **`HTTPException` mapping** — OpenAI can fail in specific ways (bad key, rate limit, generic API error). Each one is caught and turned into a specific HTTP status (401, 429, 502) with a human-readable message, instead of a raw Python traceback leaking out of the API.
- **`StreamingResponse`** — `/chat/stream` doesn't wait for OpenAI's full reply before responding. It returns a response object wrapping an `async generator`, and FastAPI sends each `yield`ed chunk to the client as it arrives. This is the direct equivalent of the old CLI's `stream_reply()` — same idea, now over HTTP instead of `print(..., end="")`.

---

## 5. What I deliberately left out

To keep it "simple but covering FastAPI things" rather than sprawling, I didn't add: authentication, a database, background tasks (`BackgroundTasks`), CORS middleware, or tests. Those are natural next steps once the current pieces make sense, but adding them now would bury the core concepts (routing, validation, DI, streaming) under setup that isn't specific to FastAPI.

---

## 6. Where to actually run this

`commands.md` has the exact PowerShell steps — venv, install, `uvicorn --reload`, then hitting each endpoint via `/docs` or `curl`. Start with `hello-fastapi`, break things on purpose (send bad JSON, hit a route with the wrong method), and read the error FastAPI gives you before moving to `agent-api`.
