# todos ✅
 - [ ] offline mode: show the last month
 - [ ] cleanup of old pdf, json (, next_prayer, today_prayers)
 - [ ] notification customization

# Project Setup ⚙️

## Clone or copy the project directory manually
```bash
~/akbarDev/scripts/prayer-times-py-script
```

## Directory structure
```
prayer-times-py-script/
├── api-version/            # old project (optional)
├── pdf-version/            # new project (ALL logic here)
│   ├── notify_helper.py
│   ├── pdf_parser.py
│   ├── prayer_times_pdf.py
│   ├── scheduler.py        # main service entrypoint
│   ├── storage.py
│   └── README.md
└── assets/
    └── prayer-notification.wav
```

## Create the Python Virtual Environment
```bash
cd ~/akbarDev/scripts/prayer-times-py-script
python3.13 -m venv .venv
source .venv/bin/activate
```

## Upgrade pip
```bash
pip install --upgrade pip
```

## Install requirements
```bash
pip install -r requirements.txt
```

# Test the PDF system manually 🧪
## Step 1 — Download monthly PDF
```py
from pdf_version.pdf_parser import download_pdf
download_pdf(region_id=15, year=2025, month=12)
```

### This saves the PDF to
```
~/.local/share/prayer-times/2025-12.pdf
```

## Step 2 — Parse PDF to JSON
```py
from pdf_version.pdf_parser import parse_pdf_to_json
parse_pdf_to_json("/home/akbar/.local/share/prayer-times/2025-12.pdf")
```

### JSON will be written to
```
~/.local/share/prayer-times/2025-12.json
```

## Step 3 — Test scheduler helper
```py
from pdf_version.prayer_times_pdf import load_today_prayers
load_today_prayers()
```

## Step 4 — Test notification
```py
from pdf_version.notify_helper import notify
notify("Test Notification", "If you see this, notifications work.")
```

# Systemd User Service Setup 💻
## Create
```
~/.config/systemd/user/prayer-times-pdf.service
```

## Insert
```ini
[Unit]
Description=Prayer Times Scheduler (PDF-based)
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/akbar/akbarDev/scripts/prayer-times-py-script
ExecStart=/home/akbar/akbarDev/scripts/prayer-times-py-script/.venv/bin/python -m pdf_version.scheduler
Restart=always
RestartSec=20

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

## Reload systemd
```bash
systemctl --user daemon-reload

```

## Start service
```bash
systemctl --user start prayer-times-pdf.service
```

## Enable at login
```bash
systemctl --user enable prayer-times-pdf.service
```

## Check status
```bash
systemctl --user status prayer-times-pdf.service
```

## Check logs:
```bash
journalctl --user -u prayer-times-pdf.service -f
```

# Credits 💳
## Prayer timetable source: islom.uz
API -> `islom.uz/prayertime/pdf/15/12`
15 -> region `Namangan`
12 -> month `December`

# Author  ✍️
[Akbar Ahmad ibn Akrom](https://github.com/MuhammadAkbar007)

