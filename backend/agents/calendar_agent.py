from google.adk.agents import LlmAgent
from db.singleton import get_db
from datetime import datetime, timedelta
import structlog
from typing import List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

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

    async def _get_google_service(self, user_id: str):
        db = get_db()
        user_doc_ref = db.db.collection('users').document(user_id)
        user_doc = await user_doc_ref.get()
        if user_doc.exists:
            data = user_doc.to_dict()
            creds_data = data.get('google_calendar_creds')
            if creds_data:
                creds = Credentials(
                    token=creds_data['token'],
                    refresh_token=creds_data['refresh_token'],
                    token_uri=creds_data['token_uri'],
                    client_id=creds_data['client_id'],
                    client_secret=creds_data['client_secret'],
                    scopes=creds_data['scopes']
                )
                service = build('calendar', 'v3', credentials=creds)
                return service
        return None

    async def create_event(self, user_id: str, title: str, start_time: str, end_time: str, attendees: str = "") -> dict:
        '''Create a calendar event. attendees should be a comma-separated string of emails. start_time and end_time MUST be valid ISO 8601 with timezone offset (e.g., 2026-04-09T09:00:00+00:00)'''
        service = await self._get_google_service(user_id)
        if service:
            # Use Google Calendar
            attendee_list = [{'email': a.strip()} for a in attendees.split(',') if a.strip()] if attendees else []
            event = {
                'summary': title,
                'start': {
                    'dateTime': start_time,
                },
                'end': {
                    'dateTime': end_time,
                },
                'attendees': attendee_list,
            }
            import asyncio
            loop = asyncio.get_event_loop()
            created_event = await loop.run_in_executor(None, lambda: service.events().insert(calendarId='primary', body=event).execute())
            log.info('google_calendar.event.created', id=created_event.get('id'), title=title)
            return {'event_id': created_event.get('id'), 'status': 'created_in_google_calendar', 'link': created_event.get('htmlLink')}
        else:
            # Fallback to local
            db = get_db()
            attendee_list = [a.strip() for a in attendees.split(',') if a.strip()] if attendees else []
            data = {
                'user_id': user_id, 'title': title, 
                'start_time': start_time, 'end_time': end_time, 
                'attendees': attendee_list, 'task_ids': []
            }
            event_id = await db.create('events', data)
            log.info('local_event.created', id=event_id, title=title)
            return {'event_id': event_id, 'status': 'created_locally'}

    async def get_upcoming_events(self, user_id: str, days_ahead: int = 7) -> list:
        '''Retrieve calendar events for the next N days'''
        service = await self._get_google_service(user_id)
        cutoff = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
        now_str = datetime.utcnow().isoformat() + 'Z'
        
        if service:
            import asyncio
            loop = asyncio.get_event_loop()
            events_result = await loop.run_in_executor(None, lambda: service.events().list(
                calendarId='primary', timeMin=now_str, timeMax=cutoff,
                maxResults=100, singleEvents=True, orderBy='startTime').execute()
            )
            events = events_result.get('items', [])
            formatted_events = []
            for e in events:
                start = e.get('start', {}).get('dateTime', e.get('start', {}).get('date'))
                end = e.get('end', {}).get('dateTime', e.get('end', {}).get('date'))
                formatted_events.append({
                    'id': e['id'],
                    'title': e.get('summary', 'Busy'),
                    'start_time': start,
                    'end_time': end
                })
            return formatted_events
        else:
            db = get_db()
            events = await db.query('events', [('user_id', '==', user_id)])
            now_str_local = datetime.utcnow().isoformat()
            cutoff_local = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()
            
            upcoming = []
            for e in events:
                # Ensure start_time is a string for comparison and serialization
                st = str(e.get('start_time', ''))
                if now_str_local <= st <= cutoff_local:
                    event_copy = dict(e)
                    # Convert any potential Firestore timestamp objects to strings
                    for key, val in event_copy.items():
                        if not isinstance(val, (str, int, float, bool, type(None), list, dict)):
                            event_copy[key] = str(val)
                    upcoming.append(event_copy)
            
            return sorted(upcoming, key=lambda e: str(e.get('start_time', '')))

    async def find_free_slots(self, user_id: str, duration_mins: int = 60, days_ahead: int = 3) -> list:
        '''Find available time slots for a meeting of given duration within work hours (9 AM - 6 PM)'''
        upcoming_events = await self.get_upcoming_events(user_id, days_ahead)
        
        free_slots = []
        for day_offset in range(days_ahead):
            day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=day_offset+1)
            busy_times = []
            for e in upcoming_events:
                st = e.get('start_time', '')
                et = e.get('end_time', '')
                
                if st and st.startswith(day.strftime("%Y-%m-%d")):
                    try:
                        st_dt = datetime.fromisoformat(st.replace('Z', '+00:00'))
                        et_dt = datetime.fromisoformat(et.replace('Z', '+00:00'))
                        busy_times.append((
                            st_dt.hour * 60 + st_dt.minute,
                            et_dt.hour * 60 + et_dt.minute
                        ))
                    except Exception:
                        busy_times.append((0, 24*60))
                        
            busy_times.sort()
            current, work_end = 9 * 60, 18 * 60
            for b_start, b_end in busy_times:
                if current + duration_mins <= b_start:
                    free_slots.append({'start': day.replace(hour=current//60, minute=current%60).isoformat() + "Z",
                                       'end': day.replace(hour=(current+duration_mins)//60, minute=(current+duration_mins)%60).isoformat() + "Z"})
                current = max(current, b_end)
            if current + duration_mins <= work_end:
                free_slots.append({'start': day.replace(hour=current//60, minute=current%60).isoformat() + "Z",
                                   'end': day.replace(hour=(current+duration_mins)//60, minute=(current+duration_mins)%60).isoformat() + "Z"})
        return free_slots[:5]
