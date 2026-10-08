# Pulse

A Python + QML Linux notification island with live notifications, pets, music, volume feedback, settings, and history. See [work completed so far](PROGRESS.md) and [the supplied plan](docs/project-plan.txt).

## Run

```bash
cd /home/naf1s/Projects/pulse
./run.sh --demo --debug
```

Without demo, click the pill to expand/collapse; right-click opens Settings, which also has a Quit Pulse button. `--demo` plays a repeating scripted sequence of messages, download progress, media and volume cards; left-click dismisses a demo card. In live mode, message clicks open the app/default action; × dismisses Pulse's copy. `--reduced-motion` disables the size transitions and uses short content fades. Use `--observe` for real notifications.

X11/XWayland defaults to Qt Quick software rendering to avoid GLX initialization failures. Use `--renderer software` to explicitly select it or `--renderer hardware` to try GPU rendering. An existing `QT_QUICK_BACKEND` setting takes precedence in auto mode. Desktop animation performance still needs checking with the selected renderer.

The transparent window stays 420 × 160; its input region follows the animated island, from a 30 × 30 pet to an expanded card. Ordinary messages use a compact 280 × 54 px layout (bounded by theme maximum width), without an app-name label; progress cards use 68 px height; music uses a compact 72 px layout and volume uses 58 px. Debug text shows animation state, frame rate and queue length while expanded.

The idle pet has pastel colors, expressive eyes and pink cheeks inspired by the
supplied references. Right-click and open the Pets tab to choose from 38 animals and round emotes in
a scrollable preview grid. Selection changes immediately and is saved between
launches. Hover makes the pet happy; after 30 seconds idle it gets sleepy.
The pet fades away when a card opens, and reduced motion disables blinking.
Pet colors follow the selected character; themes style notification cards.
New cards trigger a temporary surprised expression while the card opens. Dismissing the last
card gives it a happy expression as it returns. Reduced motion skips these
temporary reactions. Size changes use eased transitions without spring overshoot.

You can also choose a pet for one run with `./run.sh --observe --pet panda`, or
list IDs with `./run.sh --list-pets`. The picker's saved choice lives in
`~/.config/pulse/pet.json` (or under `$XDG_CONFIG_HOME`). See [pet details](docs/pets.md).

## Environment

The local `.venv` uses the existing Python 3.13 / PySide6 6.9.2 installation via system site packages. PyPI downloads were unavailable during setup. For a clean installation once network access works:

```bash
uv venv --clear .venv --python 3.13
uv pip install --python .venv/bin/python -e '.[dev]'
```

qasync and dbus-fast remain optional dependencies (`.[notifications]`) for future native async adapters. The current observer uses installed systemd tools and Qt; no asyncio integration is needed.

## Live notifications on KDE

```bash
./run.sh --observe --debug
```

In another desktop terminal, send a test notification:

```bash
notify-send -a Pulse 'Hello from Pulse' 'Live observer test' -t 8000
```

Observer mode uses the installed `busctl` JSON monitor through Qt's process API;
it does not require qasync or dbus-fast. Plasma keeps handling notifications, so
both Plasma and Pulse may show a popup. Clicking a message invokes its default action through KDE when supported, or
opens the installed app. The × button dismisses only Pulse's copy. Supplied
action buttons appear when KDE action invocation is available; inline replies
remain unavailable. See [interaction behavior and desktop tests](docs/interaction-and-polish.md). Notification replacements
and closure signals are mirrored when their server IDs have been observed.
Monitoring must be allowed by the session bus. Startup failure prints an error
and exits with status 2. `--observe` and `--demo` are mutually exclusive.

Live mode also watches MPRIS music players and PipeWire output volume:

```bash
./run.sh --observe --debug                 # Notifications, music and volume
./run.sh --music --volume --debug          # Music and volume only
./run.sh --observe --no-music --no-volume  # Notifications only
```

Start music in an MPRIS-compatible player to keep a compact now-playing card
visible with track, artist and cover art when supplied by the player. Notifications
and volume cards temporarily cover it; the latest track returns afterward.
Pause, stop or close the player to return to the pet. Left-clicking the music
card keeps it visible; playback controls remain in your music app.
Double-click the music card to hide it without pausing playback. Double-click
the idle pet to restore it, or right-click and toggle Now playing in General settings.
Hidden music stays hidden across track changes and restarts through saved preferences. This UI toggle requires the music source to be enabled.
Change output volume or mute using your normal desktop
controls to show a level card. These adapters are read-only; they do not control
playback or volume. `wpctl` is required for volume; `busctl` is required for music.
The initial volume reading sets a baseline without showing a card. Repeated
unchanged readings do not reopen the island. Music and volume cards follow
DND/per-app rules (`Music` and `Audio`) but are not saved to notification history.
System sources fail independently and retry without stopping notification
capture. See [system source details](docs/system-sources.md).

For YouTube, Pulse uses player-supplied artwork or derives a thumbnail when
the player exposes the video URL. Spotify cover URLs are supported directly.
When Chrome and KDE expose the same track, Pulse prefers the entry with artwork.
If Chrome exposes neither artwork nor a link, enable the official
[Plasma Integration browser extension](https://community.kde.org/Plasma/Browser_Integration)
with media integration enabled. This machine already has the KDE native backend
installed. Browser/player support varies; Pulse keeps the music-note fallback
when no usable image is available. No artwork is guessed from a song title.

Live capture was confirmed working by the user on KDE. This development
environment blocks session-bus access, so further live integration checks still
run on the desktop. See [observer status](docs/observer.md) for limits.

## Notification history

Live observer mode now saves the latest 1,000 eligible notification arrivals to
`$XDG_DATA_HOME/pulse/history.sqlite3` (normally
`~/.local/share/pulse/history.sqlite3`). Each entry contains the app name,
title, body, and UTC arrival time. Replacements create new history entries;
queued cards are saved on arrival and are not duplicated when displayed later.
Demo, muted and DND-suppressed notifications are not saved.

```bash
./run.sh --history             # Show the latest 20 entries, newest first
./run.sh --history 50          # Show up to 50 entries
./run.sh --clear-history       # Delete all saved entries
./run.sh --observe --no-history # Observe without saving this run
```

History commands print one JSON object per entry and exit without opening a
window. `--history-file PATH` selects a different SQLite file for capture or
history commands. New databases are created with owner-only permissions.
If storage fails during capture, Pulse reports the error and continues showing
notifications with history disabled for that run. The Settings window includes a graphical History tab with Refresh and Clear controls. See [history behavior](docs/history.md).

## Notification controls

Run `./run.sh --observe --dnd` to suppress ordinary Pulse cards while allowing
critical notifications. These settings affect Pulse only; Plasma keeps its own
notification settings.

Pulse reads `$XDG_CONFIG_HOME/pulse/config.toml` (normally
`~/.config/pulse/config.toml`) when present. Start with
[config.example.toml](config.example.toml), or try it directly:

```bash
./run.sh --demo --config config.example.toml --debug
```

Under `[notifications]`, set `dnd = true`, `allow_critical = false` for strict
silence, or `muted_apps = ["Music", "Downloads"]` to mute named apps. Names match
exactly, ignoring case. App muting also blocks critical cards from that app.
Suppressed cards are dropped rather than saved for later. `default_timeout`
sets seconds for live notifications requesting the default; explicit timeouts
and persistent cards retain their semantics. Under `[appearance]`, set
`reduced_motion = true` for short fades. CLI `--dnd` and `--reduced-motion` enable
those settings for one run. Restart after editing; invalid settings produce a
clear startup error. A missing default file uses built-in defaults; an explicit
missing `--config` file is an error.

## Themes

Choose one of three built-in themes:

```bash
./run.sh --demo --theme ocean --debug
./run.sh --observe --theme rose
./run.sh --observe --theme default
```

Default preserves the current compact appearance. Ocean uses cool blue colors
and gentler content fades; Rose uses pink accents and quicker content fades. For a custom
theme, copy a file from `themes/` and pass `--theme /path/to/theme.json`.
Under `[appearance]` in config.toml, set `theme = "ocean"` or a JSON path.
Config theme paths are relative to that config file; CLI theme paths are relative
to the launcher's working directory (the project root when using run.sh).

Themes are validated JSON data, with no executable code. Invalid colors,
unsupported keys or presets, and sizes outside compact bounds produce a clear
diagnostic and fall back to Default. Reduced motion overrides every preset.
Restart to apply changes. See [theme format](docs/themes.md) and the
[JSON schema](themes/schema.json).

## Window routes

`--backend auto` selects the installed LayerShellQt QML plugin only when system Qt and Python Qt versions match exactly; otherwise it uses X11/XWayland (`xcb`). `--backend layer-shell` requires that matching installation. This implementation checks the Arch-style `/usr/lib/qt6` plugin location. Layer-shell requests top anchoring, overlay layer, no reserved screen space and no keyboard focus.

The current machine has **KDE Wayland**, system Qt **6.11.2**, and Python Qt **6.9.2**, so auto chooses XWayland. Native layer-shell remains unverified. A matching system PySide6/Qt installation is needed to test that route. Background blur is not implemented.

## Verification

```bash
.venv/bin/python -m pytest -q
./run.sh --backend offscreen --demo --debug --quit-after 5
```

Offscreen rendering checks QML loading and timers; it cannot verify compositor placement, stacking, input masks or real display frame rate. See [the spike record](docs/spike.md) for the remaining desktop checks.

### Settings window

Right-click Pulse to open Settings, or launch with `./run.sh --observe --settings`.
General includes Now playing, volume feedback, DND, and reduced motion. Pets and
Appearance let you select a companion and palette. History shows the latest 100
saved notifications, with Refresh and Clear history controls. Demo cards are not saved.

Changes apply immediately and save in `~/.config/pulse/preferences.json`
(respecting `XDG_CONFIG_HOME`); pets retain their existing `pet.json` storage.
Saved preferences override TOML defaults, and explicit command-line appearance/DND
options override them for that run. Editing TOML still requires a restart.
Music and volume toggles control card visibility; live sources must be enabled
with `--observe`, `--music`, or `--volume`. DND affects Pulse only.

## Interaction and polish roadmap

Pulse's chosen pet remains central to the product: it will react to computer activity.
The next stages are interaction verification, pet/card transition polish, native
Wayland investigation, optional blur, and only then possible inline replies.
See [the ordered roadmap](docs/interaction-and-polish.md), including planned activity reactions.
