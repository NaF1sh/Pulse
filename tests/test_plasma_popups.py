from PySide6.QtCore import QCoreApplication

from pulse.sources.plasma_popups import PlasmaPopups

_APP = QCoreApplication.instance() or QCoreApplication([])


class Lease:
    def __init__(self, parent):
        self.closed = False
        self.callback = None

    def start(self, callback):
        self.callback = callback

    def close(self):
        self.closed = True


def test_inhibition_requires_both_opt_in_and_ready_monitor():
    control = PlasmaPopups(factory=Lease)
    control.set_enabled(True)
    assert control.lease is None
    control.set_monitor_ready(True)
    lease = control.lease
    lease.callback(True, 'Active')
    assert control.last_status == ('Active', False)
    control.set_monitor_ready(False)
    assert lease.closed
    assert control.lease is None
    control.stop()


def test_default_leaves_desktop_unchanged_and_reconnection_reacquires():
    control = PlasmaPopups(factory=Lease)
    control.set_monitor_ready(True)
    assert control.lease is None
    control.set_enabled(True)
    first = control.lease
    control.set_monitor_ready(False)
    control.set_monitor_ready(True)
    assert control.lease is not first
    assert first.closed
    control.stop()


def test_turning_off_while_inhibit_is_pending_ignores_late_reply():
    control = PlasmaPopups(factory=Lease)
    control.set_enabled(True)
    control.set_monitor_ready(True)
    lease = control.lease
    control.set_enabled(False)
    lease.callback(True, 'Late success')
    assert lease.closed
    assert control.lease is None
    assert control.last_status == ('Plasma popups are unchanged.', False)
    control.stop()


def test_failed_inhibition_closes_its_connection_and_retries():
    control = PlasmaPopups(factory=Lease)
    control.set_enabled(True)
    control.set_monitor_ready(True)
    lease = control.lease
    lease.callback(False, 'Unsupported')
    assert lease.closed
    assert control.retry.isActive()
    assert control.last_status == ('Unsupported', True)
    control.sync()
    replacement = control.lease
    assert replacement is not None and replacement is not lease
    control.stop()
    assert replacement.closed
    assert not control.retry.isActive()


def test_bus_transport_cannot_claim_success_without_bus(monkeypatch):
    from pulse.sources.plasma_popups import BusLease
    monkeypatch.setenv('DBUS_SESSION_BUS_ADDRESS', 'unix:path=/tmp/pulse-no-popup-bus')
    lease = BusLease()
    result = []
    lease.start(lambda active, detail: result.append((active, detail)))
    assert result and result[0][0] is False
    lease.close()
    assert lease.connection is None


def test_repeated_preference_updates_do_not_acquire_multiple_leases():
    control = PlasmaPopups(factory=Lease)
    control.set_enabled(True)
    control.set_monitor_ready(True)
    lease = control.lease
    for _ in range(10):
        control.set_enabled(True)
        control.set_monitor_ready(True)
    assert control.lease is lease
    control.stop()
