import subprocess
from pathlib import Path

DEFAULT_SOUND = (
    Path(__file__).resolve().parent.parent / "assets" / "prayer-notification.wav"
)


def _play_sound(sound_path: Path | str | None):
    if not sound_path:
        return
    try:
        p = Path(sound_path)
        if not p.exists():
            return

        # subprocess.run(["paplay", "--volume=65536", str(p)], check=False)
        subprocess.run(["pw-play", str(p)], check=False)
    except Exception:
        # never raise from notification subsystem
        return


def notify(title: str, message: str, sound: Path | str | None = None):
    """
    Show a desktop notification using libnotify and optionally play a sound.
    This function swallows exceptions so scheduler remains running in case of notify failure.
    """
    try:
        subprocess.run(
            ["notify-send", "--urgency=critical", title, message],
            check=False,
        )
    except Exception:
        pass

    # Play sound (fire-and-forget)
    try:
        _play_sound(sound or DEFAULT_SOUND)
    except Exception:
        pass
