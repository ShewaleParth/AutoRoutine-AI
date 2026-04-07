"""
FlowMind MCP Server — exposes all 11 tools via FastMCP.
Agents connect to this server to call tools.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP
from autoroutine_mcp.tools.task_tools import (
    create_task, list_tasks, update_task, delete_task, prioritize_tasks
)
from autoroutine_mcp.tools.calendar_tools import (
    create_event, get_upcoming_events, find_free_slots, get_todays_events
)
from autoroutine_mcp.tools.notes_tools import (
    create_note, search_notes, extract_entities, get_notes
)
from autoroutine_mcp.tools.insight_tools import (
    build_context_graph, get_insights, get_morning_briefing
)
import structlog

log = structlog.get_logger()

# ── Create the main MCP server ─────────────────────────────────────────────
app = FastMCP(
    "flowmind-mcp",
    instructions=(
        "FlowMind MCP Server — provides tools for task management, "
        "calendar scheduling, note-taking, and AI-powered insights. "
        "You are connected to a live Firestore database."
    ),
)

# ── Register all 13 tools ──────────────────────────────────────────────────
# Task tools (5)
app.add_tool(create_task)
app.add_tool(list_tasks)
app.add_tool(update_task)
app.add_tool(delete_task)
app.add_tool(prioritize_tasks)

# Calendar tools (4)
app.add_tool(create_event)
app.add_tool(get_upcoming_events)
app.add_tool(find_free_slots)
app.add_tool(get_todays_events)

# Notes tools (4)
app.add_tool(create_note)
app.add_tool(search_notes)
app.add_tool(extract_entities)
app.add_tool(get_notes)

# Insight tools (3)  — the unique differentiator
app.add_tool(build_context_graph)
app.add_tool(get_insights)
app.add_tool(get_morning_briefing)

log.info("mcp.server.ready", tool_count=16)


if __name__ == "__main__":
    # Run as stdio MCP server (used by ADK agents)
    app.run(transport="stdio")
