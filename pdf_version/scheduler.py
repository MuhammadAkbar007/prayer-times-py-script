import time
import traceback
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from .notify_helper import notify
from .pdf_parser import download_pdf, parse_pdf_to_json
from .storage import get_month_paths
from . import tmux_helper

REGION_ID = 15  # Namangan (change if needed)
CHECK_INTERVAL_SECONDS = 60  # main loop tick
DOWNLOAD_RETRY_HOURS = 6  # if download fails, retry after this many hours
MIN_PDF_SIZE_BYTES = 500

DEFAULT_ICON = Path(__file__).resolve().parent.parent / "assets" / "mosque.png"

_notified_for_today = set()  # set of prayer names already notified for current date


def ensure_month_data(year: int, month: int) -> bool:
    """
    Ensure that JSON for the requested month exists.
    Returns True if JSON available (exists after possible download+parse).
    If download/parse fails, returns False.
    """
    pdf_path, json_path = get_month_paths(year, month)

    # If json already exists and non-empty -> OK
    if json_path.exists() and json_path.stat().st_size > 0:
        return True

    # Try to download the PDF (if missing) and parse it
    try:
        if not pdf_path.exists() or pdf_path.stat().st_size < MIN_PDF_SIZE_BYTES:
            print(f"[scheduler] downloading PDF for {year}-{month:02d}...")
            download_pdf(REGION_ID, year, month)
        print(f"[scheduler] parsing PDF -> JSON for {year}-{month:02d} ...")
        parse_pdf_to_json(pdf_path)
        # parse_pdf_to_json writes the JSON file itself
        return True
    except Exception as e:
        print(f"[scheduler] ensure_month_data failed: {e}", file=sys.stderr)
        traceback.print_exc()
        return False


def load_month_data(year: int, month: int):
    _, json_path = get_month_paths(year, month)
    if not json_path.exists():
        return None
    try:
        return json.loads(json_path.read_text())
    except Exception:
        return None


def get_schedule_for_date(dt: date):
    d = dt
    data = load_month_data(d.year, d.month)
    if not data:
        return None
    key = d.strftime("%Y-%m-%d")
    return data.get(key)


def format_full_day(schedule: dict, is_stale: bool = False) -> str:
    """Return a multi-line string of today's schedule"""
    lines = []
    if is_stale:
        lines.append("⚠️  Using old data (offline)")
        lines.append("")
    for k in ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]:
        v = schedule.get(k, "-")
        lines.append(f"{k}: {v}")
    return "\n".join(lines)


def get_next_prayer_from_schedule(schedule: dict):
    """Return (name, time_str) or None if schedule is None."""
    if not schedule:
        return None
    now = datetime.now()
    now_minutes = now.hour * 60 + now.minute
    for name in ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]:
        t = schedule.get(name)
        if not t:
            continue
        hh, mm = map(int, t.split(":"))
        t_minutes = hh * 60 + mm
        if t_minutes > now_minutes:
            return name, t
    # all passed → try tomorrow's Fajr
    tomorrow = date.today() + timedelta(days=1)
    sched_tom = get_schedule_for_date(tomorrow)
    if sched_tom and "Fajr" in sched_tom:
        return "Fajr", sched_tom["Fajr"]
    return None


def write_status(
    schedule_today, offline=False, using_stale_data=False, stale_date=None
):
    """Write the short one-line status and full-day file for tmux popup."""
    if schedule_today:
        name_time = get_next_prayer_from_schedule(schedule_today)
        if name_time:
            name, t = name_time
            if using_stale_data and stale_date:
                # Show indicator for stale data with date
                short = f"● {name} {t} ({stale_date.strftime('%b %d')}) 󰥔 "
            elif using_stale_data:
                short = f"● {name} {t} 󰥔 "
            else:
                short = f"{name} {t} 󰥔 "
        else:
            short = "No upcoming (all passed)"
        full = format_full_day(schedule_today, is_stale=using_stale_data)
    else:
        if offline:
            short = "● Offline: no data"
            full = "No prayer schedule available (offline)."
        else:
            short = "Loading...🌀"
            full = "No prayer schedule available yet."
    tmux_helper.write_next_prayer(short)
    tmux_helper.write_full_day(full)


def send_notification_if_needed(schedule_today):
    """
    Check whether any prayer is exactly now. If so and not already notified, notify.
    Must be called once per loop (or minute).
    """
    global _notified_for_today
    if not schedule_today:
        return

    now_str = datetime.now().strftime("%H:%M")
    today_key = date.today().isoformat()

    # If date changed we should have reset notifications elsewhere.
    for name, t in schedule_today.items():
        # skip non-prayer keys (if any), expect HH:MM strings
        if not isinstance(t, str) or ":" not in t:
            continue
        if t == now_str:
            key = f"{today_key}|{name}"
            if key not in _notified_for_today:
                # send notification
                title = f"    Prayer Reminder for {name}"
                message = f"It's time for {name} prayer ( {t} )"
                notify(title, message, icon=DEFAULT_ICON)
                _notified_for_today.add(key)
                # after notifying, update next-prayer text
                write_status(schedule_today)
                print(f"[scheduler] Notified for {name} at {t}")


def clear_notifications_for_new_day():
    global _notified_for_today
    _notified_for_today = set()


def cleanup_old_month_files(current_year, current_month):
    """
    Remove previous month files (PDF + JSON) to avoid accumulating storage.
    Keep only current month files.
    **ONLY call this after successfully downloading current month data**
    """
    base_pdf, base_json = get_month_paths(current_year, current_month)
    # iterate files in dir and delete any that are not the current month pair
    storage_dir = base_pdf.parent
    deleted_count = 0
    for f in storage_dir.iterdir():
        try:
            if f == base_pdf or f == base_json:
                continue
            # only remove pdf or json files with YYYY-MM prefix
            if f.suffix in (".pdf", ".json"):
                # optional safety: only delete if name matches pattern YYYY-MM.*
                name = f.stem  # e.g. "2025-12"
                if len(name) >= 7 and name[4] == "-":
                    f.unlink(missing_ok=True)
                    deleted_count += 1
        except Exception:
            pass
    if deleted_count > 0:
        print(f"[scheduler] Cleaned up {deleted_count} old files")


def find_most_recent_available_data():
    """
    Find the most recent month with available JSON data.
    Returns (year, month, date_obj) or None.
    Checks current month, then goes backwards up to 3 months.
    """
    today = date.today()
    for i in range(4):  # Check current + 3 previous months
        check_date = today - timedelta(days=i * 30)
        data = load_month_data(check_date.year, check_date.month)
        if data:
            # Find the most recent date in this data
            dates = sorted(data.keys())
            if dates:
                last_date_str = dates[-1]
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
                return check_date.year, check_date.month, last_date
    return None


def main_loop():
    """
    Main scheduler loop. Run forever.
    """
    print("[scheduler] Starting scheduler loop.")
    last_checked_date = date.today()
    last_download_attempt = None  # datetime of last failed attempt

    while True:
        try:
            today = date.today()
            year, month = today.year, today.month

            # If month JSON is missing try to ensure it.
            ok = ensure_month_data(year, month)

            if ok:
                # Successfully have current month data
                schedule_today = get_schedule_for_date(today)

                if schedule_today is None:
                    # Current month JSON exists but today's entry is missing (very rare)
                    # This could happen if PDF was corrupted or parsing failed for specific dates
                    print(
                        f"[scheduler] Warning: Current month data exists but no entry for {today}"
                    )
                    write_status(None, offline=True)
                else:
                    # Normal case: we have current data
                    write_status(schedule_today, offline=False, using_stale_data=False)

                # Only cleanup old files AFTER successfully getting new data
                cleanup_old_month_files(year, month)

            else:
                # Failed to get current month data - try to use stale data
                print("[scheduler] Could not get current month data, using fallback...")

                # Try to find the most recent available data
                fallback = find_most_recent_available_data()

                if fallback:
                    fb_year, fb_month, fb_date = fallback
                    print(f"[scheduler] Using data from {fb_year}-{fb_month:02d}")

                    # Try to get today's data from old month (might work if it's early in new month)
                    schedule_today = get_schedule_for_date(today)

                    if schedule_today is None:
                        # Use the last available date from the old month
                        schedule_today = get_schedule_for_date(fb_date)
                        stale_date = fb_date
                    else:
                        # Today's date exists in old month (early in new month case)
                        stale_date = today

                    write_status(
                        schedule_today,
                        offline=True,
                        using_stale_data=True,
                        stale_date=stale_date,
                    )
                else:
                    # No data at all
                    schedule_today = None
                    write_status(None, offline=True)

                # Retry policy: attempt redownload every DOWNLOAD_RETRY_HOURS
                if (
                    last_download_attempt is None
                    or (datetime.now() - last_download_attempt).total_seconds()
                    > DOWNLOAD_RETRY_HOURS * 3600
                ):
                    print("[scheduler] Attempting to re-download current month data...")
                    last_download_attempt = datetime.now()
                    ok2 = ensure_month_data(year, month)
                    if ok2:
                        # fresh data arrived → reload
                        schedule_today = get_schedule_for_date(today)
                        cleanup_old_month_files(year, month)
                        clear_notifications_for_new_day()
                        write_status(
                            schedule_today, offline=False, using_stale_data=False
                        )

            # If day changed since last loop, reset notified set
            if today != last_checked_date:
                last_checked_date = today
                clear_notifications_for_new_day()

            # Send notifications if any prayer matches current minute
            # (even with stale data, times might still be useful)
            send_notification_if_needed(schedule_today)

            # Sleep until next tick
            time.sleep(CHECK_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("[scheduler] Interrupted by user, exiting.")
            raise
        except Exception as e:
            print(f"[scheduler] Unexpected error: {e}", file=sys.stderr)
            traceback.print_exc()
            # Sleep a bit on error to avoid tight crash loops
            time.sleep(30)


if __name__ == "__main__":
    main_loop()
