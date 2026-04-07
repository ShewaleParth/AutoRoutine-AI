"""
Notes MCP Tools — create_note, search_notes, extract_entities
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp.server.fastmcp import FastMCP
from db.firestore_client import FirestoreClient
import re
import structlog

log = structlog.get_logger()
db = FirestoreClient()

mcp = FastMCP("flowmind-notes-tools")


def _extract_entities_from_text(text: str) -> list:
    """
    Simple rule-based entity extraction.
    Finds people (capitalized names), dates, and action verbs.
    In production, this would use Gemini's NLP capabilities.
    """
    entities = []

    # Action items — sentences starting with verbs
    action_patterns = [
        r'\b(review|update|send|prepare|write|create|schedule|call|meet|finish|complete|fix|check|follow up)\b[^.!?]*',
    ]
    for pattern in action_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            entities.append({"type": "action", "value": m.strip()[:100]})

    # Dates — common date patterns
    date_patterns = [
        r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
        r'\b(today|tomorrow|next week|this week|EOD|end of day)\b',
        r'\b\d{1,2}(st|nd|rd|th)?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',
        r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\b',
    ]
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            val = m if isinstance(m, str) else ' '.join(m)
            if val.strip():
                entities.append({"type": "deadline", "value": val.strip()})

    # People — capitalized words that follow "with", "from", "by", "cc", "@"
    people_patterns = [
        r'\b(?:with|from|by|cc|@)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
        r'\b([A-Z][a-z]+)\s+will\b',
        r'\b([A-Z][a-z]+)\s+should\b',
    ]
    for pattern in people_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            entities.append({"type": "person", "value": m.strip()})

    # Deduplicate
    seen = set()
    unique = []
    for e in entities:
        key = f"{e['type']}:{e['value'].lower()}"
        if key not in seen:
            seen.add(key)
            unique.append(e)

    return unique[:20]  # Cap at 20 entities


@mcp.tool()
async def create_note(
    user_id: str,
    content: str,
    tags: list = [],
    auto_extract: bool = True,
    linked_task_ids: list = [],
) -> dict:
    """
    Save a note to Firestore with optional automatic entity extraction.
    auto_extract: if True, automatically finds people, dates, and action items.
    Returns: { note_id, entities_found }
    """
    entities = []
    if auto_extract and content:
        entities = _extract_entities_from_text(content)

    # Generate a simple summary (first 150 chars)
    summary = content[:150].strip()
    if len(content) > 150:
        summary += "..."

    data = {
        "user_id": user_id,
        "content": content,
        "summary": summary,
        "entities": entities,
        "tags": tags,
        "linked_task_ids": linked_task_ids,
    }
    note_id = await db.create("notes", data)
    log.info("tool.create_note", id=note_id, entities=len(entities), user=user_id)
    return {
        "note_id": note_id,
        "summary": summary,
        "entities_found": len(entities),
        "entities": entities,
    }


@mcp.tool()
async def search_notes(
    user_id: str,
    query: str,
    limit: int = 10,
) -> list:
    """
    Search notes by keyword in content, summary, or tags.
    Returns: list of matching note dicts
    """
    notes = await db.query("notes", [("user_id", "==", user_id)], limit=100)

    query_lower = query.lower()
    results = []
    for note in notes:
        content = note.get("content", "").lower()
        summary = note.get("summary", "").lower()
        tags = [t.lower() for t in note.get("tags", [])]

        if (query_lower in content or
                query_lower in summary or
                any(query_lower in t for t in tags)):
            results.append(note)

    log.info("tool.search_notes", query=query, results=len(results), user=user_id)
    return results[:limit]


@mcp.tool()
async def extract_entities(text: str) -> dict:
    """
    Extract structured entities (people, dates, actions) from any text.
    Useful for processing meeting notes or emails.
    Returns: { people, deadlines, actions, total }
    """
    entities = _extract_entities_from_text(text)

    people    = [e["value"] for e in entities if e["type"] == "person"]
    deadlines = [e["value"] for e in entities if e["type"] == "deadline"]
    actions   = [e["value"] for e in entities if e["type"] == "action"]

    log.info("tool.extract_entities", people=len(people), deadlines=len(deadlines), actions=len(actions))
    return {
        "people": people,
        "deadlines": deadlines,
        "actions": actions,
        "all_entities": entities,
        "total": len(entities),
    }


@mcp.tool()
async def get_notes(user_id: str, limit: int = 20) -> list:
    """
    Get all notes for a user, newest first.
    Returns: list of note dicts
    """
    notes = await db.query("notes", [("user_id", "==", user_id)], limit=limit)
    log.info("tool.get_notes", count=len(notes), user=user_id)
    return notes
