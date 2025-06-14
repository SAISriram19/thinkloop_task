# School Reception Voice Agent

This is an AI-powered voice agent designed for school and college receptions, built to handle various inquiries and automate tasks like appointment scheduling and information retrieval. It leverages real-time communication, a large language model, and database integrations to provide a comprehensive receptionist solution.

## Features

*   **Intelligent Conversational AI:** Powered by Google Gemini, the agent can understand complex queries, maintain context, and generate human-like responses.
*   **Real-time Voice Interaction:** Utilizes LiveKit for seamless, low-latency audio communication, allowing for natural conversations.
*   **Multi-language Support:** Currently supports English and Hindi for diverse caller needs, with an extensible translation system.
*   **Dynamic Knowledge Base:** Provides up-to-date information on school hours, admissions, departments, FAQs, holidays, important dates, and course offerings, loaded from `knowledge_base.json`.
*   **Appointment Scheduling & Management:**
    *   Allows callers to schedule appointments with teachers.
    *   Performs real-time availability checks using Google Calendar.
    *   Handles scheduling conflicts by suggesting alternative times.
    *   Stores appointment details in a Supabase database.
*   **Google Calendar Integration:** Syncs all scheduled appointments directly to a designated Google Calendar.
*   **Email Confirmation:** Sends automated appointment confirmation emails to parents using SMTP.
*   **Caller Information Logging:** Can identify and log caller names within the call analytics database.
*   **Teacher & School Information Management:** Stores and retrieves school details and a list of teachers (and their subjects) from Supabase.
*   **Call Analytics:** Logs comprehensive call history, including unique call IDs, start/end times, duration, language used, and caller information, all stored in Supabase.
*   **Noise Cancellation:** Integrates LiveKit's noise cancellation plugin for clearer audio processing during calls.

## Technologies Used

*   **LiveKit:** The core real-time communication platform for voice input/output and session management.
    *   `livekit-agents`: Framework for building conversational AI agents.
    *   `livekit-plugins-google`: Integrates Google services, including Gemini LLM and Google TTS.
    *   `livekit-plugins-noise-cancellation`: For audio enhancement.
*   **Google Gemini (LLM):** The Large Language Model responsible for understanding user intent, generating responses, and deciding when to invoke tools.
    *   Specifically, `gemini-2.0-flash-exp` (via `google.beta.realtime.RealtimeModel`) for low-latency, real-time conversational AI.
*   **Google Cloud Platform:**
    *   **Google Calendar API:** For scheduling events and checking availability.
    *   **Google OAuth 2.0 Client:** For secure authentication with Google services.
*   **Supabase:** Used as the primary backend database. It provides a PostgreSQL database for storing:
    *   `school_info`: General school details.
    *   `teachers`: Teacher names and subjects.
    *   `appointments`: Scheduled meetings.
    *   `call_analytics`: Call history and caller information.
*   **Python:** The primary programming language.
    *   `python-dotenv`: For managing environment variables.
    *   `smtplib`, `email.mime`: For sending emails.
    *   `datetime`, `uuid`, `json`, `asyncio`, `os`: Standard libraries for various functionalities.
*   **Other Libraries:** `pytz` (for timezone handling).

## Prerequisites

*   Python 3.8 or higher.
*   A LiveKit account and a running LiveKit server instance (e.g., LiveKit Cloud or self-hosted). This is essential for the agent to connect and handle real-time audio.
*   A Google Cloud Project with:
    *   **Google Calendar API** enabled.
    *   **OAuth 2.0 Client ID credentials** (downloaded as `credentials.json`).
    *   A **Google Gemini API Key** (obtained from Google AI Studio).
*   A Supabase Project with your database URL and API key.
*   An SMTP server for sending emails (e.g., Gmail with App Passwords, or another email service).

## Setup

1.  **Clone this repository:**
    ```bash
    git clone https://github.com/SAISriram19/thinkloop_task
    cd thinkloop_task
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    
    .venv\Scripts\activate
    
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Google Credentials Setup:**
    *   **Google Calendar API:**
        *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
        *   Select or create your project.
        *   Navigate to **APIs & Services > Library** and enable **Google Calendar API**.
        *   Navigate to **APIs & Services > Credentials**.
        *   Click "Create Credentials" and select "OAuth client ID."
        *   Choose "Desktop app" (or "Web application" if you have a specific redirect URI).
        *   Download the `credentials.json` file.
        *   **Place this `credentials.json` file in your project's root directory.** The first time you run the agent, it will open a browser for authentication and create a `token.pickle` file.
    *   **Google Gemini API Key:** Obtain your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

5.  **Supabase Database Setup:**
    *   Go to your Supabase dashboard and create a new project.
    *   **Create the necessary tables** as defined by the `Database` class in `database.py`. The primary tables are `school_info`, `teachers`, `appointments`, and `call_analytics`. Ensure their schemas match the data inserted by `database.py` functions (e.g., `parent_name` in `appointments`, `caller_name` in `call_analytics`).
    *   You can use SQL commands in the Supabase SQL Editor to create these tables. For example:
        ```sql
        -- Example for appointments table (adjust columns as per your add_appointment method)
        CREATE TABLE appointments (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            parent_name TEXT,
            student_name TEXT,
            teacher_name TEXT,
            date_time TIMESTAMP WITH TIME ZONE,
            purpose TEXT,
            contact_number TEXT,
            email TEXT,
            language TEXT,
            status TEXT DEFAULT 'scheduled'
        );

        -- Example for teachers table
        CREATE TABLE teachers (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            name TEXT,
            subject TEXT
        );

        -- Example for call_analytics table
        CREATE TABLE call_analytics (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            call_id TEXT UNIQUE,
            start_time TIMESTAMP WITH TIME ZONE,
            end_time TIMESTAMP WITH TIME ZONE,
            duration INTEGER,
            language TEXT,
            status TEXT,
            caller_name TEXT
        );

        -- Example for school_info table
        CREATE TABLE school_info (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            name TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            office_hours TEXT,
            class_hours TEXT,
            summer_hours TEXT
        );
        ```
    *   Populate initial data: You can use the `add_sample_data.py` script to insert sample appointment data, or manually insert teachers/school info using SQL (as previously provided).

6.  **Create a `.env` file** in your project's root directory with the following environment variables:
    ```env
    # LiveKit Server Details (replace with your actual credentials)
    LIVEKIT_URL=ws://localhost:7880  # Or your LiveKit Cloud URL
    LIVEKIT_API_KEY=your_livekit_api_key
    LIVEKIT_API_SECRET=your_livekit_api_secret

    # Google Gemini API Key
    GOOGLE_API_KEY=your_google_gemini_api_key

    # Supabase Configuration (replace with your actual project details)
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_anon_key

    # Email Configuration (for appointment confirmations - optional, but recommended)
    EMAIL_USER=your_email@example.com
    EMAIL_PASS=your_email_password # Use App Password for Gmail
    EMAIL_HOST=smtp.gmail.com
    EMAIL_PORT=587 # Often 587 for TLS, or 465 for SSL
    ```
    *   **Important Note on `EMAIL_PASS` for Gmail:** If you're using a Gmail account, you will need to generate an "App password" instead of using your regular Gmail password. See [Google's documentation on App passwords](https://support.google.com/accounts/answer/185833).

7.  **Customize `knowledge_base.json` and `translations.py`:**
    *   Update `knowledge_base.json` with your school's specific information, FAQs, department details, holidays, important dates, and course offerings.
    *   Refine or add translations in `translations.py` as needed for supported languages.

## Usage

1.  **Activate your virtual environment** (if not already activated):
    ```bash
  
    .venv\\Scripts\\activate
    

2.  **Run the voice agent:**
    ```bash
    python agent.py console
    ```
    (Use `python agent.py` if running headlessly or integrating with a LiveKit client.)

3.  The agent will connect to your LiveKit server and start listening for incoming calls or console input (if running in `console` mode).

4.  **Interaction Flow:**
    *   The agent will play its initial welcome message.
    *   It will listen to the caller's request (e.g., "What are the school hours?", "My name is John Doe, can I schedule an appointment with Dr. Lisa Patel for my son Vihaan next Tuesday at 10 AM for a Computer Science discussion? My number is..., my email is...").
    *   The Gemini LLM will process the request, retrieve information from the knowledge base, or identify intent to use tools (like scheduling).
    *   If a tool is invoked (e.g., `schedule_appointment`), the agent will execute the corresponding Python function, interact with Supabase and Google Calendar, and send email confirmations.
    *   The agent will then generate and speak an appropriate response based on the outcome (e.g., "Your appointment has been scheduled," or "I'm sorry, I couldn't find that information.").


