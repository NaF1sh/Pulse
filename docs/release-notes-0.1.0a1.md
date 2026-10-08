# Pulse 0.1.0a1 — preview release draft

A Linux desktop companion that brings notifications, music, and volume into a
compact island, with 38 companions and three themes.

## Included

- Compact message cards with source images, installed app icons, and a pet fallback.
- Supported KDE notification actions and installed-app launching.
- Persistent now-playing cards and PipeWire volume feedback.
- Refined, keyboard-accessible Settings with local history and first-run guidance.
- User-level installer, app-menu entry, update route, and data-preserving uninstall.
- Duplicate-instance protection, crash recovery, diagnostics, and connection retries.
- Experimental opt-in Plasma popup inhibition while Pulse's notification monitor is ready.
- Primary-monitor change handling and offscreen checks at 100%, 150%, and 200% scaling.
- MIT licensing for original code and documentation, with reference-image exclusions.

## Compatibility

KDE Plasma is the primary development target. X11/XWayland uses software rendering
by default. Native Wayland is experimental and needs compatible Qt/LayerShellQt.
Other desktops are not yet verified. Critical Plasma popups may still appear in
quiet mode; the inhibition API can also pause notification sounds.

## Validation and publication status

**166 automated tests passed** locally. Source/wheel builds and installed-package
startup were also checked. Real session-bus and compositor checks remain unverified in this
restricted environment. The first GitHub CI run must be checked after upload.

These are draft notes. No release has been published or tagged by this work.
