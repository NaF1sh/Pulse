"""Priority queue with an injectable monotonic clock and no UI dependencies."""
from time import monotonic

from pulse.core.rules import Rules


class Manager:
    def __init__(self, clock=monotonic, rules=None):
        self.clock = clock
        self.rules = rules or Rules()
        self.current = None
        self.pending = []
        self.deadline = None

    def _show(self, notification):
        self.current = notification
        self.deadline = (self.clock() + notification.timeout
                         if notification.timeout > 0 else None)

    def submit(self, notification):
        if not self.rules.allows(notification):
            self.close(notification.id)
            return
        if self.current and self.current.id == notification.id:
            self._show(notification)
            return
        for index, queued in enumerate(self.pending):
            if queued.id == notification.id:
                self.pending[index] = notification
                break
        else:
            self.pending.append(notification)
        self.pending.sort(key=lambda item: -item.priority)
        if self.current is None:
            self._show(self.pending.pop(0))
        elif self.pending[0].priority > self.current.priority:
            interrupted = self.current
            self._show(self.pending.pop(0))
            self.pending.insert(0, interrupted)
            self.pending.sort(key=lambda item: -item.priority)

    def dismiss(self):
        self.current = None
        self.deadline = None
        if self.pending:
            self._show(self.pending.pop(0))

    def tick(self):
        if self.deadline is not None and self.clock() >= self.deadline:
            self.dismiss()

    def close(self, notification_id):
        self.pending = [item for item in self.pending if item.id != notification_id]
        if self.current is not None and self.current.id == notification_id:
            self.dismiss()
