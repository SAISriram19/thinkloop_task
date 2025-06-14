from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

class Database:
    def __init__(self):
        """Initialize Supabase client"""
        try:
            self.supabase_url = os.getenv('SUPABASE_URL')
            self.supabase_key = os.getenv('SUPABASE_KEY')
            
            if not self.supabase_url or not self.supabase_key:
                raise ValueError("Missing Supabase credentials in .env file")
                
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            print("Successfully connected to Supabase")
        except Exception as e:
            print(f"Error initializing Supabase client: {str(e)}")
            raise

    def initialize_tables(self):
        """Check if required tables exist in Supabase"""
        try:
            # Check school_info table
            response = self.supabase.table('school_info').select('*').limit(1).execute()
            print("school_info table exists")
            
            # Check teachers table
            response = self.supabase.table('teachers').select('*').limit(1).execute()
            print("teachers table exists")
            
            # Check appointments table
            response = self.supabase.table('appointments').select('*').limit(1).execute()
            print("appointments table exists")
            
            # Check call_analytics table
            response = self.supabase.table('call_analytics').select('*').limit(1).execute()
            print("call_analytics table exists")
            
        except Exception as e:
            print(f"Error checking tables: {str(e)}")
            raise

    def initialize_school_info(self, school_info):
        """Initialize school information in the database"""
        try:
            # Check if school info already exists
            response = self.supabase.table('school_info').select('*').execute()
            
            if not response.data:
                # Insert new school info
                response = self.supabase.table('school_info').insert(school_info).execute()
                print("School information initialized successfully")
            else:
                print("School information already exists")
                
        except Exception as e:
            print(f"Error initializing school info: {str(e)}")
            raise

    def add_appointment(self, parent_name, student_name, teacher_name, date_time, purpose, contact_number, email, language):
        """Add a new appointment to the database"""
        try:
            appointment_data = {
                'parent_name': parent_name,
                'student_name': student_name,
                'teacher_name': teacher_name,
                'date_time': date_time.isoformat(),
                'purpose': purpose,
                'contact_number': contact_number,
                'email': email,
                'language': language,
                'status': 'scheduled'
            }
            
            response = self.supabase.table('appointments').insert(appointment_data).execute()
            
            if response.data:
                print(f"Appointment added successfully with ID: {response.data[0]['id']}")
                return response.data[0]['id']
            else:
                print("Failed to add appointment")
                return None
                
        except Exception as e:
            print(f"Error adding appointment: {str(e)}")
            return None

    def log_call(self, call_id, start_time, language, caller_name=None):
        """Log a new call in the database"""
        try:
            call_data = {
                'call_id': call_id,
                'start_time': start_time.isoformat(),
                'language': language,
                'status': 'in_progress',
                'caller_name': caller_name
            }
            
            response = self.supabase.table('call_analytics').insert(call_data).execute()
            
            if response.data:
                print(f"Call logged successfully with ID: {response.data[0]['id']}")
                return response.data[0]['id']
            else:
                print("Failed to log call")
                return None
                
        except Exception as e:
            print(f"Error logging call: {str(e)}")
            return None

    def update_call(self, call_id, end_time, duration):
        """Update call information when it ends"""
        try:
            update_data = {
                'end_time': end_time.isoformat(),
                'duration': duration,
                'status': 'completed'
            }
            
            response = self.supabase.table('call_analytics').update(update_data).eq('call_id', call_id).execute()
            
            if response.data:
                print(f"Call updated successfully")
                return True
            else:
                print("Failed to update call")
                return False
                
        except Exception as e:
            print(f"Error updating call: {str(e)}")
            return False

    def update_call_details(self, call_id, **kwargs):
        """Update specific details of an existing call record in the database.
        Args:
            call_id (str): The ID of the call to update.
            **kwargs: Keyword arguments for the fields to update (e.g., caller_name='John Doe', purpose='inquiry').
        """
        try:
            if not kwargs:
                print("[DEBUG] No details provided to update for call_id: {call_id}")
                return False
            
            # Ensure timestamps are correctly formatted if passed
            update_data = {}
            for key, value in kwargs.items():
                if isinstance(value, datetime):
                    update_data[key] = value.isoformat()
                else:
                    update_data[key] = value

            response = self.supabase.table('call_analytics').update(update_data).eq('call_id', call_id).execute()
            
            if response.data:
                print(f"Call details updated successfully for call_id: {call_id}")
                return True
            else:
                print(f"Failed to update call details for call_id: {call_id}. Response: {response.data}")
                return False
                
        except Exception as e:
            print(f"Error updating call details for call_id {call_id}: {str(e)}")
            return False

    def get_appointments(self, teacher_name=None, start_date=None, end_date=None):
        """Get appointments from the database with optional filters"""
        try:
            query = self.supabase.table('appointments').select('*')
            
            if teacher_name:
                query = query.eq('teacher_name', teacher_name)
            if start_date:
                query = query.gte('date_time', start_date.isoformat())
            if end_date:
                query = query.lte('date_time', end_date.isoformat())
                
            response = query.execute()
            
            if response.data:
                return response.data
            else:
                print("No appointments found")
                return []
                
        except Exception as e:
            print(f"Error getting appointments: {str(e)}")
            return []

    def get_all_teachers(self):
        """Get all teachers from the database"""
        try:
            response = self.supabase.table('teachers').select('*').execute()
            
            if response.data:
                return response.data
            else:
                print("No teachers found")
                return []
                
        except Exception as e:
            print(f"Error getting teachers: {str(e)}")
            return []

    def get_teacher_by_name(self, name):
        """Get a specific teacher by name"""
        try:
            response = self.supabase.table('teachers').select('*').eq('name', name).execute()
            
            if response.data:
                return response.data[0]
            else:
                print(f"No teacher found with name: {name}")
                return None
                
        except Exception as e:
            print(f"Error getting teacher: {str(e)}")
            return None

    def get_school_info(self):
        """Get school information from the database"""
        try:
            response = self.supabase.table('school_info').select('*').execute()
            
            if response.data:
                return response.data[0]
            else:
                print("No school information found")
                return None
                
        except Exception as e:
            print(f"Error getting school info: {str(e)}")
            return None

    def initialize_default_teachers(self):
        """Initialize default teachers in the database"""
        try:
            # Check if teachers already exist
            response = self.supabase.table('teachers').select('*').execute()
            
            if not response.data:
                default_teachers = [
                    {
                        'name': 'Dr. Sarah Johnson',
                        'subject': 'Mathematics',
                        'email': 'sarah.johnson@school.edu',
                        'phone': '555-0101',
                        'office_hours': '9:00 AM - 3:00 PM'
                    },
                    {
                        'name': 'Prof. Michael Chen',
                        'subject': 'Science',
                        'email': 'michael.chen@school.edu',
                        'phone': '555-0102',
                        'office_hours': '9:30 AM - 3:30 PM'
                    },
                    {
                        'name': 'Ms. Emily Rodriguez',
                        'subject': 'English',
                        'email': 'emily.rodriguez@school.edu',
                        'phone': '555-0103',
                        'office_hours': '10:00 AM - 4:00 PM'
                    },
                    {
                        'name': 'Mr. David Kim',
                        'subject': 'History',
                        'email': 'david.kim@school.edu',
                        'phone': '555-0104',
                        'office_hours': '9:00 AM - 3:00 PM'
                    },
                    {
                        'name': 'Dr. Lisa Patel',
                        'subject': 'Computer Science',
                        'email': 'lisa.patel@school.edu',
                        'phone': '555-0105',
                        'office_hours': '10:30 AM - 4:30 PM'
                    }
                ]
                response = self.supabase.table('teachers').insert(default_teachers).execute()
                print("Default teachers initialized successfully")
            else:
                print("Teachers already exist in the database.")
                
        except Exception as e:
            print(f"Error initializing default teachers: {str(e)}")
            raise 