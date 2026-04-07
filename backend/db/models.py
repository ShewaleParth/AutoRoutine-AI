from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class Priority(int, Enum):
    LOW = 1
    MEDIUM = 2
    NORMAL = 3
    HIGH = 4
    CRITICAL = 5


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


# ─────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────
class TaskCreate(BaseModel):
    user_id: str
    title: str
    description: str = ""
    priority: Priority = Priority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    due_date: Optional[str] = None          # ISO 8601 string, e.g. "2025-04-10T18:00:00"
    tags: List[str] = []
    dependencies: List[str] = []           # Other task IDs this task depends on


class Task(TaskCreate):
    id: str = ""
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None


# ─────────────────────────────────────────────
# Calendar Event
# ─────────────────────────────────────────────
class CalendarEventCreate(BaseModel):
    user_id: str
    title: str
    start_time: str                         # ISO 8601 string
    end_time: str                           # ISO 8601 string
    attendees: List[str] = []
    task_ids: List[str] = []               # Linked task IDs
    description: str = ""
    location: str = ""


class CalendarEvent(CalendarEventCreate):
    id: str = ""
    created_at: Optional[Any] = None


# ─────────────────────────────────────────────
# Note
# ─────────────────────────────────────────────
class NoteCreate(BaseModel):
    user_id: str
    content: str
    summary: str = ""
    entities: List[dict] = []             # Extracted people, dates, action items
    tags: List[str] = []
    linked_task_ids: List[str] = []


class Note(NoteCreate):
    id: str = ""
    created_at: Optional[Any] = None


# ─────────────────────────────────────────────
# Context Graph Node & Edge (for InsightAgent)
# ─────────────────────────────────────────────
class GraphNode(BaseModel):
    user_id: str
    node_type: str                         # "task" | "event" | "note" | "person" | "deadline"
    source_id: str                         # ID of the original document
    label: str
    attributes: dict = {}


class GraphEdge(BaseModel):
    user_id: str
    from_node_id: str
    to_node_id: str
    relation: str                          # e.g. "blocks", "relates_to", "mentioned_in"


# ─────────────────────────────────────────────
# User Preferences
# ─────────────────────────────────────────────
class UserPrefs(BaseModel):
    timezone: str = "Asia/Kolkata"
    work_hours: dict = {"start": "09:00", "end": "18:00"}
    energy_pattern: str = "morning_peak"  # "morning_peak" | "afternoon_peak"
