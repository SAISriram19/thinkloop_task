import asyncio
import os
import uuid
from datetime import datetime
import json
import traceback
import threading
import sys  # Import the sys module

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    google,
    noise_cancellation,
)

from database import Database
from translations import get_translation
from calendar_manager import CalendarManager
from email_manager import EmailManager

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize database connection
db = Database()

# Load knowledge base
def load_knowledge_base():
    with open('knowledge_base.json', 'r') as f:
        return json.load(f)

KNOWLEDGE_BASE = load_knowledge_base()

# Initialize school information in database
school_info = {
    'name': KNOWLEDGE_BASE['school_info']['name'],
    'address': KNOWLEDGE_BASE['school_info']['address'],
    'phone': KNOWLEDGE_BASE['school_info']['phone'],
    'email': KNOWLEDGE_BASE['school_info']['email'],
    'website': KNOWLEDGE_BASE['school_info']['website'],
    'office_hours': KNOWLEDGE_BASE['hours']['office'],
    'class_hours': KNOWLEDGE_BASE['hours']['classes'],
    'summer_hours': KNOWLEDGE_BASE['hours']['summer']
}
db.initialize_school_info(school_info)

def ordinal(n):
    # Helper to get ordinal suffix for a day
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return str(n) + suffix

def format_datetime(dt):
    day = dt.strftime('%A')
    month = dt.strftime('%B')
    day_num = ordinal(dt.day)
    time = dt.strftime('%I:%M %p').lstrip('0')
    return f"{day}, {month} {day_num} at {time}"

class Assistant(Agent):
    def __init__(self) -> None:
        # Get school info from database
        school_info = db.get_school_info()
        
        system_prompt = f"""You are a professional school receptionist for {school_info['name']}. 
        Your role is to:
        1. Greet callers warmly and professionally
        2. Handle inquiries about school hours, admissions, and general information
        3. Take messages for staff members
        4. Provide clear and concise information
        5. Maintain a friendly and helpful tone
        6. Transfer calls to appropriate departments when needed
        7. Schedule appointments with teachers, ensuring to collect the parent's name, student's name, teacher's name, preferred date and time, purpose of the meeting, contact number, and email address.
        8. Log the caller's name using the 'log_caller_information' tool when identified.
        9. Support multiple languages (English and Hindi)
        10. Track and analyze call patterns

        You have access to the following information:
        - School Name: {school_info['name']}
        - School Address: {school_info['address']}
        - School Hours: {school_info['office_hours']}
        - Main Phone: {school_info['phone']}
        - Email: {school_info['email']}
        - Website: {school_info['website']}

        Department Extensions:
        {json.dumps(KNOWLEDGE_BASE['departments'], indent=2)}

        Emergency Contacts:
        {json.dumps(KNOWLEDGE_BASE['emergency_contacts'], indent=2)}

        Frequently Asked Questions (FAQs):
        {json.dumps(KNOWLEDGE_BASE['faq'], indent=2)}

        School Holidays:
        {json.dumps(KNOWLEDGE_BASE['holidays'], indent=2)}

        Important Dates:
        {json.dumps(KNOWLEDGE_BASE['important_dates'], indent=2)}

        Courses Offered:
        {json.dumps(KNOWLEDGE_BASE['courses_offered'], indent=2)}

        Always be polite, patient, and professional in your responses.
        Use the knowledge base to provide accurate information.
        If you don't know something, offer to transfer the call to the appropriate department.
        
        IMPORTANT: Your initial greeting should always be: "Hello, this is Delhi Public School reception. How may I help you?" """

        super().__init__(instructions=system_prompt)
        self.current_language = 'en'
        self.call_id = str(uuid.uuid4())
        self.call_start_time = datetime.now()
        self.calendar = CalendarManager()
        self.email_manager = EmailManager()

    async def handle_incoming_call(self, participant):
        """Handle incoming call from a participant"""
        print(f"Received call from {participant.identity}")
        
        # Log call start
        db.log_call(self.call_id, self.call_start_time, self.current_language)

        # Debug: Print API key to verify loading
        gemini_api_key = os.getenv('GOOGLE_API_KEY')
        if gemini_api_key:
            print(f"[DEBUG] GOOGLE_API_KEY loaded: {'*' * (len(gemini_api_key) - 5)}{gemini_api_key[-5:]}") # Only show last 5 chars for security
        else:
            print("[DEBUG] GOOGLE_API_KEY not loaded or is empty.")

        # Create a new session with Gemini and Google TTS
        session = AgentSession(
            llm=google.beta.realtime.RealtimeModel(
                model="gemini-2.0-flash-exp",
                voice="Puck",
                temperature=0.8,
                api_key=os.getenv('GOOGLE_API_KEY') # Pass API key
            ),
            tts=google.TTS() # Removed voice and gender parameters
        )

        await session.start(
            room=self.room,
            agent=self,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )

        # Send welcome message in current language
        welcome_message = get_translation('greeting', self.current_language)
        await session.tts.say(welcome_message)

    async def handle_track_subscribed(self, track, publication, participant):
        """Handle subscribed audio track"""
        if track.kind == "audio":
            print(f"Processing audio from {participant.identity}")
            # The noise cancellation plugin will automatically process the audio

    async def switch_language(self, language, session):
        """Switch the conversation language"""
        if language in ['en', 'hi']:
            self.current_language = language
            message = get_translation('language_switch', language, language=language)
            await session.tts.say(message)

    async def log_caller_information(self, caller_name: str, session):
        """Logs the caller's name and updates the call record.
        This function should be called when the agent successfully identifies the caller's name.
        Args:
            caller_name (str): The name of the caller.
        """
        print(f"\n[DEBUG] Logging caller information: {caller_name}")
        try:
            # Update the existing call log with the caller's name
            db.update_call_details(self.call_id, caller_name=caller_name)
            print(f"[DEBUG] Successfully updated call log with caller name: {caller_name}")
            await session.tts.say(f"Thank you, {caller_name}. I have noted your name.")
        except Exception as e:
            print(f"[DEBUG] Error logging caller information: {e}")
            await session.tts.say("I apologize, I was unable to note your name at this time.")
            return False

    async def schedule_appointment(self, parent_name, student_name, teacher_name, date_time, purpose, contact_number, email, session):
        """Schedule an appointment with a teacher and add to Google Calendar and send confirmation email"""
        try:
            print(f"\n[DEBUG] Starting appointment scheduling with data:")
            print(f"Parent: {parent_name}")
            print(f"Student: {student_name}")
            print(f"Teacher: {teacher_name}")
            print(f"DateTime: {date_time}")
            print(f"Purpose: {purpose}")
            print(f"Contact: {contact_number}")
            print(f"Email: {email}")
            
            # Add to local DB
            print("\n[DEBUG] Attempting to add to local database...")
            appointment_id = db.add_appointment(
                parent_name, student_name, teacher_name, date_time,
                purpose, contact_number, email, self.current_language
            )
            print(f"[DEBUG] Local DB appointment_id: {appointment_id}")
            
            # Add to Google Calendar
            print("\n[DEBUG] Attempting to add to Google Calendar...")
            print(f"DateTime being sent to calendar: {date_time}")
            cal_result = self.calendar.create_appointment(
                teacher_name, parent_name, student_name, date_time
            )
            print(f"[DEBUG] Google Calendar result: {cal_result}")

            formatted_time = format_datetime(date_time)
            if appointment_id and cal_result['status'] == 'success':
                print("\n[DEBUG] Both local DB and Google Calendar operations successful")
                message = f"Your appointment has been scheduled for {formatted_time}. It has also been added to the school calendar."
                await session.tts.say(message)

                # Send confirmation email
                if email:
                    print("\n[DEBUG] Attempting to send confirmation email...")
                    self.email_manager.send_appointment_confirmation_email(
                        email, parent_name, student_name, teacher_name, formatted_time, purpose
                    )
                    print("[DEBUG] Email sent successfully")
                else:
                    print("[DEBUG] No email address provided for confirmation email.")

                return True
            elif cal_result['status'] == 'conflict':
                print("\n[DEBUG] Calendar conflict detected")
                suggestions = cal_result['suggestions']
                if suggestions:
                    suggestion_texts = [format_datetime(s) for s in suggestions]
                    message = get_translation('appointment_conflict', self.current_language, suggestions=", ".join(suggestion_texts))
                else:
                    message = get_translation('appointment_conflict_no_suggestions', self.current_language)
                await session.tts.say(message)
                return False
            elif cal_result['status'] == 'error':
                print(f"\n[DEBUG] Calendar error: {cal_result['message']}")
                message = f"I encountered an error while trying to add the appointment to Google Calendar: {cal_result['message']}. Please try again later."
                await session.tts.say(message)
                return False
            else:
                print("\n[DEBUG] Appointment scheduling failed")
                message = get_translation('appointment_failed', self.current_language)
                await session.tts.say(message)
                return False
        except Exception as e:
            print(f"\n[DEBUG] Exception in schedule_appointment: {str(e)}")
            print(f"Exception type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False


async def entrypoint(ctx: agents.JobContext):
    agent = Assistant()
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Puck",
            temperature=0.8,
            api_key=os.getenv('GOOGLE_API_KEY') # Pass API key
        ),
        tts=google.TTS() # Removed voice and gender parameters
    )

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    # Log call start
    db.log_call(agent.call_id, agent.call_start_time, agent.current_language)

    # Debug: Print API key to verify loading
    gemini_api_key = os.getenv('GOOGLE_API_KEY')
    if gemini_api_key:
        print(f"[DEBUG] GOOGLE_API_KEY loaded: {'*' * (len(gemini_api_key) - 5)}{gemini_api_key[-5:]}") # Only show last 5 chars for security
    else:
        print("[DEBUG] GOOGLE_API_KEY not loaded or is empty.")

    # Send welcome message
    welcome_message = get_translation('greeting', agent.current_language)
    await session.tts.say(welcome_message)

    try:
        # Keep the agent running
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error in main loop: {e}")
        raise
    finally:
        # Log call end
        end_time = datetime.now()
        duration = (end_time - agent.call_start_time).seconds
        db.update_call(agent.call_id, end_time, duration)


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))