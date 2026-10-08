<div align="center">
  <img src="assets/pulse.svg" width="80" alt="Pulse icon">
  <h1>Pulse</h1>
  <p>A quiet companion for your Linux desktop.</p>
  <p>Notifications, music, and volume in a small island that gets out of your way.</p>
</div>

![Pulse showing messages, music, and volume in the actual interface with simulated data](docs/assets/pulse-demo.gif)

**Early preview · KDE Plasma is the primary development desktop.** Live notification capture has been confirmed on KDE; wider desktop compatibility and native Wayland behavior still need testing.

## Small presence, useful details

- **Messages at a glance.** Source icons, compact previews, notification actions, and click-to-open when supported by the desktop and app.
- **Your music nearby.** Track, artist, and artwork from MPRIS players. Notifications briefly take its place, then the song returns.
- **A companion you choose.** 38 pets and emotes, three palettes, and reduced-motion support.
- **Controls that stay out of the way.** Volume feedback, Do not disturb, and local notification history.

![Pulse settings with sidebar navigation and notification preferences](docs/assets/settings.png)

## Install

Requires **Linux and Python 3.12+**. The installer creates a private Python environment, downloads dependencies, and adds Pulse to your app menu. No `sudo` is needed.

```bash
git clone https://github.com/NaF1sh/Pulse.git
cd Pulse
./install.sh
```

Open **Pulse** from your app menu, or run:

```bash
~/.local/bin/pulse
```

The first launch explains the controls and lets you choose your companion. Launching it again opens Settings in the running instance.

System tools enable desktop features:

| Tool | Used for |
| --- | --- |
| `busctl` | Desktop notifications and MPRIS music |
| `wpctl` | PipeWire volume feedback |
| `gio` | Opening installed applications |

These usually come from your distribution's systemd, WirePlumber, and GLib packages. Run `~/.local/bin/pulse --doctor` for a local dependency check. Missing features and notification connection failures are also visible in **Settings → Status**.

Try the interface without reading notifications:

```bash
~/.local/bin/pulse --demo
```

Quit an existing live instance first when switching to demo mode. Pulse intentionally keeps one instance per desktop session.

## Learn the gestures

| Gesture | Result |
| --- | --- |
| Right-click the pet or card | Open Settings |
| Click a notification | Request its default action or open its app |
| Click × | Dismiss Pulse's copy |
| Double-click music or the idle pet | Hide or restore the music card |

The **Status** page also offers a sample notification. Keyboard navigation works throughout Settings.

## Compatibility and current limits

| Area | Current behavior |
| --- | --- |
| KDE Plasma | Primary development target; notification action support is detected at runtime |
| X11 / XWayland | Default fallback with software rendering |
| Native Wayland | Experimental; requires matching Qt and LayerShellQt installations |
| Other desktops | Not yet verified; notification monitoring permissions and app activation may differ |
| Music | Requires an MPRIS-compatible player; artwork depends on the player/browser |
| Website icons | Uses the image provided by the browser, with an app/pet fallback |

Pulse mirrors the desktop notification service. **Your desktop can still show its own popup.** On supported Plasma versions, the opt-in **Quiet Plasma popups** setting requests temporary inhibition while Pulse is connected. Critical alerts may still appear, and notification sounds may be paused. This experimental mode needs real-desktop verification; see [popup behavior and testing](docs/plasma-popups.md). Pulse does not replace your notification daemon. Inline replies, blur, and playback controls are not implemented.

Connection failures keep Pulse open and retry every 15 seconds. This helps recovery; it does not override desktop permissions.

## Privacy

Live mode stores up to **1,000 notification arrivals locally**, including app name, title, message, and arrival time. Clear them in Settings → History, or launch with `--observe --no-history` to disable recording for that session. Demo cards are not recorded.

Preferences and history use the standard XDG config/data locations. Pulse does not upload notification history. Media artwork may load from URLs supplied by your player or derived from its YouTube video URL; notification icons are resolved locally.

## Update or uninstall

From your checkout:

```bash
git pull
./install.sh
```

Quit and reopen Pulse after updating.

```bash
./install.sh --uninstall
```

Uninstalling keeps your preferences and notification history. Installation paths can be reviewed with `./install.sh --dry-run`. Automatic login startup is not enabled.

## Help build Pulse

Useful feedback includes your desktop environment, session type, `pulse --doctor` output, and steps to reproduce. Avoid including private notification text in reports.

- [Detailed usage and configuration](docs/usage.md)
- [Development and tests](docs/development.md)
- [Contributing](CONTRIBUTING.md)
- [Release checklist](docs/release-readiness.md)
- [Report a bug](https://github.com/NaF1sh/Pulse/issues)

If Pulse makes your desktop a little better, a star helps other people discover it.

## License

Original code and documentation are [MIT licensed](LICENSE). See [asset exclusions](ASSET_NOTICE.md) for supplied reference images and third-party artwork.
