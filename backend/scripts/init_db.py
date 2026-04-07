"""
init_db.py — Seeds the Firestore database with demo data.
Run once to populate example tasks, events, notes, and user prefs.

Usage:
    cd backend
    source venv/Scripts/activate  (Windows)
    python scripts/init_db.py
"""

import asyncio
import sys
import os

# Allow imports from backend/ root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from db.firestore_client import FirestoreClient


async def seed():
    db = FirestoreClient()
    USER_ID = "demo_user"

    print("🌱 Seeding Firestore...")

    # ── User Preferences ──────────────────────
    await db.set_doc("user_prefs", USER_ID, {
        "user_id": USER_ID,
        "timezone": "Asia/Kolkata",
        "work_hours": {"start": "09:00", "end": "18:00"},
        "energy_pattern": "morning_peak",
    })
    print("  ✅ user_prefs/demo_user")

    # ── Tasks ─────────────────────────────────
    tasks = [
        {
            "user_id": USER_ID,
            "title": "Review Q2 roadmap",
            "description": "Go through product roadmap and add comments",
            "priority": 4,
            "status": "pending",
            "due_date": "2025-04-08T18:00:00",
            "tags": ["product", "review"],
            "dependencies": [],
        },
        {
            "user_id": USER_ID,
            "title": "Prepare hackathon demo slides",
            "description": "Create the 3-min demo deck for judges",
            "priority": 5,
            "status": "in_progress",
            "due_date": "2025-04-07T10:00:00",
            "tags": ["hackathon", "presentation"],
            "dependencies": [],
        },
        {
            "user_id": USER_ID,
            "title": "Write unit tests for agents",
            "description": "Cover TaskAgent, CalendarAgent with pytest",
            "priority": 3,
            "status": "pending",
            "due_date": "2025-04-09T18:00:00",
            "tags": ["dev", "testing"],
            "dependencies": [],
        },
    ]
    task_ids = []
    for t in tasks:
        tid = await db.create("tasks", t)
        task_ids.append(tid)
        print(f"  ✅ tasks/{tid}  — {t['title']}")

    # ── Calendar Events ────────────────────────
    events = [
        {
            "user_id": USER_ID,
            "title": "Daily Standup",
            "start_time": "2025-04-07T09:00:00",
            "end_time": "2025-04-07T09:15:00",
            "attendees": ["alice@team.com", "bob@team.com"],
            "task_ids": [],
            "description": "Daily sync",
            "location": "Zoom",
        },
        {
            "user_id": USER_ID,
            "title": "Q2 Review Meeting",
            "start_time": "2025-04-07T14:00:00",
            "end_time": "2025-04-07T15:00:00",
            "attendees": ["manager@team.com"],
            "task_ids": [task_ids[0]] if task_ids else [],
            "description": "Review roadmap with manager",
            "location": "Conference Room A",
        },
    ]
    for e in events:
        eid = await db.create("events", e)
        print(f"  ✅ events/{eid}  — {e['title']}")

    # ── Notes ─────────────────────────────────
    notes = [
        {
            "user_id": USER_ID,
            "content": (
                "Meeting with Alice on Monday. "
                "Action items: update roadmap by Thursday, "
                "send summary to team by EOD Friday. "
                "Bob will handle the budget section."
            ),
            "summary": "Monday meeting — roadmap update & team summary due",
            "entities": [
                {"type": "person", "value": "Alice"},
                {"type": "person", "value": "Bob"},
                {"type": "deadline", "value": "Thursday"},
                {"type": "action", "value": "update roadmap"},
                {"type": "action", "value": "send summary"},
            ],
            "tags": ["meeting", "roadmap"],
            "linked_task_ids": [task_ids[0]] if task_ids else [],
        }
    ]
    for n in notes:
        nid = await db.create("notes", n)
        print(f"  ✅ notes/{nid}")

    # ── Context Graph placeholder ──────────────
    await db.set_doc("context_graph", USER_ID, {
        "user_id": USER_ID,
        "nodes": [],
        "edges": [],
        "last_built": None,
    })
    print("  ✅ context_graph/demo_user  (empty, will be built by InsightAgent)")

    print("\n🎉 Database seeded successfully!")
    print(f"   Collections created: tasks, events, notes, user_prefs, context_graph")
    print(f"   Open Firestore console to verify:")
    print(f"   https://console.cloud.google.com/firestore/data")


if __name__ == "__main__":
    asyncio.run(seed())
