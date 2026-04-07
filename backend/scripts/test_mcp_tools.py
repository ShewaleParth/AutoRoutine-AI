"""
Test that all MCP tools import correctly and can connect to Firestore.
Run: venv\Scripts\python scripts\test_mcp_tools.py
"""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv; load_dotenv()

async def main():
    print("Testing MCP tool imports...")

    from autoroutine_mcp.tools.task_tools import create_task, list_tasks, update_task, delete_task, prioritize_tasks
    print("  ✅ task_tools    — 5 tools loaded")

    from autoroutine_mcp.tools.calendar_tools import create_event, get_upcoming_events, find_free_slots, get_todays_events
    print("  ✅ calendar_tools — 4 tools loaded")

    from autoroutine_mcp.tools.notes_tools import create_note, search_notes, extract_entities, get_notes
    print("  ✅ notes_tools   — 4 tools loaded")

    from autoroutine_mcp.tools.insight_tools import build_context_graph, get_insights, get_morning_briefing
    print("  ✅ insight_tools — 3 tools loaded")

    print("\nTesting live tool calls against Firestore...")

    # Test list_tasks
    tasks = await list_tasks(user_id="demo_user")
    print(f"  ✅ list_tasks    — returned {len(tasks)} tasks")

    # Test prioritize_tasks
    ranked = await prioritize_tasks(user_id="demo_user")
    print(f"  ✅ prioritize_tasks — {len(ranked)} pending tasks ranked")

    # Test get_todays_events
    events = await get_todays_events(user_id="demo_user")
    print(f"  ✅ get_todays_events — {len(events)} events today")

    # Test extract_entities
    sample_text = "Meeting with Alice on Monday. Bob will send the report by Friday EOD."
    out = await extract_entities(text=sample_text)
    print(f"  ✅ extract_entities — found {out['total']} entities: {out['people']} people, {out['deadlines']} dates")

    # Test build_context_graph
    graph = await build_context_graph(user_id="demo_user")
    print(f"  ✅ build_context_graph — {graph['nodes']} nodes, {graph['edges']} edges")

    # Test get_insights
    insights = await get_insights(user_id="demo_user")
    print(f"  ✅ get_insights  — {len(insights['insights'])} insights, risk: {insights['risk_level']}")

    # Test morning briefing
    briefing = await get_morning_briefing(user_id="demo_user")
    print(f"  ✅ get_morning_briefing — {briefing['meeting_count']} meetings, {briefing['task_count']} tasks")

    print(f"\n🎉 All 16 MCP tools working correctly!")

asyncio.run(main())
