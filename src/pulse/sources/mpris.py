"""Discover MPRIS players and sample track/playback changes without UI blocking."""
import json
import shutil

from PySide6.QtCore import QObject, QTimer, Signal

from pulse.core.models import Kind, Notification
from pulse.sources.command import Command
from pulse.sources.artwork import artwork_url
from pulse.sources.dbus_observer import clean_text

PLAYER = "org.mpris.MediaPlayer2.Player"


def unvariant(value):
    return value.get("data") if isinstance(value, dict) else None


def parse_player(output, service):
    payload = json.loads(output)
    if not isinstance(payload, dict) or payload.get("type") != "a{sv}":
        raise ValueError("Unexpected MPRIS property signature")
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise ValueError("Invalid MPRIS property payload")
    properties = data[0]
    status = unvariant(properties.get("PlaybackStatus"))
    metadata = unvariant(properties.get("Metadata"))
    if status not in ("Playing", "Paused", "Stopped") or not isinstance(metadata, dict):
        return None
    title = clean_text(unvariant(metadata.get("xesam:title")), 160)
    artists = unvariant(metadata.get("xesam:artist"))
    artist = ", ".join(clean_text(item, 80) for item in artists[:5]) if isinstance(artists, list) else ""
    if not title or status == "Stopped":
        return None
    track = unvariant(metadata.get("mpris:trackid"))
    artwork = artwork_url(unvariant(metadata.get("mpris:artUrl")),
                          unvariant(metadata.get("xesam:url")))
    return dict(service=service, title=title, artist=artist, status=status,
                track=track if isinstance(track, str) else title, artwork=artwork,
                capabilities={key: unvariant(properties.get(key)) is True for key in
                              ('CanControl', 'CanPlay', 'CanPause', 'CanGoNext', 'CanGoPrevious')})


class Mpris(QObject):
    controlsChanged = Signal()
    notification = Signal(object)
    cleared = Signal()
    status = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected = None
        self.control_error = ''
        self.action = Command(self)
        self.action.completed.connect(self.control_finished)
        self.discovery = Command(self)
        self.query = Command(self)
        self.discovery.completed.connect(self.discovered)
        self.query.completed.connect(self.received)
        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.poll)
        self.players = []
        self.remaining = []
        self.samples = []
        self.querying = None
        self.previous = None
        self.executable = None
        self.error_reported = False
        self.stopping = False

    def start(self):
        self.executable = shutil.which("busctl")
        if not self.executable:
            self.status.emit("Music source unavailable: busctl is not installed.")
            return
        self.timer.start()
        self.poll()

    def poll(self):
        if self.querying is not None or self.discovery.busy:
            return
        self.discovery.start(self.executable, ["--user", "--json=short", "--timeout=1",
            "call", "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "ListNames"])

    def discovered(self, code, output, error):
        try:
            payload = json.loads(output) if code == 0 else {}
            data = payload.get("data", [])
            names = data[0] if payload.get("type") == "as" and isinstance(data, list) and data else []
            if code != 0 or payload.get("type") != "as" or not isinstance(names, list):
                raise ValueError("Cannot discover MPRIS players; check your session bus.")
            self.players = sorted(name for name in names if isinstance(name, str) and name.startswith("org.mpris.MediaPlayer2."))[:8]
        except (ValueError, TypeError, AttributeError):
            if not self.error_reported:
                self.status.emit("Music source unavailable: cannot read the session bus.")
            self.error_reported = True
            self.previous = None
            self.selected = None
            self.controlsChanged.emit()
            self.cleared.emit()
            self.timer.setInterval(5000)
            return
        if self.error_reported:
            self.status.emit("Music source reconnected.")
        self.error_reported = False
        self.timer.setInterval(2000)
        self.remaining = list(self.players)
        self.samples = []
        self.next_player()

    def next_player(self):
        if self.stopping:
            return
        if not self.remaining:
            self.querying = None
            self.publish()
            return
        self.querying = self.remaining.pop(0)
        self.query.start(self.executable, ["--user", "--json=short", "--timeout=1", "call",
            self.querying, "/org/mpris/MediaPlayer2", "org.freedesktop.DBus.Properties", "GetAll", "s", PLAYER])

    def received(self, code, output, error):
        if code == 0:
            try:
                sample = parse_player(output, self.querying)
                if sample:
                    self.samples.append(sample)
            except (ValueError, TypeError, AttributeError):
                pass
        self.next_player()

    def publish(self):
        playing = [sample for sample in self.samples if sample["status"] == "Playing"]
        candidates = playing or self.samples
        if not candidates:
            self.previous = None
            self.selected = None
            self.controlsChanged.emit()
            self.cleared.emit()
            return
        previous_service = self.previous[0] if self.previous else None
        selected = next((item for item in candidates if item["service"] == previous_service),
                        next((item for item in candidates if item["artwork"]), candidates[0]))
        # KDE's browser integration may expose richer metadata for the same tab.
        # Keep the current track, but prefer its duplicate with actual cover art.
        if not selected["artwork"]:
            selected = next((item for item in candidates if item["artwork"]
                             and item["title"].casefold() == selected["title"].casefold()), selected)
        if self.selected != selected:
            self.selected = selected
            self.control_error = ''
            self.controlsChanged.emit()
        signature = tuple(selected[key] for key in ("service", "track", "title", "artist", "status", "artwork"))
        if signature == self.previous:
            return
        self.previous = signature
        self.notification.emit(Notification(
            -2000001, "Music", selected["title"], selected["artist"] or "Media player",
            timeout=0, kind=Kind.MEDIA, status=selected["status"], artwork=selected["artwork"]))

    def stop(self):
        self.stopping = True
        self.timer.stop()
        self.discovery.stop()
        self.query.stop()
        self.action.stop()

    @property
    def controls(self):
        sample = self.selected or {}
        caps = sample.get('capabilities', {})
        control = caps.get('CanControl', False)
        return dict(available=bool(self.selected), busy=self.action.busy, error=self.control_error,
                    previous=control and caps.get('CanGoPrevious', False),
                    next=control and caps.get('CanGoNext', False),
                    toggle=control and caps.get('CanPause' if sample.get('status') == 'Playing' else 'CanPlay', False))

    def control(self, action):
        if action not in ('previous', 'toggle', 'next') or not self.controls.get(action) or self.action.busy or not self.executable:
            return
        method = {'previous': 'Previous', 'next': 'Next',
                  'toggle': 'Pause' if self.selected['status'] == 'Playing' else 'Play'}[action]
        self.control_error = ''
        self.action.start(self.executable, ['--user', '--timeout=1', 'call', self.selected['service'],
                                          '/org/mpris/MediaPlayer2', PLAYER, method])
        self.controlsChanged.emit()

    def control_finished(self, code, output, error):
        self.control_error = '' if code == 0 else 'The player did not respond. Try again.'
        self.controlsChanged.emit()
        if not self.stopping:
            self.poll()
