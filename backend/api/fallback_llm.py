"""
Fallback LLM chain with real tool execution.

Chain:  Gemini (ADK)  →  Groq / Llama-3.3-70B  →  OpenAI / GPT-4o-mini

When Gemini is rate-limited, the fallback:
  1. Calls Groq/OpenAI with the same tool schemas the agents expose
  2. If the LLM returns a tool_call, executes it against Firestore directly
  3. Feeds the result back and gets the final natural-language reply

The user gets a real action taken, not just a text suggestion.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
import structlog
import httpx

log = structlog.get_logger()

# ── System prompt ─────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are AutoRoutine AI — an intelligent life-management assistant.
You help users manage tasks, calendar events, notes, and productivity insights.
Be concise, friendly, and action-oriented.
Always use the available tools to perform actions — never just describe what you would do.
For dates/times, use ISO 8601 format. Assume user_id="demo_user" unless told otherwise.
Today's date is {today}."""

# ── Tool schemas (OpenAI function-calling format) ─────────────────────────────
_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task and save it to the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id":  {"type": "string", "description": "The user's ID"},
                    "title":    {"type": "string", "description": "Task title"},
                    "priority": {"type": "integer", "description": "Priority 1-5 (5=highest)", "default": 3},
                    "due_date": {"type": "string", "description": "ISO 8601 due date (optional)"},
                },
                "required": ["user_id", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List tasks for a user, optionally filtered by status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "status":  {"type": "string", "enum": ["pending", "done"], "description": "Filter by status"},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update an existing task status or priority.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id":  {"type": "string", "description": "The ID of the task to update"},
                    "status":   {"type": "string", "enum": ["pending", "done"], "description": "New status for the task"},
                    "priority": {"type": "integer", "description": "New priority 1-5"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": "Create a calendar event.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id":    {"type": "string"},
                    "title":      {"type": "string"},
                    "start_time": {"type": "string", "description": "ISO 8601 start datetime"},
                    "end_time":   {"type": "string", "description": "ISO 8601 end datetime"},
                    "attendees":  {"type": "string", "description": "Comma-separated email list (optional)"},
                },
                "required": ["user_id", "title", "start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_events",
            "description": "Get upcoming calendar events for the next N days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id":    {"type": "string"},
                    "days_ahead": {"type": "integer", "default": 7},
                },
                "required": ["user_id"],
            },
        },
    },
]


# ── DB tool executor ──────────────────────────────────────────────────────────
async def _execute_tool(name: str, args: dict) -> str:
    """Execute a tool call against Firestore and return a JSON string result."""
    try:
        from db.singleton import get_db
        db = get_db()

        if name == "create_task":
            data = {
                "user_id": args["user_id"],
                "title": args["title"],
                "priority": args.get("priority", 3),
                "status": "pending",
            }
            if args.get("due_date"):
                data["due_date"] = args["due_date"]
            task_id = await db.create("tasks", data)
            log.info("fallback.tool.create_task", task_id=task_id, title=args["title"])
            return json.dumps({"task_id": task_id, "status": "created", "title": args["title"]})

        elif name == "list_tasks":
            filters = [("user_id", "==", args["user_id"])]
            if args.get("status"):
                filters.append(("status", "==", args["status"]))
            tasks = await db.query("tasks", filters)
            return json.dumps(tasks)

        elif name == "update_task":
            updates = {}
            if args.get("status"): updates["status"] = args["status"]
            if args.get("priority"): updates["priority"] = args["priority"]
            if updates:
                await db.update("tasks", args["task_id"], updates)
                log.info("fallback.tool.update_task", task_id=args["task_id"], updates=updates)
            return json.dumps({"task_id": args["task_id"], "updated": True, "fields": list(updates.keys())})

        elif name == "create_event":
            data = {
                "user_id": args["user_id"],
                "title": args["title"],
                "start_time": args["start_time"],
                "end_time": args["end_time"],
                "attendees": [a.strip() for a in args.get("attendees", "").split(",") if a.strip()],
                "task_ids": [],
            }
            event_id = await db.create("events", data)
            log.info("fallback.tool.create_event", event_id=event_id, title=args["title"])
            return json.dumps({"event_id": event_id, "status": "created", "title": args["title"]})

        elif name == "get_upcoming_events":
            events = await db.query("events", [("user_id", "==", args["user_id"])])
            now_str = datetime.utcnow().isoformat()
            cutoff = (datetime.utcnow() + timedelta(days=args.get("days_ahead", 7))).isoformat()
            upcoming = [e for e in events if now_str <= e.get("start_time", "") <= cutoff]
            return json.dumps(sorted(upcoming, key=lambda e: e.get("start_time", "")))

        return json.dumps({"error": f"Unknown tool: {name}"})

    except Exception as e:
        log.error("fallback.tool.error", tool=name, error=str(e)[:200])
        return json.dumps({"error": str(e)})


# ── Single provider call (with tool loop) ─────────────────────────────────────
async def _call_provider(provider: dict, user_message: str) -> str | None:
    api_key = os.getenv(provider["env_key"], "").strip()
    if not api_key:
        log.warning("fallback.skip.no_key", provider=provider["name"])
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT.format(today=datetime.utcnow().strftime("%Y-%m-%d"))},
        {"role": "user", "content": user_message},
    ]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # ── Agentic loop: LLM → tool calls → LLM ──────────────────────
            for _ in range(5):   # max 5 rounds
                payload = {
                    "model": provider["model"],
                    "messages": messages,
                    "tools": _TOOLS,
                    "tool_choice": "auto",
                    "max_tokens": 1024,
                    "temperature": 0.3,
                }
                resp = await client.post(provider["url"], headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                choice = data["choices"][0]
                msg = choice["message"]

                # If no tool calls → we have the final reply
                if not msg.get("tool_calls"):
                    text = (msg.get("content") or "").strip()
                    log.info("fallback.success", provider=provider["name"])
                    return text

                # Execute all tool calls in parallel
                messages.append(msg)  # append assistant message with tool_calls
                tool_results = await asyncio.gather(*[
                    _execute_tool(tc["function"]["name"], json.loads(tc["function"]["arguments"]))
                    for tc in msg["tool_calls"]
                ])
                for tc, result in zip(msg["tool_calls"], tool_results):
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })
                # Loop back so LLM can synthesise a reply from tool results

            return "I performed your request. Please refresh to see the latest data."

    except httpx.HTTPStatusError as e:
        log.warning("fallback.http_error", provider=provider["name"],
                    status=e.response.status_code, detail=e.response.text[:200])
    except Exception as e:
        log.warning("fallback.error", provider=provider["name"], error=str(e)[:200])

    return None


# ── Provider config ───────────────────────────────────────────────────────────
_PROVIDERS = [
    {
        "name": "groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
        "env_key": "GROQ_API_KEY",
    },
    {
        "name": "openai",
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
]


# ── Public entrypoint ─────────────────────────────────────────────────────────
async def call_fallback(user_message: str) -> str:
    """
    Try each provider. Returns first successful response,
    or a friendly error if all fail.
    """
    for provider in _PROVIDERS:
        result = await _call_provider(provider, user_message)
        if result:
            return result

    log.error("fallback.all_failed")
    return (
        "⚠️ All AI providers are currently unavailable. "
        "Please wait a moment and try again."
    )
