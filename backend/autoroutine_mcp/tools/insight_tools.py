"""
Insight MCP Tools — build_context_graph, get_insights
The Context Graph is FlowMind's unique differentiator.
It connects tasks, events, notes, people, and deadlines into a knowledge graph
that the InsightAgent reasons over to surface proactive recommendations.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp.server.fastmcp import FastMCP
from db.firestore_client import FirestoreClient
from datetime import datetime, timedelta
import structlog

log = structlog.get_logger()
db = FirestoreClient()

mcp = FastMCP("flowmind-insight-tools")


@mcp.tool()
async def build_context_graph(user_id: str) -> dict:
    """
    Build the Context Graph by connecting tasks, events, and notes.
    Detects relationships like:
      - task blocks event (task due after event starts)
      - note mentions task (entity match)
      - shared people across events and notes
    Stores result in Firestore context_graph collection.
    Returns: { nodes, edges, insights_count }
    """
    # Fetch all data in parallel
    import asyncio
    tasks, events, notes = await asyncio.gather(
        db.query("tasks",  [("user_id", "==", user_id)], limit=100),
        db.query("events", [("user_id", "==", user_id)], limit=100),
        db.query("notes",  [("user_id", "==", user_id)], limit=100),
    )

    nodes = []
    edges = []

    # Create nodes for each entity
    for t in tasks:
        nodes.append({
            "id": f"task_{t['id']}",
            "type": "task",
            "label": t.get("title", ""),
            "priority": t.get("priority", 3),
            "status": t.get("status", "pending"),
            "due_date": t.get("due_date", ""),
        })

    for e in events:
        nodes.append({
            "id": f"event_{e['id']}",
            "type": "event",
            "label": e.get("title", ""),
            "start_time": e.get("start_time", ""),
            "attendees": e.get("attendees", []),
        })

    for n in notes:
        nodes.append({
            "id": f"note_{n['id']}",
            "type": "note",
            "label": n.get("summary", "")[:60],
            "entities": n.get("entities", []),
        })

    # Build edges: detect blocking relationships
    # A task "blocks" an event if task is due AFTER the event starts (incomplete)
    for t in tasks:
        if t.get("status") in ("pending", "in_progress") and t.get("due_date"):
            for e in events:
                if e.get("start_time") and t["due_date"] >= e["start_time"]:
                    edges.append({
                        "from": f"task_{t['id']}",
                        "to":   f"event_{e['id']}",
                        "relation": "blocks",
                        "risk": "high" if t.get("priority", 0) >= 4 else "medium",
                    })

    # Link notes to tasks they reference (via linked_task_ids)
    for n in notes:
        for tid in n.get("linked_task_ids", []):
            edges.append({
                "from": f"note_{n['id']}",
                "to":   f"task_{tid}",
                "relation": "references",
            })

    # Link events to their task dependencies
    for e in events:
        for tid in e.get("task_ids", []):
            edges.append({
                "from": f"task_{tid}",
                "to":   f"event_{e['id']}",
                "relation": "required_for",
            })

    graph = {
        "user_id": user_id,
        "nodes": nodes,
        "edges": edges,
        "last_built": datetime.utcnow().isoformat(),
        "stats": {
            "tasks": len(tasks),
            "events": len(events),
            "notes": len(notes),
            "edges": len(edges),
        },
    }

    await db.set_doc("context_graph", user_id, graph)
    log.info("tool.build_context_graph", nodes=len(nodes), edges=len(edges), user=user_id)

    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "blocking_relationships": [e for e in edges if e.get("relation") == "blocks"],
        "built_at": graph["last_built"],
    }


@mcp.tool()
async def get_insights(user_id: str, context_type: str = "all") -> dict:
    """
    Surface proactive AI insights from the Context Graph.
    context_type: 'all' | 'deadlines' | 'conflicts' | 'patterns'

    Returns insights like:
      - Deadline risks (high-priority tasks due soon)
      - Blocking conflicts (task blocks an event)
      - Overdue tasks
      - Suggested focus blocks
    Returns: { insights, actions, risk_level }
    """
    import asyncio
    tasks, events, graph_doc = await asyncio.gather(
        db.query("tasks",  [("user_id", "==", user_id)], limit=100),
        db.query("events", [("user_id", "==", user_id)], limit=100),
        db.get("context_graph", user_id),
    )

    insights = []
    actions  = []
    now      = datetime.utcnow()
    tomorrow = (now + timedelta(days=1)).isoformat()
    next3    = (now + timedelta(days=3)).isoformat()

    # ── Insight 1: Deadline Risks ──────────────
    if context_type in ("all", "deadlines"):
        urgent_tasks = [
            t for t in tasks
            if t.get("status") not in ("done",)
            and t.get("due_date", "9999") <= next3
            and t.get("priority", 0) >= 4
        ]
        for t in urgent_tasks:
            insights.append({
                "type": "deadline_risk",
                "message": f"⚠️ '{t['title']}' is due {t.get('due_date', 'soon')} with priority {t['priority']} — not yet done.",
                "task_id": t["id"],
                "severity": "high",
            })
            actions.append(f"Raise priority or reschedule: {t['title']}")

    # ── Insight 2: Blocking Conflicts ──────────
    if context_type in ("all", "conflicts") and graph_doc:
        blocking_edges = [
            e for e in graph_doc.get("edges", [])
            if e.get("relation") == "blocks"
        ]
        if blocking_edges:
            insights.append({
                "type": "blocking_conflict",
                "message": f"🔴 {len(blocking_edges)} task(s) are blocking upcoming meetings.",
                "conflicts": blocking_edges[:3],
                "severity": "high",
            })
            actions.append("Fast-track blocking tasks or reschedule affected meetings")

    # ── Insight 3: Overdue Tasks ───────────────
    overdue = [
        t for t in tasks
        if t.get("status") not in ("done",)
        and t.get("due_date", "9999") < now.isoformat()
    ]
    if overdue:
        insights.append({
            "type": "overdue",
            "message": f"🔴 {len(overdue)} task(s) are overdue and still pending.",
            "tasks": [{"id": t["id"], "title": t["title"]} for t in overdue[:5]],
            "severity": "critical",
        })
        actions.append(f"Address {len(overdue)} overdue tasks immediately")

    # ── Insight 4: Today's Focus ───────────────
    today_str  = now.strftime("%Y-%m-%d")
    today_events = [e for e in events if e.get("start_time", "").startswith(today_str)]
    today_tasks  = [t for t in tasks if t.get("due_date", "").startswith(today_str) and t.get("status") != "done"]

    if today_events or today_tasks:
        insights.append({
            "type": "daily_focus",
            "message": f"📅 Today: {len(today_events)} meetings, {len(today_tasks)} tasks due.",
            "events": [e.get("title") for e in today_events],
            "tasks":  [t.get("title") for t in today_tasks],
            "severity": "info",
        })

    risk_level = "critical" if overdue else ("high" if any(i["severity"] == "high" for i in insights) else "normal")

    log.info("tool.get_insights", count=len(insights), risk=risk_level, user=user_id)
    return {
        "insights": insights,
        "actions": actions,
        "risk_level": risk_level,
        "summary": f"{len(insights)} insight(s) found. Risk: {risk_level}.",
    }


@mcp.tool()
async def get_morning_briefing(user_id: str) -> dict:
    """
    Generate a complete morning briefing combining tasks, events, and insights.
    This is the 'Morning Briefing' workflow entry point.
    Returns: { greeting, events_today, tasks_today, insights, suggested_focus }
    """
    import asyncio
    now = datetime.utcnow()
    today_str = now.strftime("%Y-%m-%d")

    tasks, events = await asyncio.gather(
        db.query("tasks",  [("user_id", "==", user_id)], limit=50),
        db.query("events", [("user_id", "==", user_id)], limit=50),
    )

    today_events = sorted(
        [e for e in events if e.get("start_time", "").startswith(today_str)],
        key=lambda e: e.get("start_time", "")
    )
    today_tasks = sorted(
        [t for t in tasks if t.get("status") != "done" and (
            t.get("due_date", "").startswith(today_str) or t.get("priority", 0) >= 4
        )],
        key=lambda t: -t.get("priority", 0)
    )

    hour = now.hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")

    log.info("tool.get_morning_briefing", events=len(today_events), tasks=len(today_tasks), user=user_id)
    return {
        "greeting": f"{greeting}! Here's your FlowMind briefing.",
        "date": today_str,
        "events_today": today_events[:5],
        "tasks_priority": today_tasks[:5],
        "meeting_count": len(today_events),
        "task_count": len(today_tasks),
        "suggested_focus": today_tasks[0].get("title") if today_tasks else "No high-priority tasks today — great!",
    }
