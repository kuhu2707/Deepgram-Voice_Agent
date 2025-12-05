# utils_datetime.py

from datetime import timedelta, timezone
import dateparser

IST_OFFSET = timedelta(hours=5, minutes=30)
IST = timezone(IST_OFFSET)

def parse_spoken_datetime(text):
    """
    Convert spoken date/time like 'today at 6 PM' or 'tomorrow morning 10'
    into a correct ISO datetime in Asia/Kolkata timezone.
    Returns: (iso_string, None) OR (None, error_message)
    """

    if not text or not text.strip():
        return None, "No date/time provided."

    settings = {
        "RETURN_AS_TIMEZONE_AWARE": True,
        "TO_TIMEZONE": "Asia/Kolkata",
        "TIMEZONE": "Asia/Kolkata",
        "PREFER_DATES_FROM": "future",
    }

    dt = dateparser.parse(text, settings=settings)

    if not dt:
        return None, f"Could not understand date/time: '{text}'"

    return dt.isoformat(), None
