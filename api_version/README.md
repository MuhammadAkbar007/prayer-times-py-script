# Prayer Times

Fetches prayer times from islom.uz API.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## systemd service file
path is `~/.config/systemd/user/prayer-times.service`

```bash
[Unit]
Description=Prayer Times Reminder (Namangan)
After=network-online.target

[Service]
ExecStart=/home/akbar/akbarDev/pet-projects/prayer-times-py-script/.venv/bin/python /home/akbar/akbarDev/pet-projects/prayer-times-py-script/prayer_times.py
Restart=always
RestartSec=10

# Make logs visible via `journalctl --user-unit=prayer-times.service`
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```
