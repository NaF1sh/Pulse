import importlib.util
from pathlib import Path
import subprocess

import pytest

spec = importlib.util.spec_from_file_location('pulse_installer', Path(__file__).resolve().parents[1] / 'tools/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def test_launcher_preserves_spaces_and_arguments(tmp_path):
    interpreter = tmp_path / 'path with spaces' / 'python'
    interpreter.parent.mkdir()
    interpreter.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
    interpreter.chmod(0o755)
    launcher = tmp_path / 'pulse'
    launcher.write_text(installer.launcher_text(interpreter))
    launcher.chmod(0o755)
    result = subprocess.check_output([str(launcher)], text=True)
    assert result.splitlines() == ['-m', 'pulse.main', '--observe']
    result = subprocess.check_output([str(launcher), '--theme', 'some path.json'], text=True)
    assert result.splitlines() == ['-m', 'pulse.main', '--theme', 'some path.json']


def test_installer_refuses_unowned_paths(tmp_path):
    paths = {'root': tmp_path / 'app', 'launcher': tmp_path / 'pulse',
             'desktop': tmp_path / 'pulse.desktop', 'icon': tmp_path / 'pulse.svg'}
    paths['launcher'].write_text('my other program')
    with pytest.raises(ValueError, match='existing file'):
        installer.install(paths, python='python3')
    assert paths['launcher'].read_text() == 'my other program'
    assert not paths['root'].exists()


def test_uninstall_keeps_history_and_modified_launcher(tmp_path):
    import json
    paths = {'root': tmp_path / 'app', 'launcher': tmp_path / 'pulse',
             'desktop': tmp_path / 'pulse.desktop', 'icon': tmp_path / 'pulse.svg'}
    paths['root'].mkdir()
    (paths['root'] / 'install.json').write_text(json.dumps({'installer': installer.MARKER}))
    paths['launcher'].write_text('different program')
    paths['desktop'].write_text(installer.desktop_text(paths['launcher']))
    history = tmp_path / 'history.sqlite3'
    history.write_text('keep this data')
    installer.uninstall(paths)
    assert history.read_text() == 'keep this data'
    assert paths['launcher'].read_text() == 'different program'
    assert not paths['desktop'].exists()
    assert not paths['root'].exists()
