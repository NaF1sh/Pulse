# Developing Pulse

Use Python 3.12+ on Linux. From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
./run.sh --demo
```

For live sources, use `./run.sh --observe`. Open Settings directly with `--settings`.

If you already have a compatible Python environment with PySide6, Pydantic, setuptools, wheel, and pip, the installer can reuse its packages:

```bash
./install.sh --python /path/to/python --system-site-packages
```

This route disables dependency downloads and build isolation. Normal users should use `./install.sh`.

## Validation

```bash
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software .venv/bin/python -m pytest -q
./run.sh --backend offscreen --demo --quit-after 5
./run.sh --doctor
```

Offscreen tests cover QML loading, interactions, persistence, parsing, queue behavior, and startup. They cannot establish real compositor stacking, input regions, focus, or frame rate. Use the [desktop checklist](release-readiness.md) for those.

Build a wheel with `python -m pip wheel --no-deps .`. A built package must contain the QML files and theme presets; test it outside the repository, not only through `PYTHONPATH=src`.

## README visuals

The checked-in GIF and screenshots are captured from the real QML interface using simulated data. Regenerate them with ffmpeg installed:

```bash
PYTHONPATH=src .venv/bin/python tools/render_demo.py
```

The renderer uses temporary preferences and does not capture your desktop or private notifications.

## Installation layout

The installer uses `$XDG_DATA_HOME/pulse/app` for its isolated environment and `$XDG_DATA_HOME/applications` for the desktop entry. Defaults are under `~/.local/share`. The launcher goes in `~/.local/bin`; `PULSE_BIN_DIR` can override this for testing. Config and history live separately and survive uninstall.

A per-session lock prevents duplicate windows. A local activation file asks the existing instance to open Settings; it contains only a random request identifier. Offscreen runs remain independent for tests.
