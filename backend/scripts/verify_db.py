import sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
import asyncio
from db.firestore_client import FirestoreClient

async def verify():
    db = FirestoreClient()
    tasks = await db.query('tasks', [])
    events = await db.query('events', [])
    notes = await db.query('notes', [])
    print(f'tasks:  {len(tasks)} documents')
    print(f'events: {len(events)} documents')
    print(f'notes:  {len(notes)} documents')
    if tasks:
        print(f'first task: {tasks[0]["title"]}')
    print('SUCCESS - Firestore is working correctly!')

asyncio.run(verify())
