from PySide6.QtCore import QCoreApplication

from pulse.core.manager import Manager
from pulse.core.models import Kind, Notification
from pulse.core.rules import Rules
from pulse.ui.controller import Controller


def track(title="Song"):
    return Notification(-2000001, "Music", title, "Artist", timeout=0, kind=Kind.MEDIA, status="Playing")


def test_music_remains_visible_without_occupying_notification_queue():
    app = QCoreApplication.instance() or QCoreApplication([])
    controller = Controller()
    controller.set_media(track())
    assert controller.active
    assert controller.title == "Song"
    assert controller.manager.current is None
    assert controller.queued == 0
    controller.tick()
    controller.manager.clock = lambda: 100000
    controller.tick()
    controller.dismiss()
    assert controller.title == "Song"
    controller.timer.stop()


def test_notifications_interrupt_music_and_return_to_latest_track_after_timeout():
    app = QCoreApplication.instance() or QCoreApplication([])
    now = [0.0]
    controller = Controller()
    controller.manager = Manager(clock=lambda: now[0])
    controller.set_media(track("First"))
    controller.submit(Notification(1, "Chat", "Message", timeout=2))
    assert controller.title == "Message"
    controller.set_media(track("Latest"))
    assert controller.title == "Message"
    now[0] = 2
    controller.tick()
    assert controller.title == "Latest"
    assert controller.card["kind"] == "media"
    controller.timer.stop()


def test_stopping_music_during_notification_returns_to_pet_after_dismissal():
    app = QCoreApplication.instance() or QCoreApplication([])
    controller = Controller()
    controller.set_media(track())
    controller.submit(Notification(1, "Chat", "Message"))
    controller.clear_media()
    assert controller.title == "Message"
    controller.dismiss()
    assert not controller.active
    controller.timer.stop()


def test_music_obeys_dnd_and_muting():
    app = QCoreApplication.instance() or QCoreApplication([])
    for rules in (Rules(dnd=True), Rules(muted_apps=("music",))):
        controller = Controller(rules=rules)
        controller.set_media(track())
        assert not controller.active
        controller.timer.stop()


def test_hiding_music_retains_latest_track_and_keeps_notifications_working():
    app = QCoreApplication.instance() or QCoreApplication([])
    controller = Controller()
    controller.set_media(track("First"))
    controller.toggle_music()
    assert not controller.musicVisible
    assert not controller.active
    controller.set_media(track("Latest"))
    assert not controller.active
    controller.submit(Notification(1, "Chat", "Message"))
    assert controller.title == "Message"
    controller.dismiss()
    assert not controller.active
    controller.toggle_music()
    assert controller.musicVisible
    assert controller.title == "Latest"
    controller.timer.stop()


def test_clearing_hidden_music_does_not_restore_a_stale_track():
    app = QCoreApplication.instance() or QCoreApplication([])
    controller = Controller()
    controller.set_media(track())
    controller.toggle_music()
    controller.clear_media()
    controller.toggle_music()
    assert not controller.active
    controller.timer.stop()
