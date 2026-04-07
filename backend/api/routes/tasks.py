from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

class CreateTaskReq(BaseModel):
    user_id: str
    title: str
    priority: int = 3
    due_date: Optional[str] = None

class UpdateTaskReq(BaseModel):
    status: Optional[str] = None
    priority: Optional[int] = None

@router.post('/tasks')
async def create_task_endpoint(req: CreateTaskReq, request: Request):
    task_agent = request.app.state.orchestrator.task_agent
    return await task_agent.create_task(
        user_id=req.user_id, title=req.title, 
        priority=req.priority, due_date=req.due_date
    )

@router.get('/tasks')
async def list_tasks_endpoint(request: Request, user_id: str, status: Optional[str] = None):
    task_agent = request.app.state.orchestrator.task_agent
    return await task_agent.list_tasks(user_id=user_id, status=status)

@router.put('/tasks/{task_id}')
async def update_task_endpoint(task_id: str, req: UpdateTaskReq, request: Request):
    task_agent = request.app.state.orchestrator.task_agent
    return await task_agent.update_task(
        task_id=task_id, status=req.status, priority=req.priority
    )
