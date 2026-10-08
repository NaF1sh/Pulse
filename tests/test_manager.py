from pulse.core.manager import Manager
from pulse.core.models import Notification, Priority


def test_priority_preempts_and_equal_priority_keeps_order():
    manager = Manager()
    first = Notification(1, "Chat", "First")
    second = Notification(2, "Chat", "Second")
    urgent = Notification(3, "Battery", "Low", priority=Priority.HIGH)
    manager.submit(first)
    manager.submit(second)
    manager.submit(urgent)
    assert manager.current == urgent
    manager.dismiss()
    assert manager.current == first
    manager.dismiss()
    assert manager.current == second


def test_active_and_queued_replacements_do_not_duplicate():
    manager = Manager()
    manager.submit(Notification(1, "Download", "Starting"))
    manager.submit(Notification(2, "Chat", "Old"))
    manager.submit(Notification(1, "Download", "Finished"))
    manager.submit(Notification(2, "Chat", "Updated"))
    assert manager.current.title == "Finished"
    assert len(manager.pending) == 1
    manager.dismiss()
    assert manager.current.title == "Updated"


def test_timeout_and_persistent_notifications_with_fake_clock():
    now = [0.0]
    manager = Manager(clock=lambda: now[0])
    manager.submit(Notification(1, "Chat", "Timed", timeout=2))
    manager.submit(Notification(2, "Chat", "Persistent", timeout=0))
    now[0] = 1.99
    manager.tick()
    assert manager.current.id == 1
    now[0] = 2
    manager.tick()
    assert manager.current.id == 2
    now[0] = 100
    manager.tick()
    assert manager.current.id == 2


def test_replacement_refreshes_timeout():
    now = [0.0]
    manager = Manager(clock=lambda: now[0])
    manager.submit(Notification(1, "Chat", "First", timeout=2))
    now[0] = 1
    manager.submit(Notification(1, "Chat", "Updated", timeout=2))
    now[0] = 2
    manager.tick()
    assert manager.current.title == "Updated"
    now[0] = 3
    manager.tick()
    assert manager.current is None


def test_external_close_removes_queued_and_active_cards():
    manager = Manager()
    for id in (1, 2, 3):
        manager.submit(Notification(id, "Chat", str(id)))
    manager.close(2)
    manager.close(99)
    assert [item.id for item in manager.pending] == [3]
    manager.close(1)
    assert manager.current.id == 3
