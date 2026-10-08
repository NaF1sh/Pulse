"""User-started focus and break sessions; elapsed time includes system suspend."""
import math
import time
from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot
from pulse.core.models import Kind, Notification


def elapsed_clock():
    return time.clock_gettime(time.CLOCK_BOOTTIME) if hasattr(time, 'CLOCK_BOOTTIME') else time.monotonic()


class Focus(QObject):
    changed = Signal()

    def __init__(self, parent=None, *, clock=elapsed_clock):
        super().__init__(parent)
        self.clock = clock
        self.phase = 'idle'
        self.paused = False
        self.remaining = 0
        self.duration = 0
        self.deadline = 0
        self.break_minutes = 5
        self.completed = 0
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.tick)

    @Property('QVariantMap', notify=changed)
    def state(self):
        return dict(phase=self.phase, paused=self.paused, remaining=self.remaining,
                    clock=f'{self.remaining // 60:02d}:{self.remaining % 60:02d}',
                    completed=self.completed, active=self.phase != 'idle')

    @property
    def card(self):
        if self.phase == 'idle':
            return None
        titles = {'focus': 'Time to focus', 'break': 'Take a breather',
                  'break_ready': 'Focus complete · take a break', 'done': 'Break complete · ready when you are'}
        text = 'Click to start your break' if self.phase == 'break_ready' else 'Click to begin another session' if self.phase == 'done' else ('Paused · ' if self.paused else '') + self.state['clock'] + ' remaining'
        return Notification(-3000001, 'Pulse Focus', titles[self.phase], text,
                            timeout=0, kind=Kind.PROGRESS,
                            value=1 - self.remaining / self.duration if self.duration else 1,
                            value_label=self.state['clock'], status='Focus')

    @Slot(int, int)
    def start(self, minutes=25, break_minutes=5):
        if self.phase not in ('idle', 'done') or not 1 <= minutes <= 180 or not 1 <= break_minutes <= 60:
            return
        self.break_minutes = break_minutes
        self.begin('focus', minutes)

    def begin(self, phase, minutes):
        self.phase = phase
        self.paused = False
        self.remaining = self.duration = minutes * 60
        self.deadline = self.clock() + self.duration
        self.timer.start()
        self.changed.emit()

    @Slot()
    def startBreak(self):
        if self.phase == 'break_ready':
            self.begin('break', self.break_minutes)

    @Slot()
    def togglePause(self):
        if self.phase not in ('focus', 'break'):
            return
        self.tick()
        if self.phase not in ('focus', 'break'):
            return
        self.paused = not self.paused
        if self.paused:
            self.timer.stop()
        else:
            self.deadline = self.clock() + self.remaining
            self.timer.start()
        self.changed.emit()

    @Slot()
    def stop(self):
        self.timer.stop()
        self.phase = 'idle'
        self.paused = False
        self.remaining = self.duration = 0
        self.changed.emit()

    def tick(self):
        if self.phase not in ('focus', 'break') or self.paused:
            return
        remaining = max(0, math.ceil(self.deadline - self.clock()))
        if remaining == self.remaining:
            return
        self.remaining = remaining
        if remaining == 0:
            self.timer.stop()
            if self.phase == 'focus':
                self.completed += 1
                self.phase = 'break_ready'
            else:
                self.phase = 'done'
        self.changed.emit()
