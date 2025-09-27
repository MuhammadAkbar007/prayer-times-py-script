import datetime
import requests
import subprocess
import time

from gi.repository import Notify  # type: ignore
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_URL = "https://islomapi.uz/api/present/day?region=Namangan"
CACHE_FILE = Path.home() / ".cache/prayer-next.txt"

#   󱩸  󰖨      
# 🕌 🌞 ☀️ 🌤 🌛 🌙
PRAYER_NAMES = {
    "tong_saharlik": "Fajr",
    "quyosh": "Sunrise",
    "peshin": "Dhuhr",
    "asr": "Asr",
    "shom_iftor": "Maghrib",
    "hufton": "Isha",
}

session = requests.Session()
retries = Retry(
    total=5,  # up to 5 retries
    backoff_factor=2,  # wait 2s, 4s, 8s, ... between retries
    status_forcelist=[500, 502, 503, 504],  # retry on these HTTP codes
    allowed_methods=["GET"],  # only retry GET requests
)
session.mount("https://", HTTPAdapter(max_retries=retries))


def safe_write(text: str):
    """Always write something to cache file so tmux never shows blank."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(text)


def fetch_prayer_times():
    try:
        response = session.get(API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["times"]  # dict with today's prayer times
    except Exception as e:
        print(f"Error fetching prayer times: {e}")
        return None


def notify(title, message):
    # subprocess.run(
    #     ["notify-send", "--urgency=critical", "--expire-time=0", title, message]
    # )
    Notify.init("Prayer Times    ")
    notification = Notify.Notification.new(title, message)
    notification.set_urgency(2)  # critical
    notification.show()

    subprocess.run(
        [
            "paplay",
            "--volume=65536",  # this is max
            "/usr/share/sounds/freedesktop/stereo/prayer-notification.wav",  # message-new-instant or complete
        ]
    )


def get_next_prayer(prayer_times):
    now = datetime.datetime.now().strftime("%H:%M")
    for name, t in sorted(prayer_times.items(), key=lambda x: x[1]):
        if now < t:
            # return f"{name}: {t}"
            return f"{PRAYER_NAMES.get(name, name)}: {t}"
    # All prayers passed, show first prayer tomorrow
    first_name, first_time = sorted(prayer_times.items(), key=lambda x: x[1])[0]
    # return f"{first_name}: {first_time}"
    return f"{PRAYER_NAMES.get(first_name, first_name)}: {first_time}"


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
        write_next_prayer(prayer_times)
    else:
        print("Prayer times unavailable at startup.")
        safe_write("Loading... 🌀")

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
                write_next_prayer(prayer_times)
            else:
                print("Prayer times unavailable after midnight.")
                safe_write("Loading... 🌀")

        # Check prayers
        if prayer_times:
            for name, t in prayer_times.items():
                if now_str == t:
                    eng_name = PRAYER_NAMES.get(name, name)
                    notify("Prayer Reminder 🕌", f"It's time for {eng_name} prayer. 📿")
                    write_next_prayer(prayer_times)  # update after prayer

        # Update cache every loop
        write_next_prayer(prayer_times)

        time.sleep(60)


if __name__ == "__main__":
    # Ensure file exists at startup
    safe_write("Loading...")
    main()
