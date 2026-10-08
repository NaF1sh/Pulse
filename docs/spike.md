# Milestone 0 record — 2026-10-08

- Session: Wayland, KDE; WAYLAND_DISPLAY=wayland-0, DISPLAY=:0.
- Python: 3.13.9; available PySide6 / Qt runtime: 6.9.2.
- System Qt: 6.11.2. LayerShellQt shell plugin and QML module are installed.
- Dependency download: failed due to DNS/network restrictions. The local virtualenv inherits existing Python packages for this spike.
- Offscreen: QML loads, automatic expand/collapse runs, application exits cleanly.
- XWayland: launch attempted, but this execution environment cannot connect to display :0. Desktop placement cannot be inferred from the offscreen run.
- Session D-Bus: access denied in this execution environment; notification owner was not verified.
- Native layer-shell: not run because system and Python Qt versions differ. Loading mismatched system plugins is avoided.

## Desktop exit gate — pending

Desktop launch reported `Could not initialize GLX` and SIGABRT on XWayland. The X11/XWayland route now defaults to software rendering; desktop validation remains pending.

The user confirmed the software-rendered desktop launch works. Periodic expansion/collapse was the expected `--demo` timer. Placement above other windows, click-through and rapid-toggle smoothness have not yet been confirmed.

Input masks now explicitly follow position and corner-radius changes as well as size, and are applied before the window is shown. Screen placement and mask handling live in `ui/window.py`; screen geometry listeners follow screen changes. Five automated tests pass, including rounded input-region checks and the offscreen demo.

Run `./run.sh --demo --debug` from a local desktop terminal.

1. Confirm the pill is top-center above other ordinary windows.
2. Click another window through transparent corners and the area around the pill, both collapsed and expanded.
3. Click the pill to toggle; right-click to exit.
4. Confirm rapid toggles reverse the spring smoothly and the window itself never resizes.
5. Check animation smoothness against the actual monitor refresh rate.
6. With matching system Qt/PySide6 installed, test `--backend layer-shell` and record placement/stacking/click-through results.

Milestone 0 was accepted by the user on 2026-10-08 ("the first version is perfect") after the software-rendering fix. Continue Milestone 1 with the working XWayland route. Native layer-shell remains unverified; no notification capture or theme work has begun.

## Primary references

- Qt input-mask contract: https://doc.qt.io/qt-6/qwindow.html#setMask
- KDE shell integration: https://api.kde.org/legacy/plasma/layer-shell-qt/html/shell_8cpp_source.html
- LayerShellQt properties were checked against the installed `/usr/include/LayerShellQt/window.h` and `/usr/lib/qt6/qml/org/kde/layershell/LayerShellQtQml.qmltypes`.
