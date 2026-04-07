from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class CreateEventReq(BaseModel):
    user_id: str
    title: str
    start: str
    end: str
    attendees: List[str] = []

@router.post('/calendar/events')
async def create_event_endpoint(req: CreateEventReq, request: Request):
    calendar_agent = request.app.state.orchestrator.calendar_agent
    return await calendar_agent.create_event(
        user_id=req.user_id, title=req.title, 
        start_time=req.start, end_time=req.end, attendees=",".join(req.attendees)
    )

@router.get('/calendar/events')
async def get_events_endpoint(request: Request, user_id: str, days_ahead: int = 7):
    calendar_agent = request.app.state.orchestrator.calendar_agent
    return await calendar_agent.get_upcoming_events(user_id=user_id, days_ahead=days_ahead)

@router.get('/calendar/free-slots')
async def find_free_slots_endpoint(request: Request, user_id: str, duration_mins: int = 60):
    calendar_agent = request.app.state.orchestrator.calendar_agent
    return await calendar_agent.find_free_slots(user_id=user_id, duration_mins=duration_mins)
