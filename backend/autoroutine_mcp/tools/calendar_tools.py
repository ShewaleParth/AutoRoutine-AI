"""
Calendar MCP Tools — create_event, get_upcoming_events, find_free_slots
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp.server.fastmcp import FastMCP
from db.firestore_client import FirestoreClient
from datetime import datetime, timedelta
import structlog

log = structlog.get_logger()
db = FirestoreClient()

mcp = FastMCP("flowmind-calendar-tools")


@mcp.tool()
async def create_event(
    user_id: str,
    title: str,
    start_time: str,
    end_time: str,
    attendees: list = [],
    task_ids: list = [],
    description: str = "",
    location: str = "",
) -> dict:
    """
    Create a calendar event in Firestore.
    start_time / end_time: ISO 8601 strings e.g. '2025-04-10T14:00:00'
    Returns: { event_id, title, start_time }
    """
    data = {
        "user_id": user_id,
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "attendees": attendees,
        "task_ids": task_ids,
        "description": description,
        "location": location,
    }
    event_id = await db.create("events", data)
    log.info("tool.create_event", id=event_id, title=title, user=user_id)
    return {"event_id": event_id, "title": title, "start_time": start_time}


@mcp.tool()
async def get_upcoming_events(user_id: str, days_ahead: int = 7, limit: int = 20) -> list:
    """
    Retrieve upcoming calendar events for the next N days.
    Returns: list of event dicts sorted by start_time
    """
    events = await db.query("events", [("user_id", "==", user_id)], limit=limit)

    now_str = datetime.utcnow().isoformat()
    cutoff = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()

    upcoming = [
        e for e in events
        if e.get("start_time", "") >= now_str and e.get("start_time", "") <= cutoff
    ]
    upcoming.sort(key=lambda e: e.get("start_time", ""))
    log.info("tool.get_upcoming_events", count=len(upcoming), user=user_id)
    return upcoming


@mcp.tool()
async def find_free_slots(
    user_id: str,
    duration_mins: int = 60,
    days_ahead: int = 3,
) -> list:
    """
    Find available time slots for a meeting of given duration.
    Checks existing events and returns free windows within work hours (9 AM - 6 PM).
    Returns: list of { start, end, duration_mins } dicts
    """
    events = await db.query("events", [("user_id", "==", user_id)], limit=50)

    free_slots = []
    work_start_hour = 9
    work_end_hour = 18

    for day_offset in range(days_ahead):
        day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        day += timedelta(days=day_offset + 1)

        busy_times = []
        for e in events:
            st = e.get("start_time", "")
            et = e.get("end_time", "")
            if st and st.startswith(day.strftime("%Y-%m-%d")):
                try:
                    busy_times.append((
                        datetime.fromisoformat(st).hour * 60 + datetime.fromisoformat(st).minute,
                        datetime.fromisoformat(et).hour * 60 + datetime.fromisoformat(et).minute,
                    ))
                except Exception:
                    pass

        busy_times.sort()

        current = work_start_hour * 60
        work_end = work_end_hour * 60

        for busy_start, busy_end in busy_times:
            if current + duration_mins <= busy_start:
                free_slots.append({
                    "start": day.replace(hour=current // 60, minute=current % 60).isoformat(),
                    "end": day.replace(hour=(current + duration_mins) // 60, minute=(current + duration_mins) % 60).isoformat(),
                    "duration_mins": duration_mins,
                })
            current = max(current, busy_end)

        if current + duration_mins <= work_end:
            free_slots.append({
                "start": day.replace(hour=current // 60, minute=current % 60).isoformat(),
                "end": day.replace(hour=(current + duration_mins) // 60, minute=(current + duration_mins) % 60).isoformat(),
                "duration_mins": duration_mins,
            })

    log.info("tool.find_free_slots", slots_found=len(free_slots), user=user_id)
    return free_slots[:5]  # Return top 5 slots


@mcp.tool()
async def get_todays_events(user_id: str) -> list:
    """
    Get all events scheduled for today.
    Returns: list of today's event dicts
    """
    events = await db.query("events", [("user_id", "==", user_id)], limit=50)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    todays = [e for e in events if e.get("start_time", "").startswith(today)]
    todays.sort(key=lambda e: e.get("start_time", ""))
    log.info("tool.get_todays_events", count=len(todays), user=user_id)
    return todays
