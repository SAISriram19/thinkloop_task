from database import Database
import os
from dotenv import load_dotenv

load_dotenv()

def test_supabase_connection():
    try:
        print("Attempting to connect to Supabase...")
        db = Database()
        print("Supabase connection test successful!")
        
        # Optional: Try to fetch some data to confirm
        print("Attempting to fetch school info...")
        school_info = db.get_school_info()
        if school_info:
            print(f"School info retrieved: {school_info['name']}")
        else:
            print("No school info found, but connection is OK.")
            
    except Exception as e:
        print(f"Supabase connection test failed: {e}")

if __name__ == "__main__":
    test_supabase_connection() 