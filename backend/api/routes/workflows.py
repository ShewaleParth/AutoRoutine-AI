from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

class WorkflowReq(BaseModel):
    user_id: str

@router.post('/workflows/{workflow_type}')
async def run_workflow_endpoint(workflow_type: str, req: WorkflowReq, request: Request):
    orchestrator = request.app.state.orchestrator
    result = await orchestrator.run_workflow(user_id=req.user_id, workflow=workflow_type)
    return {"result": result, "workflow": workflow_type}
