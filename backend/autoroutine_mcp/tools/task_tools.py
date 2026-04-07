"""
Task MCP Tools — create_task, list_tasks, update_task
All tools write/read from Firestore via FirestoreClient.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp.server.fastmcp import FastMCP
from db.firestore_client import FirestoreClient
import structlog

log = structlog.get_logger()
db = FirestoreClient()

mcp = FastMCP("flowmind-task-tools")


@mcp.tool()
async def create_task(
    user_id: str,
    title: str,
    description: str = "",
    priority: int = 3,
    due_date: str = None,
    tags: list = [],
) -> dict:
    """
    Create a new task and store it in Firestore.
    priority: 1=Low, 2=Medium, 3=Normal, 4=High, 5=Critical
    due_date: ISO 8601 string e.g. '2025-04-10T18:00:00'
    Returns: { task_id, title, status }
    """
    data = {
        "user_id": user_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "pending",
        "tags": tags,
        "dependencies": [],
    }
    if due_date:
        data["due_date"] = due_date

    task_id = await db.create("tasks", data)
    log.info("tool.create_task", id=task_id, title=title, user=user_id)
    return {"task_id": task_id, "title": title, "status": "created"}


@mcp.tool()
async def list_tasks(
    user_id: str,
    status: str = None,
    priority_min: int = None,
    limit: int = 20,
) -> list:
    """
    List tasks for a user with optional filters.
    status: 'pending' | 'in_progress' | 'done' | 'blocked'
    priority_min: only return tasks with priority >= this value
    Returns: list of task dicts
    """
    filters = [("user_id", "==", user_id)]
    if status:
        filters.append(("status", "==", status))

    tasks = await db.query("tasks", filters, limit=limit)

    if priority_min:
        tasks = [t for t in tasks if t.get("priority", 0) >= priority_min]

    log.info("tool.list_tasks", count=len(tasks), user=user_id, status=status)
    return tasks


@mcp.tool()
async def update_task(
    task_id: str,
    status: str = None,
    priority: int = None,
    title: str = None,
    description: str = None,
    due_date: str = None,
) -> dict:
    """
    Update one or more fields on an existing task.
    Only pass the fields you want to change.
    Returns: { task_id, updated: True }
    """
    updates = {}
    if status:
        updates["status"] = status
    if priority:
        updates["priority"] = priority
    if title:
        updates["title"] = title
    if description:
        updates["description"] = description
    if due_date:
        updates["due_date"] = due_date

    if updates:
        await db.update("tasks", task_id, updates)
        log.info("tool.update_task", id=task_id, fields=list(updates.keys()))

    return {"task_id": task_id, "updated": True, "fields_changed": list(updates.keys())}


@mcp.tool()
async def delete_task(user_id: str, task_id: str) -> dict:
    """
    Delete a task permanently.
    Returns: { task_id, deleted: True }
    """
    await db.delete("tasks", task_id)
    log.info("tool.delete_task", id=task_id, user=user_id)
    return {"task_id": task_id, "deleted": True}


@mcp.tool()
async def prioritize_tasks(user_id: str) -> list:
    """
    Return all pending tasks sorted by priority descending (Critical first).
    Returns: ordered list of tasks
    """
    tasks = await db.query("tasks", [("user_id", "==", user_id), ("status", "==", "pending")])
    sorted_tasks = sorted(tasks, key=lambda t: t.get("priority", 0), reverse=True)
    log.info("tool.prioritize_tasks", count=len(sorted_tasks), user=user_id)
    return sorted_tasks
