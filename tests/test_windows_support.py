import importlib.util
import os
from pathlib import Path
import sys

from pulse import platforms
from pulse.main import choose_backend
from pulse.tasks.store import TaskStore, default_path, validate_target


def test_windows_paths_and_backend_keep_linux_defaults_separate(monkeypatch, tmp_path):
    for name in ('XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_RUNTIME_DIR'):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path / 'Local AppData'))
    monkeypatch.setattr(platforms, 'is_windows', lambda: True)
    monkeypatch.setattr('pulse.main.is_windows', lambda: True)
    assert platforms.config_dir() == tmp_path / 'Local AppData/Pulse/config'
    assert default_path() == tmp_path / 'Local AppData/Pulse/data/tasks.sqlite3'
    assert platforms.runtime_dir() == tmp_path / 'Local AppData/Pulse/runtime'
    assert choose_backend('auto', '6.9.2') == 'windows'
    assert choose_backend('offscreen', '6.9.2') == 'offscreen'
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'isolated'))
    assert default_path() == tmp_path / 'isolated/pulse/tasks.sqlite3'


def test_windows_diagnostics_do_not_request_linux_packages(monkeypatch):
    from pulse.diagnostics import checks
    monkeypatch.setattr(platforms, 'is_windows', lambda: True)
    rows = checks()
    assert any(row['name'] == 'Platform' for row in rows)
    assert not any('busctl' in row['detail'] or 'wpctl' in row['detail'] for row in rows)


def test_windows_installer_dry_run_and_ownership(tmp_path, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location('windows_installer', Path('tools/install_windows.py'))
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path / 'local'))
    monkeypatch.setenv('APPDATA', str(tmp_path / 'roaming'))
    assert installer.main(['--dry-run']) == 0
    assert 'Pulse' in capsys.readouterr().out
    assert not (tmp_path / 'local').exists()
    paths = installer.locations()
    paths['root'].mkdir(parents=True)
    import pytest
    with pytest.raises(ValueError, match='non-Pulse'):
        installer.install(paths, sys.executable)


def test_native_paths_and_image_import(tmp_path):
    """Runs on the actual host, including Windows drive-letter paths in Windows CI."""
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtGui import QImage, QColor
    from pulse.ui.backgrounds import import_image
    app = QCoreApplication.instance() or QCoreApplication([])
    source = tmp_path / 'wallpaper with spaces.png'
    image = QImage(20,20,QImage.Format_RGB32)
    image.fill(QColor('red'))
    assert image.save(str(source))
    filename = import_image(str(source), tmp_path / 'backgrounds')
    assert (tmp_path / 'backgrounds' / filename).exists()
    assert validate_target(str(source)) == source.as_uri()
    store = TaskStore(tmp_path / 'tasks.sqlite3')
    store.publish('test', title='Native task', target=str(source))
    assert store.list()[0]['target'] == source.as_uri()
    store.close()
