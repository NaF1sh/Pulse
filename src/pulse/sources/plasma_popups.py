"""Opt-in, connection-scoped Plasma inhibition; never edit desktop preferences."""
import uuid

from PySide6.QtCore import QObject, QTimer, Signal

SERVICE = 'org.freedesktop.Notifications'
PATH = '/org/freedesktop/Notifications'


class BusLease(QObject):
    """A dedicated D-Bus connection owns exactly one temporary inhibition."""
    def __init__(self, parent=None):
        super().__init__(parent)
        from PySide6.QtDBus import QDBusConnection
        self.name = 'pulse-popups-' + uuid.uuid4().hex
        self.connection = QDBusConnection.connectToBus(QDBusConnection.SessionBus, self.name)
        self.pending = set()
        self.owner_watcher = None
        self.closed = False
        self.callback = None
        self.health = QTimer(self)
        self.health.setInterval(1000)
        self.health.timeout.connect(self.check_connection)

    def start(self, callback):
        from PySide6.QtDBus import QDBusServiceWatcher
        self.callback = callback
        if not self.connection.isConnected():
            callback(False, 'Session bus unavailable; Plasma popups remain enabled.')
            return
        self.owner_watcher = QDBusServiceWatcher(SERVICE, self.connection,
                                                QDBusServiceWatcher.WatchForOwnerChange, self)
        self.owner_watcher.serviceOwnerChanged.connect(self.owner_changed)
        self.health.start()
        self.call('GetCapabilities', [], self.capabilities)

    def call(self, method, arguments, callback):
        from PySide6.QtDBus import QDBusMessage, QDBusPendingCallWatcher
        message = QDBusMessage.createMethodCall(SERVICE, PATH, SERVICE, method)
        message.setArguments(arguments)
        watcher = QDBusPendingCallWatcher(self.connection.asyncCall(message, 2000), self)
        self.pending.add(watcher)
        def finished():
            self.pending.discard(watcher)
            reply = watcher.reply()
            watcher.deleteLater()
            if self.closed:
                return
            callback(reply.arguments() if reply.type() == QDBusMessage.ReplyMessage else None)
        watcher.finished.connect(finished)

    def capabilities(self, arguments):
        if not arguments or not isinstance(arguments[0], list) or 'inhibitions' not in arguments[0]:
            self.callback(False, 'This desktop does not advertise popup inhibition. Plasma settings were not changed.')
            return
        self.call('Inhibit', ['io.github.NaF1sh.Pulse', 'Notifications are shown by Pulse', {}], self.inhibited)

    def inhibited(self, arguments):
        if arguments and type(arguments[0]) is int and arguments[0] > 0:
            self.callback(True, 'Plasma inhibition is active. Critical alerts may still appear; sounds may also be paused.')
        else:
            self.callback(False, 'Could not pause Plasma popups. They remain under desktop control.')

    def owner_changed(self, name, old_owner, new_owner):
        if not self.closed:
            self.callback(False, 'Notification service changed. Reconnecting popup control…')

    def check_connection(self):
        if not self.closed and not self.connection.isConnected():
            self.callback(False, 'Session bus disconnected. Popup control will retry.')

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.health.stop()
        from PySide6.QtDBus import QDBusConnection
        if self.owner_watcher:
            self.owner_watcher.setConnection(QDBusConnection(''))
            self.owner_watcher.deleteLater()
            self.owner_watcher = None
        for watcher in self.pending:
            watcher.finished.disconnect()
            watcher.deleteLater()
        self.pending.clear()
        # Dropping all QDBusConnection copies closes this unique bus connection.
        # Plasma watches the caller's disappearance and releases only its cookies.
        self.connection = None
        QDBusConnection.disconnectFromBus(self.name)
        self.callback = None
        self.deleteLater()


class PlasmaPopups(QObject):
    status = Signal(str, bool)

    def __init__(self, parent=None, *, factory=BusLease):
        super().__init__(parent)
        self.factory = factory
        self.enabled = False
        self.monitor_ready = False
        self.lease = None
        self.last_status = None
        self.retry = QTimer(self)
        self.retry.setSingleShot(True)
        self.retry.setInterval(15000)
        self.retry.timeout.connect(self.sync)

    def report(self, detail, problem=False):
        if (detail, problem) != self.last_status:
            self.last_status = (detail, problem)
            self.status.emit(detail, problem)

    def set_enabled(self, enabled):
        if self.enabled != enabled or self.last_status is None:
            self.enabled = enabled
            self.sync()

    def set_monitor_ready(self, ready):
        if self.monitor_ready != ready:
            self.monitor_ready = ready
            self.sync()

    def drop(self):
        lease, self.lease = self.lease, None
        if lease is not None:
            lease.close()

    def sync(self):
        self.retry.stop()
        if not self.enabled or not self.monitor_ready:
            self.drop()
            self.report('Plasma popups are unchanged.' if not self.enabled else
                        'Waiting for Pulse notifications to connect. Plasma popups remain enabled.')
            return
        if self.lease is not None:
            return
        self.report('Requesting temporary Plasma popup inhibition…')
        try:
            lease = self.factory(self)
            self.lease = lease
            lease.start(lambda active, detail: self.completed(lease, active, detail))
        except (ImportError, RuntimeError) as error:
            self.drop()
            self.report('Popup control is unavailable in this Qt installation.', True)

    def completed(self, lease, active, detail):
        if lease is not self.lease:
            return
        if not active:
            self.drop()
            if self.enabled and self.monitor_ready:
                self.retry.start()
        self.report(detail, not active)

    def stop(self):
        self.enabled = False
        self.retry.stop()
        self.drop()
