from google.adk.agents import LlmAgent
from db.singleton import get_db
import structlog

log = structlog.get_logger()

class InsightAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            model='gemini-2.0-flash',
            name='insight_agent',
            description='Builds Context Graph and reasons over tasks, events, and notes to surface proactive insights',
            instruction='''You are an AI analyst that works over the user's Context Graph.
                You look for patterns, upcoming deadlines, and conflicts across tasks and calendar.
                Provide structured summaries of user's current situation.''',
            tools=[self.build_context_graph, self.get_insights]
        )


    async def build_context_graph(self, user_id: str) -> dict:
        '''Generate a unified context of tasks and calendar events'''
        db = get_db()
        tasks = await db.query('tasks', [('user_id', '==', user_id)])
        events = await db.query('events', [('user_id', '==', user_id)])
        graph = {
            'nodes': len(tasks) + len(events),
            'tasks': [t['title'] for t in tasks],
            'upcoming': [e['title'] for e in events[:3]]
        }
        log.info('graph.built', nodes=graph['nodes'])
        return graph


    async def get_insights(self, user_id: str) -> dict:
        '''Analyze potential conflicts or high-priority items'''
        db = get_db()
        tasks = await db.query('tasks', [('user_id', '==', user_id), ('priority', '>=', 4)])
        events = await db.query('events', [('user_id', '==', user_id)])
        
        insights = []
        if len(tasks) > 3:
            insights.append("Warning: You have multiple high-priority tasks pending.")
        if any('meeting' in e.get('title', '').lower() for e in events):
            insights.append("Reminder: You have meetings scheduled that might require preparation.")
            
        return {'user_id': user_id, 'insights': insights}
