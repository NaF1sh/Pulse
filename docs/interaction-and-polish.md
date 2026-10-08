# Next stage: interaction, polish, and a living companion

Pulse's identity is a chosen pet that reacts to the computer's activity. The 38-pet system stays central; the bar is how that companion communicates, rather than the product's entire identity.

## Ordered roadmap

1. **Click a notification to open the relevant app.** Initial implementation is in place: prefer the notification's default action through KDE; otherwise resolve an installed desktop entry. Preserve a separate dismiss control. Verify real Discord and other app behavior on the desktop, including focus and activation restrictions.
2. **Notification action buttons.** Initial implementation is in place for KDE's advertised action-invocation API. Preserve supplied labels and keys, reject stale/unoffered actions, and show a compact action row only when supported. Verify real app actions on the desktop.
3. **Exceptional pet/card transitions.** Keep the small footprint and smooth, interruptible motion. Develop a clear sequence from pet reaction to card opening and back, including rapid arrivals, dismissals, replacements, and music returning. Judge actual desktop motion, not just offscreen tests. Respect reduced motion throughout.
4. **Native Wayland investigation.** Resolve the Qt/PySide6/plugin version mismatch first; then verify top anchoring, stacking, input regions, multiple screens, and app activation on the native route.
5. **Optional blur.** Investigate compositor support after the native window route is understood. Preserve a polished opaque fallback and make blur optional.
6. **Inline replies, including Discord, only afterward.** Investigate actual app support before designing a reply UI. Do not treat generic notification actions as proof of inline-reply support.

## Pet reactions as a product feature

These are planned extensions, not claims that all activity sources exist today.

| Computer activity | Companion direction | Status |
| --- | --- | --- |
| Message received | Brief attentive/surprised reaction, then the message | Generic arrival reaction exists; richer choreography is planned |
| Music playing | Small rhythmic or contented reaction | Persistent music card exists; ongoing pet reaction is planned |
| Charging | Settled/resting or recharging mood | Live charging source and reaction are planned |
| Download finished | Brief celebration | Demo progress exists; general live completion detection and reaction are planned |
| Muted audio | Quiet/sleepy gesture | Live mute feedback exists; dedicated pet reaction is planned |
| Do not disturb | Calm resting state | DND filtering and settings exist; dedicated pet state is planned |

Reactions should be recognizable across all 38 designs, brief where appropriate, and calm during continuous activity. Establish priority between moods so simultaneous events do not cause flicker. Do not rely on pet expression alone to communicate important information.

## Current interaction behavior

- A message click requests its supplied `default` action if KDE action invocation is available and the notification's server ID is known.
- Otherwise Pulse opens the installed app identified by the notification's `desktop-entry` hint. If the hint is absent, an unambiguous installed app name/desktop ID match is used.
- Launches go through the desktop launcher (`gio launch`) with an argument list. Notification titles, bodies, and app names are never executed as commands.
- A successful action/launch dismisses Pulse's copy. Failure keeps the card visible and briefly shows an error.
- The × button dismisses only Pulse's copy without launching an app or invoking an action.
- Additional supplied actions appear in a horizontally scrollable row. Cards without actions remain 280 × 54 pixels; action cards add 32 pixels of height.
- Actions require KDE's `org.kde.NotificationManager.InvokeAction` API, discovered by introspection. Other desktops can use the installed-app fallback; generic action dispatch is not assumed.
- Inline-reply requests are not implemented. Music and volume sources remain read-only.
- This does not guarantee opening a particular conversation: that depends on the app's default action. A desktop-entry fallback opens the app itself.
- A successful D-Bus call confirms dispatch, not that the app visibly raised a window. Compositor focus rules and app behavior need desktop verification.

## Desktop verification

Start Pulse in live mode:

```bash
./run.sh --observe
```

From another terminal, test a supplied default action and an extra button:

```bash
notify-send -t 15000 --action=default=Open --action=mark='Mark read' \
  'Interaction test' 'Click the card or its Mark read button'
```

The terminal should print `default` when the card is clicked, or `mark` when the button is clicked. This test verifies action dispatch; it does not open a real app. The × button should dismiss only Pulse's card without producing an action result. Plasma may keep its own copy.

To test the installed-app fallback, use an app that is installed on the machine:

```bash
notify-send -t 15000 -h string:desktop-entry:discord \
  'App launch test' 'Click to open Discord'
```

Then test an actual Discord message with Discord minimized. Whether clicking opens the exact chat depends on Discord's supplied action and the desktop's activation behavior.

## References

- [Freedesktop notification specification](https://specifications.freedesktop.org/notification/latest-single/): action keys, default action, and desktop-entry hints.
- [KDE's notification-manager D-Bus interface](https://github.com/KDE/plasma-workspace/blob/master/libnotificationmanager/dbus/org.kde.notificationmanager.xml): `InvokeAction` method.
- [KDE's server implementation](https://github.com/KDE/plasma-workspace/blob/master/libnotificationmanager/server_p.cpp): action dispatch by the notification service.
