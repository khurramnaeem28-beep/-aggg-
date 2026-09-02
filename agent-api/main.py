from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import APIError, AsyncOpenAI, AuthenticationError, RateLimitError

from config import Settings, get_settings
from models import ChatRequest, ChatResponse

SYSTEM_PROMPT = "You are a concise, helpful assistant."


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Built once at startup and reused across requests, instead of
    # creating a new OpenAI client on every call.
    settings = get_settings()
    app.state.client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url="https://groq.com"
    )

    yield


app = FastAPI(title="Agent API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


def build_history(req: ChatRequest) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *[m.model_dump() for m in req.history],
        {"role": "user", "content": req.message},
    ]


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, settings: Settings = Depends(get_settings)):
    client: AsyncOpenAI = app.state.client
    try:
        completion = await client.chat.completions.create(
            model=settings.model,
            messages=build_history(req),
        )
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="OpenAI rejected the API key.")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="Rate limited by OpenAI, try again shortly.")
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {e}")

    return ChatResponse(reply=completion.choices[0].message.content or "")


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, settings: Settings = Depends(get_settings)):
    client: AsyncOpenAI = app.state.client

    async def token_stream():
        try:
            stream = await client.chat.completions.create(
                model=settings.model,
                messages=build_history(req),
                stream=True,
            )
        except (AuthenticationError, RateLimitError, APIError) as e:
            yield f"[error] {e}"
            return

        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta

    return StreamingResponse(token_stream(), media_type="text/plain")


# Mounted last, at the root path, so it only catches requests that don't
# match a route defined above (FastAPI checks explicit routes first).
app.mount("/", StaticFiles(directory="static", html=True), name="static")
