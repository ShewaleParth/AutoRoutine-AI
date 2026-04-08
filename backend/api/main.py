from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from agents.orchestrator import OrchestratorAgent
from api.routes import chat, tasks, calendar, notes, insights, workflows, auth_google
import structlog
import os

log = structlog.get_logger()
orchestrator: OrchestratorAgent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    log.info('startup.agents.initialising')
    orchestrator = OrchestratorAgent()
    app.state.orchestrator = orchestrator
    log.info('startup.agents.ready', count=orchestrator.agent_count())
    yield
    log.info('shutdown')

app = FastAPI(
    title='AutoRoutine AI',
    description='Intelligent Life OS — Multi-Agent Task & Schedule Manager',
    version='1.0.0',
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=[
        'http://localhost:3000',
        'http://localhost:5173',
        'https://autoroutine-frontend-627691634680.us-central1.run.app'
    ],
    allow_credentials=True,
    allow_methods=['*'], 
    allow_headers=['*']
)

app.include_router(chat.router, prefix='/api')
app.include_router(tasks.router, prefix='/api')
app.include_router(calendar.router, prefix='/api')
app.include_router(notes.router, prefix='/api')
app.include_router(insights.router, prefix='/api')
app.include_router(workflows.router, prefix='/api')
app.include_router(auth_google.router, prefix='/api')

@app.get('/health')
async def health():
    return {
        'status': 'ok', 
        'agents': app.state.orchestrator.agent_count(),
        'version': '1.0.0'
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
