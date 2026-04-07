from fastapi import APIRouter, Request
from pydantic import BaseModel
import structlog
import asyncio
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from api.fallback_llm import call_fallback

log = structlog.get_logger()
router = APIRouter()

# ── Singletons ────────────────────────────────────────────────────────────────
# ADK detects the app name from the agent module path ("agents/").
APP_NAME = "agents"

# One shared session service for the lifetime of the process
session_service = InMemorySessionService()

# Runner is created lazily on first request and then reused.
_runner: Runner | None = None


def _get_runner(orchestrator) -> Runner:
    global _runner
    if _runner is None:
        _runner = Runner(
            app_name=APP_NAME,
            agent=orchestrator,
            session_service=session_service,
        )
        log.info("chat.runner.created", app_name=APP_NAME)
    return _runner


# ── Models ────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    user_id: str = "demo_user"
    session_id: str = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    actions_taken: list = []
    provider: str = "gemini"   # tells the frontend which model answered


# ── Route ─────────────────────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    orchestrator = request.app.state.orchestrator
    session_id = req.session_id or "default_session"

    log.info("api.chat", user=req.user_id, session=session_id, message=req.message[:50])

    runner = _get_runner(orchestrator)

    # Ensure the session exists before running
    existing = await session_service.get_session(
        app_name=APP_NAME,
        user_id=req.user_id,
        session_id=session_id,
    )
    if not existing:
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=req.user_id,
            session_id=session_id,
        )

    content = types.Content(role="user", parts=[types.Part(text=req.message)])

    response_text = ""
    provider = "gemini"
    max_retries = 3

    # ── Try Gemini (primary) ──────────────────────────────────────────────────
    for attempt in range(max_retries):
        try:
            async for event in runner.run_async(
                user_id=req.user_id,
                session_id=session_id,
                new_message=content,
            ):
                if event.content:
                    text = "".join(
                        [p.text for p in event.content.parts if hasattr(p, "text") and p.text]
                    )
                    if text:
                        response_text += text
            break  # success

        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str

            if is_rate_limit:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)   # 2s, 4s
                    log.warning(
                        "api.chat.gemini_rate_limit",
                        attempt=attempt + 1,
                        wait=wait,
                    )
                    await asyncio.sleep(wait)
                    continue
                else:
                    # Gemini exhausted — hand off to fallback chain
                    log.warning(
                        "api.chat.gemini_exhausted",
                        msg="Switching to fallback LLM chain (Groq → OpenAI)",
                    )
                    response_text = await call_fallback(req.message)
                    provider = "fallback"
            else:
                log.error("api.chat.error", error=err_str[:200])
                response_text = "I encountered an issue processing your request. Please try again."
            break

    return ChatResponse(
        response=response_text or "Done.",
        session_id=session_id,
        provider=provider,
    )
