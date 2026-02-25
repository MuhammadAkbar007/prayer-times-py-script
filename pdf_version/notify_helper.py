import subprocess
from pathlib import Path

DEFAULT_SOUND = (
    Path(__file__).resolve().parent.parent / "assets" / "prayer-notification.wav"
)

DEFAULT_ICON = Path(__file__).resolve().parent.parent / "assets" / "mosque.png"


def _play_sound(sound_path: Path | str | None, volume: float = 1.0):
    """
    Play sound using PipeWire (pw-play) with volume control.

    Args:
        sound_path: Path to audio file
        volume: Volume level 0.0 to 1.0 (default: 1.0 = 100%)
    """
    if not sound_path:
        return

    try:
        p = Path(sound_path)
        if not p.exists():
            print(f"[Notification] Sound file not found: {p}")
            return

        # PipeWire volume control via environment variable
        # PIPEWIRE_VOLUME: 0.0 (mute) to 1.0 (100%)
        env = {"PIPEWIRE_VOLUME": str(volume)}

        subprocess.run(
            ["pw-play", str(p)], check=False, env={**subprocess.os.environ, **env}
        )
    except Exception as e:
        print(f"[Notification] Failed to play sound: {e}")


def notify(
    title: str,
    message: str,
    sound: Path | str | None = None,
    volume: float = 1.0,
    urgency: str = "critical",
    icon: Path | str | None = None,
    app_name: str = "Prayer Times  ",
    expire_time: int = 0,
):
    """
    Show a desktop notification with sound.

    Args:
        title: Notification title
        message: Notification body
        sound: Path to sound file (None = use default)
        volume: Sound volume 0.0-1.0 (default: 1.0)
        urgency: 'low', 'normal', or 'critical' (default: 'critical')
        icon: Icon name or path (default: None = system default)
        app_name: Application name shown in notification
        expire_time: Milliseconds before auto-dismiss (0 = never)
    """
    try:
        cmd = [
            "notify-send",
            f"--app-name={app_name}",
            f"--urgency={urgency}",
            f"--expire-time={expire_time}",
        ]

        # Add icon if specified
        if icon:
            cmd.append(f"--icon={icon}")
        else:
            cmd.append(f"--icon={DEFAULT_ICON}")

        # Add title and message
        cmd.extend([title, message])

        subprocess.run(cmd, check=False)

    except Exception as e:
        print(f"[Notification] Failed to send notification: {e}")

    # Play sound (fire-and-forget)
    try:
        _play_sound(sound or DEFAULT_SOUND, volume=volume)
    except Exception as e:
        print(f"[Notification] Sound playback error: {e}")
