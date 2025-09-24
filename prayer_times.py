import requests
import datetime
import subprocess
import time
from pathlib import Path

API_URL = "https://islomapi.uz/api/present/day?region=Namangan"
CACHE_FILE = Path.home() / ".cache/prayer-next.txt"

PRAYER_ICONS = {
    "tong_saharlik": "🕌 Fajr",
    "quyosh": "🌞 Sunrise",
    "peshin": "☀️Dhuhr",
    "asr": "🌤 Asr",
    "shom_iftor": "🌛 Maghrib",
    "hufton": "🌙 Isha",
}


def safe_write(text: str):
    """Always write something to cache file so tmux never shows blank."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(text)


def fetch_prayer_times():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["times"]  # dict with today's prayer times
    except Exception as e:
        print(f"Error fetching prayer times: {e}")
        safe_write("Loading...")
        return None


def notify(title, message):
    subprocess.run(["notify-send", title, message])
    subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"])


def get_next_prayer(prayer_times):
    now = datetime.datetime.now().strftime("%H:%M")
    for name, t in sorted(prayer_times.items(), key=lambda x: x[1]):
        if now < t:
            # return f"{name}: {t}"
            return f"{PRAYER_ICONS.get(name, name)}: {t}"
    # All prayers passed, show first prayer tomorrow
    first_name, first_time = sorted(prayer_times.items(), key=lambda x: x[1])[0]
    # return f"{first_name}: {first_time}"
    return f"{PRAYER_ICONS.get(first_name, first_name)}: {first_time}"


def write_next_prayer(prayer_times):
    if not prayer_times:
        safe_write("Loading...")
        return
    next_prayer = get_next_prayer(prayer_times)
    safe_write(next_prayer)


def main():
    current_day = datetime.date.today()
    prayer_times = fetch_prayer_times()

    if prayer_times:
        print(f"Prayer times for {current_day}:")
        for name, t in prayer_times.items():
            print(f"{name}: {t}")
    else:
        print("Prayer times unavailable at startup.")

    # Initial write
    write_next_prayer(prayer_times)

    while True:
        now = datetime.datetime.now()
        now_str = now.strftime("%H:%M")

        # Refresh daily
        if now.date() != current_day:
            current_day = now.date()
            prayer_times = fetch_prayer_times()
            if prayer_times:
                print(f"\nUpdated prayer times for {current_day}:")
                for name, t in prayer_times.items():
                    print(f"{name}: {t}")
            else:
                print("Prayer times unavailable after midnight.")
            write_next_prayer(prayer_times)

        # Check prayers
        if prayer_times:
            for name, t in prayer_times.items():
                if now_str == t:
                    notify("Prayer Reminder", f"It's time for {name} prayer.")
                    write_next_prayer(prayer_times)  # update after prayer

        # Update cache every loop
        write_next_prayer(prayer_times)

        time.sleep(60)


if __name__ == "__main__":
    # Ensure file exists at startup
    safe_write("Loading...")
    main()
