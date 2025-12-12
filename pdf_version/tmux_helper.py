from pathlib import Path

CACHE_DIR = Path.home() / ".cache"
NEXT_FILE = CACHE_DIR / "prayer-next.txt"
TODAY_FILE = CACHE_DIR / "prayer-today.txt"


def write_next_prayer(text: str):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # keep it short and single-line
    NEXT_FILE.write_text(text + "\n")


def write_full_day(text: str):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    TODAY_FILE.write_text(text + "\n")
