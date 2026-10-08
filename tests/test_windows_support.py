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


def load_installer():
    spec = importlib.util.spec_from_file_location('windows_installer', Path('tools/install_windows.py'))
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    return installer


def owned_install(tmp_path):
    import hashlib
    import json
    installer = load_installer()
    root = tmp_path / 'Pulse/app'
    root.mkdir(parents=True)
    link = tmp_path / 'Pulse.lnk'
    link.write_bytes(b'original shortcut')
    (root / 'install.json').write_text(json.dumps(dict(installer=installer.MARKER,
        shortcut_sha256=hashlib.sha256(link.read_bytes()).hexdigest())))
    (root / 'uninstall.py').write_text('uninstaller')
    (root / 'venv').mkdir()
    (root / 'venv/pulse.exe').write_bytes(b'app')
    data = root.parent / 'config/preferences.json'
    data.parent.mkdir()
    data.write_text('preferences')
    return installer, dict(root=root, shortcut=link), data


def test_uninstall_preserves_user_data_and_modified_shortcuts(tmp_path, monkeypatch):
    installer, paths, data = owned_install(tmp_path)
    paths['shortcut'].write_bytes(b'user modified shortcut')
    removed = []
    monkeypatch.setattr(installer, 'ensure_not_running', lambda paths: None)
    monkeypatch.setattr(installer, 'unregister_uninstaller', lambda paths: removed.append(True))
    installer.uninstall(paths)
    assert not paths['root'].exists()
    assert data.read_text() == 'preferences'
    assert paths['shortcut'].read_bytes() == b'user modified shortcut'
    assert removed == [True]


def test_running_app_blocks_removal_before_any_deletion(tmp_path, monkeypatch):
    import pytest
    from types import SimpleNamespace
    installer, paths, data = owned_install(tmp_path)
    monkeypatch.setattr(installer.subprocess, 'run', lambda *a, **k: SimpleNamespace(stdout='running\n'))
    with pytest.raises(ValueError, match='Quit Pulse'):
        installer.uninstall(paths)
    assert (paths['root'] / 'venv/pulse.exe').exists()
    assert paths['shortcut'].exists()
    assert installer.manifest_at(paths['root'])


def test_locked_file_keeps_uninstaller_and_ownership_for_retry(tmp_path, monkeypatch):
    import pytest
    installer, paths, data = owned_install(tmp_path)
    monkeypatch.setattr(installer, 'ensure_not_running', lambda paths: None)
    def locked(*args, **kwargs):
        raise PermissionError('File in use')
    monkeypatch.setattr(installer.shutil, 'rmtree', locked)
    with pytest.raises(PermissionError):
        installer.uninstall(paths)
    assert installer.manifest_at(paths['root'])
    assert (paths['root'] / 'uninstall.py').exists()
    assert paths['shortcut'].exists()
    assert data.exists()


def test_uninstall_refuses_unowned_directory(tmp_path):
    import pytest
    installer = load_installer()
    root = tmp_path / 'app'
    root.mkdir()
    (root / 'keep.txt').write_text('unrelated data')
    with pytest.raises(ValueError, match='installer-owned'):
        installer.uninstall(dict(root=root, shortcut=tmp_path / 'link'))
    assert (root / 'keep.txt').read_text() == 'unrelated data'


def test_installed_apps_registration_uses_external_python_and_ownership(tmp_path, monkeypatch):
    import contextlib
    import pytest
    installer, paths, data = owned_install(tmp_path)
    class Registry:
        HKEY_CURRENT_USER = 'user'
        REG_SZ = 1
        REG_DWORD = 4
        def __init__(self):
            self.values = {}
            self.deleted = False
        def CreateKey(self, hive, key):
            assert hive == self.HKEY_CURRENT_USER
            assert key == installer.UNINSTALL_KEY
            return contextlib.nullcontext(self)
        OpenKey = CreateKey
        def QueryValueEx(self, key, name):
            if name not in self.values:
                raise FileNotFoundError(name)
            return self.values[name], self.REG_SZ
        def SetValueEx(self, key, name, reserved, kind, value):
            self.values[name] = value
        def DeleteKey(self, hive, key):
            self.deleted = True
    registry = Registry()
    monkeypatch.setitem(sys.modules, 'winreg', registry)
    external = tmp_path / 'Python with spaces/python.exe'
    monkeypatch.setattr(installer.subprocess, 'check_output', lambda *a, **k: str(external))
    installer.register_uninstaller(paths, 'python')
    assert registry.values['DisplayName'] == 'Pulse'
    expected = installer.subprocess.list2cmdline([str(external), str(paths['root'] / 'uninstall.py'), '--uninstall', '--interactive'])
    assert registry.values['UninstallString'] == expected
    assert 'def uninstall(' in (paths['root'] / 'uninstall.py').read_text()
    registry.values['InstallLocation'] = str(tmp_path / 'different app')
    installer.unregister_uninstaller(paths)
    assert not registry.deleted
    with pytest.raises(ValueError, match='another Pulse'):
        installer.register_uninstaller(paths, 'python')
    registry.values['InstallLocation'] = str(paths['root'])
    installer.unregister_uninstaller(paths)
    assert registry.deleted


def test_python_314_is_accepted_and_reports_selected_interpreter(monkeypatch):
    import json
    installer = load_installer()
    info = dict(version=[3, 14, 0], executable='C:/Python314/python.exe', implementation='CPython', bits=64)
    monkeypatch.setattr(installer.subprocess, 'check_output', lambda *a, **k: json.dumps(info))
    assert installer.python_info('py') == info
    info['version'] = [3, 11, 9]
    import pytest
    with pytest.raises(ValueError, match='Selected Python 3.11.9'):
        installer.python_info('python')


def test_install_step_saves_actual_failure(tmp_path, capsys):
    import pytest
    installer = load_installer()
    log = tmp_path / 'install.log'
    with pytest.raises(ValueError, match='Installing dependencies failed'):
        installer.install_step('Installing dependencies', [sys.executable, '-c',
            'import sys; print("Dependency download failed", file=sys.stderr); sys.exit(7)'], log)
    assert 'Dependency download failed' in log.read_text()
    assert 'Dependency download failed' in capsys.readouterr().out


def test_stale_pulse_shortcut_is_repaired_but_unrelated_link_is_preserved(tmp_path, monkeypatch):
    import json
    import pytest
    from types import SimpleNamespace
    installer = load_installer()
    paths = dict(root=tmp_path / 'Pulse/app', shortcut=tmp_path / 'Pulse.lnk')
    paths['shortcut'].write_bytes(b'existing shortcut')
    target = paths['root'] / 'venv/Scripts/pulse-island.exe'
    response = dict(target=str(target), arguments='')
    monkeypatch.setattr(installer.subprocess, 'run', lambda *a, **k: SimpleNamespace(stdout=json.dumps(response)))
    steps = []
    monkeypatch.setattr(installer, 'install_step', lambda label, cmd, log: steps.append(label))
    monkeypatch.setattr(installer, 'shortcut', lambda paths: paths['shortcut'].write_bytes(b'repaired shortcut'))
    monkeypatch.setattr(installer, 'register_uninstaller', lambda paths, python: None)
    assert installer.is_pulse_shortcut(paths)
    response['arguments'] = '--unexpected-command'
    assert not installer.is_pulse_shortcut(paths)
    response['arguments'] = ''
    response['target'] = str(tmp_path / 'OtherApp.exe')
    with pytest.raises(ValueError, match='leaving it untouched'):
        installer.install(paths, sys.executable)
    assert not paths['root'].exists()
    assert paths['shortcut'].read_bytes() == b'existing shortcut'
    assert not steps
    response['target'] = str(target)
    installer.install(paths, sys.executable)
    assert paths['shortcut'].read_bytes() == b'repaired shortcut'
    assert installer.manifest_at(paths['root'])['shortcut_sha256']
    assert len(steps) == 3
