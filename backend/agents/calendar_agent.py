from google.adk.agents import LlmAgent
from db.singleton import get_db
from datetime import datetime, timedelta
import structlog
from typing import List, Optional

log = structlog.get_logger()

class CalendarAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            model='gemini-2.0-flash',
            name='calendar_agent',
            description='Manages calendar events: create, find free slots, list upcoming',
            instruction='''You are a calendar management specialist.
                You help the user schedule events, find free time, and manage their day.
                Always use proper ISO 8601 strings for dates and times.''',
            tools=[self.create_event, self.find_free_slots, self.get_upcoming_events]
        )


    async def create_event(self, user_id: str, title: str, start_time: str, end_time: str, attendees: str = "") -> dict:
        '''Create a calendar event. attendees should be a comma-separated string of emails.'''
        db = get_db()
        attendee_list = [a.strip() for a in attendees.split(',') if a.strip()] if attendees else []
        data = {
            'user_id': user_id, 'title': title, 
            'start_time': start_time, 'end_time': end_time, 
            'attendees': attendee_list, 'task_ids': []
        }
        event_id = await db.create('events', data)
        log.info('event.created', id=event_id, title=title)
        return {'event_id': event_id, 'status': 'created'}


    async def get_upcoming_events(self, user_id: str, days_ahead: int = 7) -> list:
        '''Retrieve calendar events for the next N days'''
        db = get_db()
        events = await db.query('events', [('user_id', '==', user_id)])
        now_str = datetime.utcnow().isoformat()
        cutoff = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()
        upcoming = [e for e in events if now_str <= e.get('start_time', '') <= cutoff]
        return sorted(upcoming, key=lambda e: e.get('start_time', ''))


    async def find_free_slots(self, user_id: str, duration_mins: int = 60, days_ahead: int = 3) -> list:
        '''Find available time slots for a meeting of given duration within work hours (9 AM - 6 PM)'''
        db = get_db()
        events = await db.query('events', [('user_id', '==', user_id)])
        free_slots = []
        for day_offset in range(days_ahead):
            day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=day_offset+1)
            busy_times = []
            for e in events:
                st = e.get('start_time', '')
                et = e.get('end_time', '')
                if st and st.startswith(day.strftime("%Y-%m-%d")):
                    try:
                        busy_times.append((
                            datetime.fromisoformat(st).hour * 60 + datetime.fromisoformat(st).minute,
                            datetime.fromisoformat(et).hour * 60 + datetime.fromisoformat(et).minute
                        ))
                    except Exception:
                        pass
            busy_times.sort()
            current, work_end = 9 * 60, 18 * 60
            for b_start, b_end in busy_times:
                if current + duration_mins <= b_start:
                    free_slots.append({'start': day.replace(hour=current//60, minute=current%60).isoformat(),
                                       'end': day.replace(hour=(current+duration_mins)//60, minute=(current+duration_mins)%60).isoformat()})
                current = max(current, b_end)
            if current + duration_mins <= work_end:
                free_slots.append({'start': day.replace(hour=current//60, minute=current%60).isoformat(),
                                   'end': day.replace(hour=(current+duration_mins)//60, minute=(current+duration_mins)%60).isoformat()})
        return free_slots[:5]
