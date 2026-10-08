"""Bounded, read-only checks that can run without a graphical Qt application."""
import os
import shutil
import subprocess
import sys


def checks():
    results = []
    def add(name, state, detail):
        results.append({'name': name, 'state': state, 'detail': detail})
    add('Python', 'ok' if sys.version_info >= (3, 12) else 'error', sys.version.split()[0])
    from pulse.platforms import is_windows
    if is_windows():
        add('Platform', 'ok', 'Windows: floating island and local task events')
        add('Desktop integrations', 'info', 'Windows notification capture, music, and volume are not implemented in this preview')
        try:
            from PySide6.QtCore import qVersion
            add('Qt', 'ok', qVersion())
        except ImportError:
            add('Qt', 'error', 'Install Pulse dependencies to enable the interface')
        return results
    add('Display', 'ok' if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY') else 'warning',
        'Desktop session detected' if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
        else 'No desktop display detected; use --backend offscreen for tests')
    for executable, description in [('busctl', 'Notifications and music'), ('wpctl', 'Volume feedback'), ('gio', 'Opening installed apps')]:
        add(description, 'ok' if shutil.which(executable) else 'warning',
            f'{executable} available' if shutil.which(executable) else f'Install {executable} to enable this feature')
    if shutil.which('busctl'):
        try:
            result = subprocess.run(['busctl', '--user', '--timeout=2', '--no-pager', '--no-legend', 'list'],
                                    capture_output=True, text=True, timeout=3)
            if result.returncode:
                add('Session bus', 'warning', 'Unavailable; run Pulse inside your desktop session')
            else:
                names = {line.split()[0] for line in result.stdout.splitlines() if line.split()}
                add('Notification service', 'ok' if 'org.freedesktop.Notifications' in names else 'warning',
                    'Desktop notification service found' if 'org.freedesktop.Notifications' in names
                    else 'No notification service found')
        except (OSError, subprocess.TimeoutExpired):
            add('Session bus', 'warning', 'Check timed out or could not start')
    try:
        from PySide6.QtCore import qVersion
        add('Qt', 'ok', qVersion())
    except ImportError:
        add('Qt', 'error', 'Install Pulse dependencies to enable the interface')
    return results


def report():
    results = checks()
    for item in results:
        print(f"{item['state'].upper():7} {item['name']}: {item['detail']}")
    print('These checks do not verify notification monitoring permissions, window placement, or app activation.')
    return 1 if any(item['state'] == 'error' for item in results) else 0
