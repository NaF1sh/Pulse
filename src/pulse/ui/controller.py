from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot
import sqlite3

from pulse.core.manager import Manager


class Controller(QObject):
    changed = Signal()
    musicVisibilityChanged = Signal()
    historyFailed = Signal(str)
    reaction = Signal(str)

    def __init__(self, parent=None, *, rules=None, history=None):
        super().__init__(parent)
        self.manager = Manager(rules=rules)
        self.history = history
        self.interactions = None
        from pulse.ui.notification_icons import NotificationIcons
        self.icons = NotificationIcons()
        self._action_error = ""
        self.media = None
        self._music_visible = True
        self.volume_visible = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(50)

    @Property(bool, notify=changed)
    def active(self):
        return self.item is not None

    @property
    def item(self):
        return self.manager.current or (self.media if self._music_visible else None)

    @Property(bool, notify=changed)
    def musicVisible(self):
        return self._music_visible

    @Slot()
    def toggle_music(self):
        self._music_visible = not self._music_visible
        self.musicVisibilityChanged.emit()
        self.changed.emit()

    @Property(str, notify=changed)
    def title(self):
        return self.item.title if self.active else "Pulse"

    @Property(str, notify=changed)
    def body(self):
        return self.item.body if self.active else ""

    @Property(str, notify=changed)
    def appName(self):
        return self.item.app if self.active else ""

    @Property(int, notify=changed)
    def queued(self):
        return len(self.manager.pending)

    @Property("QVariantMap", notify=changed)
    def card(self):
        item = self.item
        return {"app": self.appName, "title": self.title, "body": self.body,
                "kind": str(item.kind) if item else "message",
                "value": item.value if item else 0.0,
                "valueLabel": item.value_label if item else "",
                "status": item.status if item else "",
                "artwork": item.artwork if item else "",
                "icon": self.icons.resolve(item) if item else "",
                "id": item.id if item else -1,
                "canOpen": bool(item and self.interactions and self.interactions.can_open(item)),
                "actions": [{"key": key, "label": label} for key, label in item.actions if key != "default"]
                           if item and self.interactions and self.interactions.action_available(item) else [],
                "busy": bool(self.interactions and self.interactions.pending)}

    def submit(self, notification, *, record_history=True):
        previous = self.item
        if record_history and self.history is not None and self.manager.rules.allows(notification):
            try:
                self.history.record(notification)
            except (sqlite3.Error, OSError) as error:
                self.historyFailed.emit(f"History disabled for this run: {error}")
                self.history = None
        self.manager.submit(notification)
        if previous is None and self.item is not None:
            self.reaction.emit("surprised")
        self.changed.emit()

    def submit_system(self, notification):
        if str(notification.kind) == "level" and not self.volume_visible:
            return
        self.submit(notification, record_history=False)

    def set_media(self, notification):
        previous = self.item
        self.media = notification if self.manager.rules.allows(notification) else None
        if previous is None and self.item is not None:
            self.reaction.emit("surprised")
        self.changed.emit()

    @Slot()
    def clear_media(self):
        if self.media is not None:
            self.media = None
            self.changed.emit()

    @Slot()
    def dismiss(self):
        previous = self.manager.current
        self.manager.dismiss()
        if previous is not None and self.item is None:
            self.reaction.emit("happy")
        self.changed.emit()

    def tick(self):
        previous = self.manager.current
        self.manager.tick()
        if previous != self.manager.current:
            self.changed.emit()

    @Slot(int)
    def close(self, notification_id):
        self.manager.close(notification_id)
        self.changed.emit()

    def remove_cards(self, predicate):
        self.manager.pending = [item for item in self.manager.pending if not predicate(item)]
        if self.manager.current is not None and predicate(self.manager.current):
            self.manager.dismiss()
        self.changed.emit()

    @Property(str, notify=changed)
    def actionError(self):
        return self._action_error

    def set_interactions(self, interactions):
        self.interactions = interactions
        interactions.changed.connect(self.changed)
        interactions.succeeded.connect(self.close)
        interactions.failed.connect(self.action_failed)

    def action_failed(self, message):
        self._action_error = message
        self.changed.emit()
        QTimer.singleShot(4000, self, self.clear_action_error)

    def clear_action_error(self):
        self._action_error = ""
        self.changed.emit()

    @Slot(int)
    @Slot(int, str)
    def activate(self, notification_id, action=""):
        item = self.manager.current
        if item is None or item.id != notification_id:
            return
        self._action_error = ""
        if self.interactions is None:
            self.dismiss()
        else:
            self.interactions.perform(item, action)
