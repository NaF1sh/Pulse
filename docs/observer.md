# KDE notification observer

The user authorized live notification work after trying the compact fake demo.
Observer mode is implemented; the user confirmed live notifications work on
their KDE desktop on 2026-10-08.

Transport: `busctl --user --json=short --no-pager monitor org.freedesktop.Notifications`,
managed by QProcess on the Qt event loop. This follows the plan's source adapter
boundary without requiring unavailable qasync/dbus-fast packages. The monitor
uses BecomeMonitor and filters traffic to/from the notification service.
Pulse never registers the notification service or sends notification replies.

Notify calls become plain-text, bounded message cards. Urgency maps to queue
priority. Millisecond timeouts become seconds; zero is persistent, a negative
timeout uses five seconds (critical notifications remain until dismissed).
Replies correlate each client's serial with the server ID so subsequent
replacement calls update the same card. NotificationClosed removes active or
queued mirrored cards. Mapping tables are bounded to 1024 entries each.

Limitations: existing notifications at startup are not fetched. If the original
call/reply was missed or its mapping evicted, replacement appears as a new card.
Monitor reconnection clears ID mappings. Notification-server restarts while the monitor
remains connected still need desktop verification. App icons, image hints, and
supported KDE actions are available; progress hints and fullscreen detection remain unimplemented. SQLite history and its
view/clear commands are now available. Pulse has its
own DND and per-app mute settings, but does not inherit Plasma's DND state.
Observer mode may show notifications that Plasma suppresses. Pulse dismissal does not call
CloseNotification. Notification contents are not printed to the terminal.

Validation: decoder fixtures cover text sanitization, urgency, timeouts,
replacement correlation across senders, closure, malformed input and split JSON
reads. A subprocess check verifies unavailable-bus errors keep the interface available.
The live app reports failures in Settings → Status and retries every 15 seconds.
The desktop session bus is denied in this environment; a private dbus-daemon
also cannot bind its socket. The user verified actual Notify capture on their
desktop; live replacement and closure behavior still needs desktop verification.

Desktop check: run `./run.sh --observe --debug`, then send a notification with
`notify-send -a Pulse 'Hello from Pulse' 'Live observer test' -t 8000`. Confirm
Pulse shows it while Plasma continues to work. Repeat with critical urgency,
replacement (`notify-send -p` then `notify-send -r ID`), and closure. Right-click
Pulse, choose Quit Pulse in Settings, and verify no busctl monitor child remains.

References:

- [Desktop Notifications Specification](https://specifications.freedesktop.org/notification/latest-single/)
- [D-Bus monitoring](https://dbus.freedesktop.org/doc/dbus-specification.html#bus-messages-become-monitor)
- [systemd busctl implementation](https://github.com/systemd/systemd/blob/main/src/busctl/busctl.c)
- [systemd JSON message format](https://github.com/systemd/systemd/blob/main/src/libsystemd/sd-bus/bus-dump-json.c)
