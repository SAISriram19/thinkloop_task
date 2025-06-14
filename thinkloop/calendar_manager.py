from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
from datetime import datetime, timedelta
import pytz

SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarManager:
    def __init__(self):
        self.creds = None
        self.service = None
        self.calendar_id = 'primary'  # Default calendar ID
        self.initialize_calendar()

    def initialize_calendar(self):
        """Initialize Google Calendar API connection"""
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('calendar', 'v3', credentials=self.creds)

    def check_availability(self, start_time, end_time):
        """Check if the time slot is available"""
        events_result = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return len(events_result.get('items', [])) == 0

    def suggest_alternative_times(self, desired_time, duration_minutes=30, days_to_check=7):
        """Suggest alternative times when there's a conflict"""
        suggested_times = []
        current_time = desired_time
        
        # Check next 7 days
        for day in range(days_to_check):
            # Check morning slots (9 AM to 12 PM)
            for hour in range(9, 12):
                for minute in [0, 30]:
                    check_time = current_time.replace(hour=hour, minute=minute)
                    end_time = check_time + timedelta(minutes=duration_minutes)
                    
                    if self.check_availability(check_time, end_time):
                        suggested_times.append(check_time)
                        if len(suggested_times) >= 3:  # Return top 3 suggestions
                            return suggested_times
            
            # Check afternoon slots (2 PM to 5 PM)
            for hour in range(14, 17):
                for minute in [0, 30]:
                    check_time = current_time.replace(hour=hour, minute=minute)
                    end_time = check_time + timedelta(minutes=duration_minutes)
                    
                    if self.check_availability(check_time, end_time):
                        suggested_times.append(check_time)
                        if len(suggested_times) >= 3:
                            return suggested_times
            
            current_time += timedelta(days=1)
        
        return suggested_times

    def create_appointment(self, teacher_name, parent_name, student_name, start_time, duration_minutes=30):
        """Create a new appointment in Google Calendar"""
        end_time = start_time + timedelta(minutes=duration_minutes)
        print(f"[CalendarManager] Attempting to create event for {teacher_name} on {start_time} - {end_time}")
        
        # Check for conflicts
        if not self.check_availability(start_time, end_time):
            print(f"[CalendarManager] Conflict detected for {start_time}")
            return {
                'status': 'conflict',
                'suggestions': self.suggest_alternative_times(start_time, duration_minutes)
            }
        
        # Create the event
        event = {
            'summary': f'Parent-Teacher Meeting: {parent_name} with {teacher_name}',
            'description': f'Student: {student_name}\nParent: {parent_name}\nTeacher: {teacher_name}',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
        }
        
        try:
            event = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
            print(f"[CalendarManager] Event created successfully: {event.get('htmlLink')}")
            return {
                'status': 'success',
                'event_id': event['id'],
                'start_time': start_time,
                'end_time': end_time
            }
        except Exception as e:
            print(f"[CalendarManager] Error creating event: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_teacher_schedule(self, teacher_name, date):
        """Get a teacher's schedule for a specific date"""
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())
        
        events_result = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', []) 