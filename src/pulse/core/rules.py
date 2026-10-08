"""Notification visibility rules, independent of desktop and UI APIs."""
from dataclasses import dataclass

from pulse.core.models import Priority


@dataclass(frozen=True)
class Rules:
    dnd: bool = False
    allow_critical: bool = True
    muted_apps: tuple[str, ...] = ()

    def allows(self, notification):
        if notification.app.casefold() in {name.casefold() for name in self.muted_apps}:
            return False
        return (not self.dnd or
                (self.allow_critical and notification.priority == Priority.HIGH))
