from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class CreateNoteReq(BaseModel):
    user_id: str
    content: str
    auto_extract: bool = True

@router.post('/notes')
async def create_note_endpoint(req: CreateNoteReq, request: Request):
    notes_agent = request.app.state.orchestrator.notes_agent
    return await notes_agent.create_note(
        user_id=req.user_id, content=req.content, auto_extract=req.auto_extract
    )

@router.get('/notes/search')
async def search_notes_endpoint(request: Request, user_id: str, query: str):
    notes_agent = request.app.state.orchestrator.notes_agent
    return await notes_agent.search_notes(user_id=user_id, query=query)
