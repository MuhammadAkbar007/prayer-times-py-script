import subprocess
from gi.repository import Notify  # type: ignore

Notify.init("Prayer Times    ")
notification = Notify.Notification.new(
    "Test Notification 🧪", "If you see this, libnotify works 🎉"
)
notification.set_urgency(2)  # 0=low, 1=normal, 2=critical
notification.show()

subprocess.run(
    [
        "paplay",
        "--volume=65536",  # this is max
        "/usr/share/sounds/freedesktop/stereo/message-new-instant.oga",  # suspend-error message-new-instant or complete
    ]
)
