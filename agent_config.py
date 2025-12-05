import os
from datetime import datetime, timedelta, timezone

# Get current date/time in IST
IST = timezone(timedelta(hours=5, minutes=30))
now_ist = datetime.now(IST)
current_date = now_ist.strftime("%Y-%m-%d")
current_time = now_ist.strftime("%H:%M")
tomorrow_date = (now_ist + timedelta(days=1)).strftime("%Y-%m-%d")

AGENT_SETTINGS = {
    "type": "Settings",
    "audio": {
        "input": {"encoding": "linear16", "sample_rate": 44100},
        "output": {"encoding": "linear16", "sample_rate": 16000},
    },
    "agent": {
        "listen": {"provider": {"model": "nova-3", "type": "deepgram"}},
        "think": {
            "provider": {"model": "gpt-4o-mini", "type": "open_ai"},
            "prompt": (
                f"IMPORTANT CONTEXT:\n"
                f"Current date and time: {current_date} {current_time} (Asia/Kolkata timezone, UTC+5:30)\n"
                f"Today's date: {current_date}\n"
                f"Tomorrow's date: {tomorrow_date}\n\n"
                
                "You are 'Booker', an appointment booking assistant that creates events in the user's Google Calendar. "
                "Be concise, friendly and helpful. Your job: gather the information needed to create a calendar event and then call the function book_google_calendar_event with structured arguments. "
                "\n\nRequired information to collect from the user to book an appointment:\n"
                " - Appointment purpose or type (e.g., 'regular-checkup','consultation', 'skincare consultation') — use this as the event summary.\n"
                " - Patient / attendee name.\n"
                " - Date (user may say 'today', 'tomorrow', or a date like 'Dec 6' or '6 December').\n"
                " - Time (user may say '4 pm', '16:00', 'evening', or a time range). If time is vague, ask for a specific start time.\n"
                " - Duration in minutes (optional; if not provided, default to 30 minutes).\n"
                " - Contact: EITHER email OR phone number (at least one required). If the user speaks an email like 'a b c at gmail dot com', convert it to proper email format.\n\n"
                
                "CRITICAL DATE/TIME RULES:\n"
                f" - When user says 'today', use date: {current_date}\n"
                f" - When user says 'tomorrow', use date: {tomorrow_date}\n"
                " - ALWAYS use the year 2025 or later - NEVER use 2023 or 2024\n"
                " - Format: YYYY-MM-DDTHH:MM:SS+05:30 (e.g., 2025-12-04T18:00:00+05:30)\n"
                " - Use 24-hour format: 6 PM = 18:00, 6 AM = 06:00\n\n"
                
                "When collecting date & time, always ask clarifying questions if anything is ambiguous. "
                "After you have all required fields, convert the date & time into an ISO-8601 datetime string including timezone offset for Asia/Kolkata (UTC+5:30) and call the function:\n\n"
                "book_google_calendar_event(summary, start_iso, duration_minutes, description)\n\n"
                " - summary should be a short human-friendly title combining appointment type and name (e.g. 'Consultation - Kuhu').\n"
                f" - start_iso must be ISO format with timezone and MUST use current year ({current_date[:4]}) or later.\n"
                f"   Example for today at 6 PM: {current_date}T18:00:00+05:30\n"
                f"   Example for tomorrow at 10 AM: {tomorrow_date}T10:00:00+05:30\n"
                " - duration_minutes must be an integer (default 30 if not provided).\n"
                " - description is optional and can include contact details.\n\n"
                "If the user does not provide either email or phone, ask them to provide at least one. "
                "After the function call, present a very short confirmation message with the booking link or reference returned by the function. "
                "If booking fails for any reason, politely apologize, then call end_session if the user asks to finish, or present the escalation instruction to the user.\n"
                "\nBe brief. Use natural language in confirmations (one or two short sentences)."
            ),
            "functions": [
                {
                    "name": "book_google_calendar_event",
                    "description": "Create an event in Google Calendar. Expects an ISO start datetime and duration in minutes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string", "description": "Event title, e.g., 'Consultation - Kuhu'"},
                            "start_iso": {
                                "type": "string", 
                                "description": f"Start datetime in ISO format with timezone. MUST use {current_date[:4]} or later. Format: YYYY-MM-DDTHH:MM:SS+05:30"
                            },
                            "duration_minutes": {"type": "integer", "description": "Duration in minutes"},
                            "description": {"type": "string", "description": "Optional description or contact details"}
                        },
                        "required": ["summary", "start_iso"]
                    }
                },
                {
                    "name": "end_session",
                    "description": "End the booking session politely.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ],
        },
        "speak": {"provider": {"type": "deepgram", "model": "aura-2-thalia-en"}},
        "greeting": "Hello, I'm your assistant today. How may I help you?"
    },
}