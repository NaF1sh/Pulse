from pulse.core.manager import Manager
from pulse.core.models import Notification, Priority
from pulse.core.rules import Rules


def test_dnd_drops_ordinary_cards_and_allows_critical():
    manager = Manager(rules=Rules(dnd=True))
    manager.submit(Notification(1, "Chat", "Ordinary"))
    assert manager.current is None
    assert manager.pending == []
    manager.submit(Notification(2, "Battery", "Critical", priority=Priority.HIGH))
    assert manager.current.id == 2


def test_strict_dnd_and_per_app_mute_also_block_critical():
    urgent = Notification(1, "Music", "Critical", priority=Priority.HIGH)
    assert not Rules(dnd=True, allow_critical=False).allows(urgent)
    assert not Rules(muted_apps=("mUsIc",)).allows(urgent)
    assert Rules(muted_apps=("Mus",)).allows(urgent)


def test_muted_replacement_removes_old_card_and_advances_queue():
    manager = Manager(rules=Rules(muted_apps=("Muted",)))
    manager.submit(Notification(1, "Chat", "First"))
    manager.submit(Notification(2, "Chat", "Next"))
    manager.submit(Notification(1, "Muted", "Updated"))
    assert manager.current.id == 2
    assert manager.pending == []
