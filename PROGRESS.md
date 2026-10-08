# Pulse — work completed so far

Updated: 8 October 2026
Project: `/home/naf1s/Projects/pulse`

This records the work completed during development, the current behavior, and the limitations that remain. The original supplied plan is saved in [docs/project-plan.txt](docs/project-plan.txt).

## 1. Project foundation and startup fixes

- Built a Linux notification island using Python, PySide6, and Qt Quick/QML.
- Added `run.sh` and a local Python environment for launching the app.
- Positioned a transparent window at the top center of the screen, with a small idle pet that expands into cards.
- Added a repeating demo with sample messages, download progress, music, and volume changes.
- Added debug information showing animation state, frame rate, and queue length.
- Investigated the GLX startup crash (`Could not initialize GLX`). X11/XWayland now defaults to software rendering; renderer overrides remain available.
- Added automatic window-backend selection. The working route on this machine is XWayland; native layer-shell requires matching system Qt and PySide6 versions.
- Added an input region that follows the island so the surrounding transparent window does not intercept clicks.

## 2. Notification handling

- Added notification models, a priority queue, interruption by higher-priority notifications, timeouts, replacements, and dismissal.
- Added a read-only desktop notification observer using `busctl` through Qt's process API.
- Pulse can mirror desktop notifications sent by Discord and other applications to the desktop notification service.
- Added correlation with notification server IDs so observed replacements and closure signals can update Pulse.
- Cleaned notification markup into plain text and bounded displayed text lengths.
- Added DND, a configurable critical-alert exemption, and per-app muting.
- Live capture was confirmed working during development. `--demo` remains a separate source of sample cards.

Pulse mirrors notifications; Plasma still handles the original notifications and may display its own popup too. Clicking a regular Pulse card now requests its default action or opens its installed app. The separate × control dismisses only Pulse's copy.

## 3. Notification design and animation revisions

- Reduced the original oversized bar and revised the layout several times based on feedback.
- Added a small portrait of the selected pet beside notification text.
- Simplified ordinary notifications to a title and a single-line message preview.
- Removed the app-name label from the popup, including the unwanted `notify-send` text. App names remain available in history and filtering rules.
- Ordinary notification cards now use a compact **280 × 54 pixel** layout, subject to the theme's maximum width. Progress cards use a taller 68 pixel layout.
- Replaced bouncing width/height springs with a 260 ms eased transition.
- Fixed initial expansion ordering so the new card's content and dimensions are selected before opening.
- Removed the extra pre-expansion delay, kept content width stable while expanding, and clipped expanding content to the card.
- Added a reduced-motion option.

The transparent host window is still 420 × 160 pixels; the visible card is smaller. Smoothness on the actual desktop still depends on the renderer and compositor.

## 4. Pet faces and selection

- Used the supplied face references to develop code-rendered pets with expressive eyes, cheeks, ears, and moods.
- Added **38 selectable designs**: 19 animals and 19 round emotes.
- Saved supplied references under `docs/references/` and documented the pets in [docs/pets.md](docs/pets.md).
- Added a scrollable selection grid with live previews.
- Pet selection applies immediately and persists between launches.
- Added idle blinking, hover reactions, sleepiness, and temporary notification/dismissal expressions.
- Added `--pet ID` for a one-run choice and `--list-pets` to list available IDs.

## 5. Live music status

- Added read-only MPRIS monitoring for compatible music players and browser media sessions.
- Reworked music into a persistent background card instead of an expiring notification.
- The card shows the current track, artist/details, artwork when available, and a decorative animated music indicator.
- Notifications and volume cards temporarily cover music; the latest playing track returns afterward.
- Pausing, stopping, or losing the player clears the music card.
- Music updates remain cached while its display is hidden.
- Double-click the music card to hide it; double-click the idle pet to restore it.
- Added a matching Now playing toggle in Settings, with saved visibility across restarts.

### YouTube, Chrome, and Spotify artwork

- Added support for artwork URLs and local artwork files supplied by players.
- Added YouTube thumbnail derivation when the media session exposes a valid YouTube video URL.
- Added selection of the richer media entry when Chrome and KDE expose the same playing title and one provides artwork.
- Added a music-note fallback when usable artwork is unavailable.
- Checked that this machine has the KDE browser-integration native backend installed. Browser-extension enablement and metadata still depend on the user's browser setup.
- Documented the official Plasma Integration extension for Chrome.

Artwork is not guessed from song titles. YouTube/Spotify support depends on the metadata exposed through the player's media session.

## 6. Volume and mute feedback

- Added read-only PipeWire output-volume monitoring through `wpctl`.
- Added compact volume cards with a speaker indicator and level meter.
- Supported mute state and amplified volume labels.
- Made the first reading establish a quiet baseline; unchanged readings do not reopen the card.
- Added source timeouts and retries so music/volume failures do not stop notification capture.
- Added a saved Volume changes visibility toggle in Settings.
- Music and volume cards follow Pulse's notification rules but are excluded from notification history.

## 7. Notification history

- Added SQLite storage for the latest **1,000 eligible live notification arrivals**.
- Stored app, title, body, priority, kind, and UTC arrival time.
- Excluded demo cards, music/volume cards, muted notifications, and DND-suppressed notifications.
- Added headless CLI commands to view and clear history, plus a custom history-file option.
- Added `--no-history` to disable live recording for a run.
- Made history failures report an error without stopping notification display.
- Added a graphical History tab showing the latest 100 entries, with Refresh and Clear history controls.

## 8. Themes and configuration

- Added Default/Lavender, Ocean, and Rose palettes.
- Added validated JSON themes, a JSON schema, and safe fallback for invalid themes.
- Added TOML startup configuration for notification rules, default timeout, reduced motion, and theme selection.
- Added saved GUI preferences separately from TOML so the settings window does not overwrite the user's configuration file.
- Saved preferences override TOML defaults; explicit appearance/DND launch flags override the corresponding defaults for that run.

Default storage paths (respecting XDG directory overrides):

| Data | Path |
| --- | --- |
| Startup configuration | `~/.config/pulse/config.toml` |
| GUI preferences | `~/.config/pulse/preferences.json` |
| Selected pet | `~/.config/pulse/pet.json` |
| Notification history | `~/.local/share/pulse/history.sqlite3` |

## 9. Settings window

Right-click Pulse to open Settings, or launch with `--settings`.

- **General:** Now playing, Volume changes, Do not disturb, and Reduce motion.
- **Pets:** select from all 38 pets.
- **Appearance:** select a built-in palette immediately.
- **History:** view, refresh, and clear saved notifications.
- Added automatic preference saving, Escape to close, and Quit Pulse.

Music and volume toggles control visibility. Their live sources must be enabled with `--observe`, `--music`, or `--volume`.

## 10. Validation completed

- Added automated coverage for notification models, queue behavior, filtering, parsing, history, themes, pets, preferences, artwork, system sources, gestures, window masks, and QML startup.
- The last complete suite run before the final compact-notification change passed **120 tests**.
- After the compact-notification changes, 29 existing relevant checks passed. Added a real QML regression check for compact dimensions, hidden app label, and opening/closing without size overshoot; it passed, as did the final targeted five-test run after cleanup.
- Exercised settings toggles, pet selection, theme selection, and history view with Qt interaction checks.
- Captured and inspected offscreen screenshots of the UI during development.

Offscreen checks do not establish real desktop animation frame rate, compositor behavior, or live session-bus access. Those need desktop testing.

## 11. Current limitations and unfinished features

- **Inline replies are not implemented.** Replying to Discord from the bar is not currently possible.
- **Click-to-open and action buttons have an initial implementation.** KDE action support is detected at runtime; an installed-app fallback handles ordinary app opening. Real Discord/app activation still needs desktop verification. Inline replies remain unimplemented.
- Music and volume adapters do not control playback or output volume.
- Native Wayland layer-shell remains unverified on this machine because the installed system Qt and Python Qt versions differ.
- Background blur is not implemented.
- Pulse does not read Discord's chat history or messages directly; it receives notifications that applications send to the desktop.
- Browser artwork availability varies with media-session metadata and browser integration.
- UI polish and real desktop animation smoothness still need user feedback.

The limitations above remain; initial interaction support is completed locally but awaits real desktop verification.

## Useful commands

Run these from `/home/naf1s/Projects/pulse`:

```bash
./run.sh --observe                    # Real notifications, music, and volume
./run.sh --observe --settings         # Start live mode with Settings open
./run.sh --demo --debug               # Sample cards and debug information
./run.sh --observe --no-music --no-volume  # Notifications only
./run.sh --music --volume             # Music and volume only
./run.sh --observe --reduced-motion   # Minimal motion
./run.sh --observe --renderer software
./run.sh --history                    # Latest 20 saved notifications
./run.sh --clear-history
./run.sh --list-pets
.venv/bin/python -m pytest -q
```

Test desktop notification delivery from another terminal:

```bash
notify-send "Pulse test" "Can you see this?"
```

The test application's name is no longer shown on the notification card.

## 12. Interaction stage and product direction

- Added preservation of notification action keys/labels and desktop-entry hints.
- Added click-to-open using KDE default actions, with installed desktop-app fallback.
- Added compact action buttons and a separate × dismiss control.
- Added runtime capability detection, stale/unoffered-action rejection, repeated-click protection, and failure feedback that preserves the notification.
- Added parser, desktop-entry resolution, dispatch, failure handling, and actual QML click/action/dismiss tests. The complete suite now passes **139 tests** after this interaction stage.
- No notification text is executed as a shell command.
- Desktop session-bus access, including a private test bus, is blocked in this development environment. Live action dispatch and app activation still require desktop testing.

The next stages are explicitly ordered: interaction verification → exceptional pet/card transitions → native Wayland investigation → optional blur → possible inline replies. The 38-pet system remains central, with future activity reactions for music, charging, messages, completed downloads, mute, and DND. See [the interaction and polish roadmap](docs/interaction-and-polish.md) for implementation details, desktop test commands, and planned versus completed pet behaviors.

### Notification source icons

- Preserved app-icon and image-path hints and validated raw notification images.
- Added compact source icons, with installed desktop-entry lookup and pet fallback.
- Browser-supplied site images can appear without network favicon requests.
- Added parser, local image, desktop-entry fallback, and real QML display coverage.

### Interface refinement

- Rebuilt Settings around a persistent sidebar, neutral surfaces, consistent spacing, and theme accents.
- Replaced mouse-only settings controls with keyboard-accessible buttons and switches.
- Added scrolling, companion selection indicators, theme previews, and a clearer history empty state.
- Added notification hover feedback, readable text, pointer cursors, and discovery tooltips.
- Rendered all four settings pages offscreen for visual inspection; added a keyboard-to-persistence regression check.
- Release readiness still requires real desktop validation, onboarding, installation improvements, and packaging. Visual refinement alone does not establish production readiness.

### Preview distribution and startup reliability

- Added a user-level installer, isolated environment, app-menu launcher, update route, and ownership-aware uninstall that preserves preferences/history.
- Added per-desktop-session duplicate-launch protection; subsequent launches request Settings in the existing instance. Crash recovery is covered by a process-level test.
- Added first-run guidance and an unrecorded sample notification.
- Added Settings → Status and `--doctor` diagnostics. Notification monitoring failures keep the UI available and retry every 15 seconds.
- Recorded the real QML interface with synthetic demo data for the rewritten README; retained detailed configuration in `docs/usage.md`.
- Added contribution guidance, an explicit release checklist, package metadata, and GitHub CI configuration.
- Built and installed a wheel in an isolated location, validated the desktop entry, launched the installed package outside the checkout, and exercised uninstall. Installed the current build in the user's app menu using existing local dependencies.
- Full desktop/session-bus verification and the first hosted CI run remain external checks; this is still an early preview.

### Preview testing and Plasma popup control

- Added opt-in, temporary Plasma popup inhibition tied to notification monitor readiness; no persistent Plasma preferences are changed.
- Added teardown, reconnect, unsupported-server, and late-reply tests. Real Plasma suppression remains unverified because the desktop bus is inaccessible here.
- Follow primary-screen changes and use the installed desktop identity for the Qt app. Added logical placement and 100%/150%/200% offscreen startup checks.
- Added a synthetic guided desktop checker and draft 0.1.0a1 release notes.
- Applied the user's MIT license choice to original code/documentation and excluded supplied reference images from release packages.
- GitHub access from the shell still fails DNS resolution; hosted CI and publication cannot be verified until push succeeds.

Validation for the preview preparation: **166 tests passed**, including scaling, monitor readiness, popup-control lifecycle, and primary-screen placement. Source and wheel artifacts build; source archives exclude the supplied reference images.
