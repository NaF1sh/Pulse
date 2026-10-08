from PySide6.QtCore import QCoreApplication
from pulse.ui.focus import Focus
from pulse.ui.controller import Controller
from pulse.core.models import Notification, Kind

_APP = QCoreApplication.instance() or QCoreApplication([])


def test_focus_pause_break_and_delayed_tick():
    now = [0]
    focus = Focus(clock=lambda: now[0])
    focus.start(1, 1)
    now[0] = 20
    focus.tick()
    assert focus.state['clock'] == '00:40'
    focus.togglePause()
    now[0] = 200
    focus.tick()
    assert focus.remaining == 40
    focus.togglePause()
    now[0] = 241
    focus.tick()
    assert focus.phase == 'break_ready'
    assert focus.completed == 1
    focus.tick()
    assert focus.completed == 1
    focus.startBreak()
    assert focus.phase == 'break'
    now[0] = 1000  # waking from suspend completes a break exactly once
    focus.tick()
    assert focus.phase == 'done'
    assert focus.card.value == 1
    focus.stop()
    assert focus.card is None


def test_focus_rejects_invalid_or_accidental_restart():
    focus = Focus(clock=lambda: 0)
    focus.start(0, 5)
    focus.start(181, 5)
    focus.start(25, 61)
    assert focus.phase == 'idle'
    focus.start(25, 5)
    focus.start(1, 1)
    assert focus.remaining == 1500
    focus.stop()


def test_notification_then_focus_then_music_priority():
    controller = Controller()
    controller.timer.stop()
    controller.set_media(Notification(2, 'Music', 'Song', kind=Kind.MEDIA))
    controller.focus.start(25, 5)
    assert controller.card['status'] == 'Focus'
    controller.submit(Notification(1, 'Chat', 'Message'))
    assert controller.card['title'] == 'Message'
    controller.dismiss()
    assert controller.card['status'] == 'Focus'
    controller.focus.stop()
    assert controller.card['title'] == 'Song'
