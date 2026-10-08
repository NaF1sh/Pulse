from PySide6.QtCore import QCoreApplication

from pulse.core.models import Kind, Notification
from pulse.ui.controller import Controller


def test_controller_exposes_replacement_queue_and_dismissal():
    app = QCoreApplication.instance() or QCoreApplication([])
    controller = Controller()
    changes = []
    controller.changed.connect(lambda: changes.append(controller.title))
    controller.submit(Notification(1, "Chat", "First"))
    controller.submit(Notification(1, "Chat", "Updated"))
    controller.submit(Notification(2, "Mail", "Next"))
    assert controller.active
    assert controller.queued == 1
    controller.dismiss()
    assert controller.title == "Next"
    controller.dismiss()
    assert not controller.active
    assert changes == ["First", "Updated", "Updated", "Next", "Pulse"]
    controller.timer.stop()


def test_controller_exposes_progress_and_level_updates():
    app = QCoreApplication.instance() or QCoreApplication([])
    controller = Controller()
    controller.submit(Notification(1, "Downloads", "File", kind=Kind.PROGRESS, value=0.25))
    assert controller.card["kind"] == "progress"
    assert controller.card["value"] == 0.25
    controller.submit(Notification(1, "Audio", "Volume", kind=Kind.LEVEL, value=0.8))
    assert controller.card["id"] == 1
    assert controller.card["kind"] == "level"
    assert controller.card["value"] == 0.8
    assert controller.queued == 0
    controller.timer.stop()


def test_pet_reactions_ignore_replacements_queue_changes_and_suppressed_events():
    from pulse.core.rules import Rules
    app = QCoreApplication.instance() or QCoreApplication([])
    controller = Controller(rules=Rules(muted_apps=("Muted",)))
    moods = []
    controller.reaction.connect(moods.append)
    controller.submit(Notification(1, "Muted", "Hidden"))
    assert moods == []
    controller.submit(Notification(2, "Chat", "Hello"))
    controller.submit(Notification(2, "Chat", "Updated"))
    controller.submit(Notification(3, "Chat", "Queued"))
    controller.dismiss()
    assert moods == ["surprised"]
    controller.dismiss()
    assert moods == ["surprised", "happy"]
    controller.timer.stop()
