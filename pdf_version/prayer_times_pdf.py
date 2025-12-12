import json
from datetime import datetime, date, timedelta
from .storage import get_month_paths

PRAYER_ORDER = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]


def load_month_data(year: int, month: int):
    """Load JSON data for the given year and month."""
    pdf_path, json_path = get_month_paths(year, month)

    if not json_path.exists():
        return None  # Scheduler will know to download/parse

    try:
        return json.loads(json_path.read_text())
    except Exception:
        return None


def get_today_schedule():
    """
    Returns today's schedule as a dict:
    {
      'Fajr': '05:55',
      'Sunrise': '07:19',
      ...
    }
    If no data exists, returns None.
    """
    today = date.today()
    data = load_month_data(today.year, today.month)
    if not data:
        return None

    key = today.strftime("%Y-%m-%d")
    return data.get(key)


def time_str_to_minutes(t: str) -> int:
    """Convert 'HH:MM' → minutes since midnight."""
    h, m = map(int, t.split(":"))
    return h * 60 + m


def get_next_prayer(schedule: dict):
    """
    Given today's schedule dict, return:
    ('Fajr', '05:55')
    or the next prayer after current time.
    """
    now = datetime.now()
    now_m = now.hour * 60 + now.minute

    for name in PRAYER_ORDER:
        t = schedule[name]
        t_m = time_str_to_minutes(t)
        if t_m > now_m:
            return name, t

    # If all times passed → next day's Fajr (tomorrow)
    tomorrow = date.today() + timedelta(days=1)
    data = load_month_data(tomorrow.year, tomorrow.month)

    if not data:
        return None  # No info for next month yet

    first_key = tomorrow.strftime("%Y-%m-%d")
    next_schedule = data.get(first_key)

    if not next_schedule:
        return None

    return "Fajr", next_schedule["Fajr"]
