# agent_functions.py
import os
import re
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore

# -------------------------------
# Small helpers
# -------------------------------
IST = timezone(timedelta(hours=5, minutes=30))

_WORD_NUMBER_MAP = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "twentyone": 21, "twentytwo": 22,
    "twentythree": 23, "twentyfour": 24
}

def _words_to_number(s: str):
    # turn "six" -> 6, "twenty two" -> 22, "one two" -> 12 (spoken digits)
    if not s:
        return None
    s = s.lower().strip()
    # join separated digits ("one two three" -> "onetwothree") attempt converting as concatenated digits
    parts = re.findall(r"[a-z]+|\d+", s)
    # try digit-words concatenation first (for "one two" style)
    if all(p.isalpha() for p in parts):
        # try join as single tokens and map
        joined = "".join(parts)
        if joined in _WORD_NUMBER_MAP:
            return _WORD_NUMBER_MAP[joined]
        # if single part exists
        if len(parts) == 1 and parts[0] in _WORD_NUMBER_MAP:
            return _WORD_NUMBER_MAP[parts[0]]
        # try last two words combination (e.g., "twenty two")
        if len(parts) >= 2:
            pair = parts[-2] + parts[-1]
            if pair in _WORD_NUMBER_MAP:
                return _WORD_NUMBER_MAP[pair]
    # try extracting digits
    digit_str = "".join(re.findall(r"\d", s))
    if digit_str:
        try:
            return int(digit_str)
        except Exception:
            pass
    # fallback: try map any single word
    for p in parts:
        if p in _WORD_NUMBER_MAP:
            return _WORD_NUMBER_MAP[p]
    return None

def _extract_time_from_text(text: str):
    """
    Try to extract hour/minute and am/pm from a spoken/time-only string.
    Returns (hour, minute, tzoffset) where hour is 0-23 (aware), minute is 0-59.
    Return (None, None, None) if not found.
    Handles:
     - "6 PM", "6 pm", "06:30", "6:30 pm", "six PM", "six thirty pm"
     - "18:00", "18"
     - If only hour provided, minute=0
    """
    if not text:
        return None, None

    s = text.strip().lower()
    # normalize common separators
    s = s.replace(".", ":").replace("−", "-")
    # direct HH:MM or H:MM with optional offset
    m = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)?", s)
    if m:
        h = int(m.group(1))
        mm = int(m.group(2))
        ampm = m.group(3)
        if ampm:
            if ampm == "pm" and h != 12:
                h += 12
            if ampm == "am" and h == 12:
                h = 0
        return h, mm

    # plain hour with am/pm like "6 pm" or "six pm"
    m2 = re.search(r"([a-z0-9\s\-]+?)\s*(am|pm)\b", s)
    if m2:
        hour_part = m2.group(1).strip()
        ampm = m2.group(2)
        hnum = _words_to_number(hour_part)
        if hnum is None:
            try:
                hnum = int(re.search(r"\d+", hour_part).group())
            except Exception:
                hnum = None
        if hnum is not None:
            h = hnum % 24
            if ampm == "pm" and h != 12:
                h += 12
            if ampm == "am" and h == 12:
                h = 0
            return h, 0

    # "six thirty pm" -> words with minute
    # find two word numbers
    m3 = re.search(r"([a-z\s]+?)\s+(thirty|fifteen|fortyfive|forty five|ten|twenty|twenty five|twentyfive)\s*(am|pm)?", s)
    if m3:
        hword = m3.group(1).strip()
        mword = m3.group(2).replace(" ", "")
        ampm = m3.group(3)
        hnum = _words_to_number(hword)
        mnum = None
        if mword in ("thirty",):
            mnum = 30
        elif mword in ("fifteen",):
            mnum = 15
        elif mword in ("fortyfive", "forty five"):
            mnum = 45
        elif mword in ("ten",):
            mnum = 10
        elif mword in ("twenty",):
            mnum = 20
        elif mword in ("twentyfive", "twenty five"):
            mnum = 25
        if hnum is not None and mnum is not None:
            h = hnum
            if ampm:
                if ampm == "pm" and h != 12:
                    h += 12
                if ampm == "am" and h == 12:
                    h = 0
            return h, mnum

    # plain hour numeric like "18" or "6"
    m4 = re.search(r"\b(\d{1,2})\b", s)
    if m4:
        h = int(m4.group(1))
        if 0 <= h <= 24:
            if h == 24:
                h = 0
            return h, 0

    # words-only single hour like "six"
    hnum = _words_to_number(s)
    if hnum is not None and 0 <= hnum <= 24:
        return hnum, 0

    return None, None

# -------------------------------
# Google credential loader
# -------------------------------
def _ensure_creds(token_path="google/token.json"):
    if not os.path.exists(token_path):
        return None, f"Google token file not found at {token_path}. Run google_setup.py to create it."
    try:
        creds = Credentials.from_authorized_user_file(token_path)
        return creds, None
    except Exception as e:
        return None, f"Failed to load Google credentials: {e}"

# -------------------------------
# parse start_iso (improved)
# -------------------------------
def _parse_start_iso(start_iso):
    """
    Return (aware_datetime, error_message_or_None).
    REJECTS dates in the past.
    """
    if not start_iso:
        return None, "No start time provided."

    s = str(start_iso).strip()
    now_ist = datetime.now(IST)

    # 1) Try full ISO format first
    if re.match(r"\d{4}-\d{2}-\d{2}T", s):
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=IST)
            
            # VALIDATION: Reject if more than 1 hour in the past
            if dt < (now_ist - timedelta(hours=1)):
                return None, f"ERROR: The date '{dt.strftime('%Y-%m-%d %H:%M')}' is in the past. Current time is '{now_ist.strftime('%Y-%m-%d %H:%M')}'. Please provide today's date or a future date."
            
            return dt, None
        except Exception:
            pass  # fall through

    # 2) Handle relative dates (today, tomorrow, etc.)
    lower = s.lower()
    base_date = None
    if "today" in lower or lower.strip() == "today":
        base_date = now_ist.date()
        s = re.sub(r"\btoday\b", "", lower, flags=re.I).strip()
    elif "tomorrow" in lower or lower.strip() == "tomorrow":
        base_date = (now_ist + timedelta(days=1)).date()
        s = re.sub(r"\btomorrow\b", "", lower, flags=re.I).strip()
    elif "day after tomorrow" in lower or "dayafter" in lower:
        base_date = (now_ist + timedelta(days=2)).date()
        s = re.sub(r"day after tomorrow|dayafter|dayaftertomorrow", "", lower, flags=re.I).strip()

    # 3) Extract time
    h, m = _extract_time_from_text(s)
    if (base_date is not None) or (h is not None):
        if base_date is None:
            base_date = now_ist.date()
        if h is None:
            return None, f"Could not determine a time from '{start_iso}'."
        
        naive_dt = datetime(
            year=base_date.year,
            month=base_date.month,
            day=base_date.day,
            hour=h,
            minute=(m or 0),
            second=0
        )
        aware = naive_dt.replace(tzinfo=IST)
        
        # If time is in the past today, move to tomorrow
        if aware <= now_ist:
            aware = aware + timedelta(days=1)
        
        return aware, None

    # 4) Try plain ISO without tz
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST)
        
        # VALIDATION
        if dt < (now_ist - timedelta(hours=1)):
            return None, f"ERROR: The date '{dt.strftime('%Y-%m-%d %H:%M')}' is in the past. Please provide a current or future date."
        
        return dt, None
    except Exception:
        pass

    # 5) Date with time pattern
    m_date_time = re.search(r"(\d{4}-\d{2}-\d{2})[ T](\d{1,2}):?(\d{2})?", s)
    if m_date_time:
        ymd = m_date_time.group(1)
        hr = int(m_date_time.group(2))
        mn = int(m_date_time.group(3) or 0)
        try:
            dt = datetime.fromisoformat(f"{ymd}T{hr:02d}:{mn:02d}:00")
            dt = dt.replace(tzinfo=IST)
            
            # VALIDATION
            if dt < (now_ist - timedelta(hours=1)):
                return None, f"ERROR: The date '{dt.strftime('%Y-%m-%d %H:%M')}' is in the past. Please provide a current or future date."
            
            return dt, None
        except Exception:
            pass

    return None, f"Could not understand start time: '{start_iso}'. Try 'today at 6 PM' or '2025-12-05T18:00:00+05:30'."
# Main: create Google Calendar event
# -------------------------------
def book_google_calendar_event(summary, start_iso, duration_minutes=30, description=""):
    """
    Create a Google Calendar event and return a plain confirmation string.
    - summary: event title string
    - start_iso: ISO datetime string or spoken text (parser will attempt to convert)
    - duration_minutes: integer
    - description: optional string
    """
    creds, err = _ensure_creds("google/token.json")
    if err:
        return f"Error: {err}"

    try:
        service = build("calendar", "v3", credentials=creds)
    except Exception as e:
        return f"Error building Google Calendar service: {e}"

    start_dt, parse_err = _parse_start_iso(start_iso)
    if parse_err:
        return f"Error: {parse_err}"

    try:
        duration = int(duration_minutes)
    except Exception:
        duration = 30

    end_dt = start_dt + timedelta(minutes=duration)

    event_body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
    }

    try:
        created = service.events().insert(calendarId="primary", body=event_body).execute()
    except Exception as e:
        return f"Failed to create event: {e}"

    event_id = created.get("id", "unknown")
    event_start = created.get("start", {}).get("dateTime", start_dt.isoformat())
    html_link = created.get("htmlLink") or ""
    confirmation_text = (
        f"Booked '{summary}' on {event_start}. I've added it to your calendar. Reference: {event_id}."
    )
    if html_link:
        confirmation_text += f" Link: {html_link}"

    return confirmation_text

# -------------------------------
# END SESSION
# -------------------------------
def end_session():
    return "Thank you — your session is now closed. If you need anything else, feel free to ask."

# -------------------------------
# FUNCTION MAP
# -------------------------------
FUNCTION_MAP = {
    "book_google_calendar_event": book_google_calendar_event,
    "end_session": end_session,
}
