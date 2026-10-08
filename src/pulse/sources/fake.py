from pulse.core.models import Kind, Notification, Priority


def script():
    """Offsets in seconds; repeated IDs exercise replacement in place."""
    return [
        (0, Notification(1, "Messages", "Alex", "Are you free for a quick call?", timeout=1.5)),
        (1, Notification(2, "Downloads", "Downloading project.zip", "Preparing", timeout=6, kind=Kind.PROGRESS, value=0.1)),
        (2, Notification(3, "Battery", "Battery low", "Connect your charger · 10% remaining", Priority.HIGH, 3)),
        (7, Notification(2, "Downloads", "Downloading project.zip", "Almost there", timeout=4, kind=Kind.PROGRESS, value=0.75)),
        (9, Notification(2, "Downloads", "Download complete", "project.zip · ready to open", timeout=2, kind=Kind.PROGRESS, value=1)),
        (12, Notification(4, "Music", "Midnight City", "M83 · Hurry Up, We're Dreaming", timeout=4, kind=Kind.MEDIA, value=0.42, status="Demo")),
        (17, Notification(5, "Audio", "Volume", "Speakers", timeout=3, kind=Kind.LEVEL, value=0.65)),
        (18, Notification(5, "Audio", "Volume", "Speakers", timeout=3, kind=Kind.LEVEL, value=0.8)),
    ]
