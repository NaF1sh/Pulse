import os
from pathlib import Path
import subprocess
import sys

from pulse.main import choose_backend


def test_missing_system_qt_falls_back(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    def missing(*args, **kwargs):
        raise FileNotFoundError
    monkeypatch.setattr(subprocess, "check_output", missing)
    assert choose_backend("auto", "6.9.2") == "xcb"


def test_mismatched_system_qt_falls_back(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: "6.11.2\n")
    assert choose_backend("auto", "6.9.2") == "xcb"


def test_qml_loads_and_demo_exits():
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=str(root / "src"))
    result = subprocess.run(
        [sys.executable, "-m", "pulse.main", "--backend", "offscreen",
         "--demo", "--debug", "--quit-after", "4.5"],
        env=env, capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert "backend=offscreen" in result.stdout
    assert "Error" not in result.stderr
