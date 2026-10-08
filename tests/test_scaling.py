"""Exercise QML rendering at common fractional/integer desktop scale factors."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('scale', ['1', '1.5', '2'])
def test_scaled_interface_starts_without_qml_errors(scale, tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=str(root / 'src'), QT_SCALE_FACTOR=scale,
               QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
               XDG_CONFIG_HOME=str(tmp_path / 'config'), XDG_DATA_HOME=str(tmp_path / 'data'))
    result = subprocess.run([sys.executable, '-m', 'pulse.main', '--backend', 'offscreen',
                             '--demo', '--settings', '--quit-after', '1'], env=env,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert 'Error' not in result.stderr
    assert 'binding loop' not in result.stderr.lower()
