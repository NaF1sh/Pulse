# Avoiding duplicate Plasma popups

In **Settings → General**, enable **Quiet Plasma popups · experimental**. Check
**Status → Plasma popups** to see whether the request succeeded.

This opt-in mode requests a temporary inhibition from the desktop notification
service while Pulse's monitor is connected. It does not edit Plasma's saved
settings or take over the notification service. It defaults off.

- Ordinary Plasma popups can be paused while Pulse displays the incoming messages.
- Plasma notification sounds may also be paused by its inhibition policy.
- Critical alerts can still appear according to Plasma's settings. This is not a
  guarantee that every possible duplicate is eliminated.
- Turning the option off, losing the Pulse monitor, or exiting Pulse releases
  Pulse's dedicated bus connection. Plasma removes that connection's inhibition.
- Other applications' inhibitors and the user's own Do not disturb preference
  remain under their existing owners' control.
- Unsupported desktops and failed requests are reported in Status. Pulse keeps
  displaying notifications and retries popup control after 15 seconds.

The controls and failure/reconnection logic are covered by automated tests. A
real Plasma session must still verify actual popup suppression and restoration.
This development session cannot access the desktop D-Bus connection.

## Desktop verification

Quit any older running Pulse build, then launch the updated version. From a
regular desktop terminal in this repository:

```bash
python3 tools/desktop_check.py --output /tmp/pulse-desktop-check.md
```

The guided check uses synthetic content to test source icons, replacement,
closure, default actions, popup inhibition/restoration, and manual music/display
checks. It does not alter Plasma preferences or capture private notifications.

## Protocol references

- [KDE notification API](https://github.com/KDE/plasma-workspace/blob/master/libnotificationmanager/dbus/org.freedesktop.Notifications.xml): `GetCapabilities` advertises `inhibitions`; `Inhibit` accepts a desktop entry, reason, and hints.
- [KDE implementation](https://github.com/KDE/plasma-workspace/blob/master/libnotificationmanager/server_p.cpp): the server tracks each inhibitor's D-Bus owner and releases its cookies when that owner disconnects.
- [Qt connection lifetime](https://doc.qt.io/qtforpython-6/PySide6/QtDBus/QDBusConnection.html): dedicated connection references must be released when disconnecting.
