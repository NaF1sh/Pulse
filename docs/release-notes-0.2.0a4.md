# Pulse 0.2.0a4 — Windows installation repair

Fixes installation being blocked by a leftover Pulse Start-menu shortcut after removal
of the app folder or installation manifest. The installer checks the shortcut target
before repairing it; unrelated shortcuts remain untouched.

The launcher no longer labels every installation failure as a Python version problem.
It can use `python` when a compatible `py` launcher is unavailable. The installer prints
the selected interpreter, updates pip, and saves dependency output and the actual failure
to `%LOCALAPPDATA%\Pulse\install.log`. Python 3.14 passes the version requirement.

The Windows CI matrix now includes Python 3.12 and 3.14. Native Windows validation remains
pending; local regression tests cover stale shortcut repair, unrelated shortcut protection,
Python version detection, and error logging. Includes the music, close-button, and uninstall
fixes from previous previews.
