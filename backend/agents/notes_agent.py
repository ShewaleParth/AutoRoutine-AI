from google.adk.agents import LlmAgent
from db.singleton import get_db
import structlog
import re

log = structlog.get_logger()

class NotesAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            model='gemini-2.0-flash',
            name='notes_agent',
            description='Manages notes, summaries, and extracts entities like action items, people, and deadlines',
            instruction='''You are a documentation specialist.
                You save raw text as notes and use NLP/Regex to extract structured entities.
                Confirm when notes are saved and summarize the extracted contents.''',
            tools=[self.create_note, self.search_notes]
        )


    async def create_note(self, user_id: str, content: str, auto_extract: bool = True) -> dict:
        '''Save a text note and optionally extract entities'''
        db = get_db()
        entities = {}
        if auto_extract:
            # Simple simulation of entity extraction
            entities['action_items'] = re.findall(r'(\[ \]|TODO:?|Action:?) (.*)', content)
            entities['dates'] = re.findall(r'\d{4}-\d{2}-\d{2}', content)
            entities['people'] = re.findall(r'@(\w+)', content)
        
        data = {
            'user_id': user_id, 
            'content': content, 
            'entities': entities, 
            'created_at': structlog.get_context().get('timestamp', '')
        }
        note_id = await db.create('notes', data)
        log.info('note.created', id=note_id, entities=len(entities))
        return {'note_id': note_id, 'extracted': list(entities.keys())}


    async def search_notes(self, user_id: str, query: str) -> list:
        '''Search notes by keyword in content'''
        db = get_db()
        notes = await db.query('notes', [('user_id', '==', user_id)])
        return [n for n in notes if query.lower() in n.get('content', '').lower()]
