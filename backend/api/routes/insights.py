from fastapi import APIRouter, Request

router = APIRouter()

@router.get('/insights')
async def get_insights_endpoint(request: Request, user_id: str):
    insight_agent = request.app.state.orchestrator.insight_agent
    return await insight_agent.get_insights(user_id=user_id)
