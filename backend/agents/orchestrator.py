import asyncio
import structlog
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from agents.task_agent import TaskAgent
from agents.calendar_agent import CalendarAgent
from agents.notes_agent import NotesAgent
from agents.insight_agent import InsightAgent

log = structlog.get_logger()

class OrchestratorAgent(LlmAgent):
    @property
    def task_agent(self):
        return self.find_sub_agent('task_agent')
    @property
    def calendar_agent(self):
        return self.find_sub_agent('calendar_agent')
    @property
    def notes_agent(self):
        return self.find_sub_agent('notes_agent')
    @property
    def insight_agent(self):
        return self.find_sub_agent('insight_agent')

    def __init__(self):
        # Instantiate sub-agents
        task = TaskAgent()
        cal = CalendarAgent()
        notes = NotesAgent()
        ins = InsightAgent()
        
        super().__init__(
            model='gemini-2.0-flash',
            name='orchestrator',
            description='Executive AI Assistant coordinating specialized agents.',
            instruction='''You are AutoRoutine AI's orchestrator.
                You help the user manage tasks, calendar, notes, and productivity insights.
                Delegate work to specialized tools (agents) when needed:
                - task_agent: handles all TODOs and task lists.
                - calendar_agent: handles schedules and events.
                - notes_agent: handles memo taking and summarization.
                - insight_agent: handles context graph analysis and proactive help.
                - run_workflow: for complex multi-step processes like morning_briefing.
                Synthesize responses elegantly.''',
            sub_agents=[task, cal, notes, ins],
            # Wrap each agent in an AgentTool
            tools=[
                AgentTool(task),
                AgentTool(cal),
                AgentTool(notes),
                AgentTool(ins),
                self.run_workflow
            ]
        )

    async def run_workflow(self, user_id: str, workflow: str) -> str:
        '''Execute complex predefined agent sequences'''
        # We manually find subagents for internal logic
        task = self.task_agent
        calendar = self.calendar_agent
        insight = self.insight_agent
        
        if workflow == 'morning_briefing':
            events = await calendar.get_upcoming_events(user_id=user_id, days_ahead=1)
            tasks = await task.list_tasks(user_id=user_id, status='pending')
            await insight.build_context_graph(user_id=user_id)
            insights = await insight.get_insights(user_id=user_id)
            return f"Morning Briefing: {len(events)} events, {len(tasks)} tasks, {len(insights.get('insights', []))} insights."
            
        return f"Unknown workflow requested: {workflow}"

    def agent_count(self) -> int:
        return 1 + len(self.sub_agents)
