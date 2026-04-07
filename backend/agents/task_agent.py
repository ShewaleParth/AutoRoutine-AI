from google.adk.agents import LlmAgent
from db.singleton import get_db
import structlog

log = structlog.get_logger()

class TaskAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            model='gemini-2.0-flash',
            name='task_agent',
            description='Manages tasks: create, list, update, prioritise',
            instruction='''You are a task management specialist.
                You create, retrieve, and update tasks from Firestore.
                Always confirm actions taken and list resulting task IDs.''',
            tools=[self.create_task, self.list_tasks, self.update_task, self.prioritise]
        )


    async def create_task(self, user_id: str, title: str, priority: int = 3, due_date: str = None) -> dict:
        '''Create a new task and store in Firestore'''
        db = get_db()
        data = {'user_id': user_id, 'title': title, 'priority': priority, 'status': 'pending'}
        if due_date: data['due_date'] = due_date
        task_id = await db.create('tasks', data)
        log.info('task.created', id=task_id, title=title)
        return {'task_id': task_id, 'status': 'created'}


    async def list_tasks(self, user_id: str, status: str = None) -> list:
        '''Retrieve tasks for a user with optional status filter'''
        db = get_db()
        filters = [('user_id', '==', user_id)]
        if status: filters.append(('status', '==', status))
        return await db.query('tasks', filters)


    async def update_task(self, task_id: str, status: str = None, priority: int = None) -> dict:
        '''Update an existing task status or priority'''
        db = get_db()
        updates = {}
        if status: updates['status'] = status
        if priority: updates['priority'] = priority
        if updates:
            await db.update('tasks', task_id, updates)
        return {'task_id': task_id, 'updated': True, 'fields': list(updates.keys())}

    async def prioritise(self, user_id: str) -> list:
        '''List all pending tasks ordered by priority (highest first)'''
        db = get_db()
        tasks = await db.query('tasks', [('user_id', '==', user_id), ('status', '==', 'pending')])
        return sorted(tasks, key=lambda t: t.get('priority', 0), reverse=True)
