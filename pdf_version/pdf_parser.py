import json
import pdfplumber
import requests
from .storage import get_month_paths

# mapping Uzbek → English prayer names
PRAYER_MAP = {
    "тонг (саҳарлик)": "Fajr",
    "тонг": "Fajr",
    "саҳарлик": "Fajr",
    "қуёш": "Sunrise",
    "пешин": "Dhuhr",
    "аср": "Asr",
    "шом (ифтор)": "Maghrib",
    "шом": "Maghrib",
    "ифтор": "Maghrib",
    "хуфтон": "Isha",
}


def normalize_prayer_name(uz_name: str) -> str:
    """Normalize Uzbek prayer names from PDF."""
    key = uz_name.strip().lower()
    return PRAYER_MAP.get(key, uz_name)  # fallback: raw name


def find_column_index(header_row, possible_names):
    """
    Find column index by checking if any of the possible_names
    appears in the header cell (case-insensitive, partial match).
    """
    for idx, cell in enumerate(header_row):
        if not cell:
            continue
        cell_lower = cell.lower()
        for name in possible_names:
            if name in cell_lower:
                return idx
    raise ValueError(f"Could not find column with any of: {possible_names}")


def download_pdf(region_id: int, year: int, month: int, timeout: int = 30):
    """
    Download the prayer times PDF from islom.uz for given region + month.
    Returns the path to the downloaded PDF.
    Raises exceptions on failure.
    """
    # Example URL: https://islom.uz/prayertime/pdf/15/12
    url = f"https://islom.uz/prayertime/pdf/{region_id}/{month}"

    pdf_path, json_path = get_month_paths(year, month)

    print(f"[PDF Downloader] Fetching: {url}")
    print(f"[PDF Downloader] Saving to: {pdf_path}")

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Failed to download PDF: {e}")

    # Save file
    pdf_path.write_bytes(response.content)

    # Validate file is non-empty
    if pdf_path.stat().st_size < 500:
        # The website sometimes returns an HTML error page or empty file.
        raise RuntimeError(f"Downloaded PDF seems invalid (size too small): {pdf_path}")

    print("[PDF Downloader] Download successful.")
    return pdf_path


def parse_pdf_to_json(pdf_path):
    """
    Read table from the monthly prayer PDF and convert it
    into JSON-serializable structure:
    {
        "YYYY-MM-DD": {
            "Fajr": "05:55",
            "Sunrise": "07:19",
            ...
        },
        ...
    }
    """

    print(f"[PDF Parser] Opening PDF: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]  # The table is always on the first page
        table = page.extract_table()

    if not table:
        raise RuntimeError("Failed to extract table from PDF.")

    # The first few rows may contain headers or titles.
    # We locate the header row dynamically.
    header_row = None
    header_idx = None
    for idx, row in enumerate(table):
        clean = [c.strip().lower() if isinstance(c, str) else "" for c in row]
        if "кун" in clean:
            header_row = clean
            header_idx = idx
            break

    if header_row is None:
        raise RuntimeError("Could not identify header row in PDF table.")

    # Debug: print what we actually got
    print(f"[PDF Parser] Header row: {header_row}")

    # Use fuzzy matching for columns
    try:
        col_day = find_column_index(header_row, ["кун"])
        col_fajr = find_column_index(header_row, ["тонг", "саҳарлик"])
        col_sunrise = find_column_index(header_row, ["қуёш"])
        col_dhuhr = find_column_index(header_row, ["пешин"])
        col_asr = find_column_index(header_row, ["аср"])
        col_maghrib = find_column_index(header_row, ["шом", "ифтор"])
        col_isha = find_column_index(header_row, ["хуфтон"])
    except ValueError as e:
        print(f"[PDF Parser] Available columns: {header_row}")
        raise RuntimeError(f"Column mapping failed: {e}")

    # Build result
    month_data = {}
    pdf_name = pdf_path.stem  # "2025-12"
    year, month = pdf_name.split("-")
    y = int(year)
    m = int(month)

    # Start from the row after header
    for row in table[header_idx + 1 :]:
        if not row[col_day]:
            continue

        day_raw = str(row[col_day]).strip()
        if not day_raw.isdigit():
            continue

        day = int(day_raw)
        date = f"{y:04d}-{m:02d}-{day:02d}"

        month_data[date] = {
            "Fajr": str(row[col_fajr]).strip(),
            "Sunrise": str(row[col_sunrise]).strip(),
            "Dhuhr": str(row[col_dhuhr]).strip(),
            "Asr": str(row[col_asr]).strip(),
            "Maghrib": str(row[col_maghrib]).strip(),
            "Isha": str(row[col_isha]).strip(),
        }

    # Save JSON
    _, json_path = get_month_paths(y, m)
    json_path.write_text(json.dumps(month_data, indent=2, ensure_ascii=False))

    print(f"[PDF Parser] Parsed {len(month_data)} days")
    print(f"[PDF Parser] JSON saved to: {json_path}")
    return month_data
