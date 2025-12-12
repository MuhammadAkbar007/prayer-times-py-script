from pathlib import Path

BASE_DIR = Path.home() / ".local/share/prayer-times"
TMP_FILE = Path("/tmp/next_prayer")


def get_month_paths(year: int, month: int):
    """Return (pdf_path, json_path) for given year-month."""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{year:04d}-{month:02d}"
    pdf_path = BASE_DIR / f"{name}.pdf"
    json_path = BASE_DIR / f"{name}.json"
    return pdf_path, json_path
