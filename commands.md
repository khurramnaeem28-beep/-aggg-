# FastAPI Commands — Step by Step

Run these in order from a PowerShell terminal in VS Code. Every `cd` uses a full path, so it doesn't matter where your terminal starts.

---

## 1. Check Python is available

```powershell
python --version
```

---

## 2. Run "hello world"

```powershell
cd "e:\ai agents\okay agent\hello-fastapi"
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\uvicorn app:app --reload
```

Open http://127.0.0.1:8000/docs in a browser — that's FastAPI's auto-generated interactive docs, built entirely from your route signatures and Pydantic models.

Try it from another terminal:

```powershell
curl http://127.0.0.1:8000/
curl "http://127.0.0.1:8000/greet/Soman?loud=true"
curl -X POST http://127.0.0.1:8000/items -H "Content-Type: application/json" -d "{\"title\": \"write docs\"}"
```

`--reload` restarts the server automatically whenever you edit `app.py` — leave it running and edit a route to see it pick up the change.

Stop the server with `Ctrl+C`.

---

## 3. Set up the agent API

```powershell
cd "e:\ai agents\okay agent\agent-api"
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and replace the placeholder with your real OpenAI key.

---

## 4. Run the agent API

```powershell
.venv\Scripts\uvicorn main:app --reload
```

Open http://127.0.0.1:8000/ for the chat UI, or http://127.0.0.1:8000/docs to try `/chat` directly from Swagger.

---

## 5. Call it from the terminal

Health check:

```powershell
curl http://127.0.0.1:8000/health
```

Non-streaming chat:

```powershell
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"What is FastAPI, in one sentence?\"}"
```

Streaming chat (tokens print as they arrive):

```powershell
curl -N -X POST http://127.0.0.1:8000/chat/stream -H "Content-Type: application/json" -d "{\"message\": \"Count to 5 slowly.\"}"
```

---

## 6. Trigger validation errors on purpose

```powershell
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{}"
```

FastAPI rejects this with a 422 before `chat()` ever runs, because `message` is required in `ChatRequest`. Check the response body — it tells you exactly which field failed and why.

---

## 7. Stop and clean up

`Ctrl+C` stops `uvicorn`. To remove a virtual environment:

```powershell
Remove-Item -Recurse -Force .venv
```
