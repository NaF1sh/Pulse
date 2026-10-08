from PySide6.QtCore import QCoreApplication
from PySide6.QtTest import QTest

from pulse.runtime import Session

_APP = QCoreApplication.instance() or QCoreApplication([])


def test_second_instance_activates_first_and_release_allows_restart(tmp_path):
    first = Session(directory=tmp_path, identity='test')
    assert first.acquire()
    activations = []
    first.activated.connect(lambda: activations.append(True))
    second = Session(directory=tmp_path, identity='test')
    assert not second.acquire()
    QTest.qWait(100)
    assert activations == [True]
    first.close()
    assert second.acquire()
    second.close()


def test_different_desktop_sessions_are_independent(tmp_path):
    first = Session(directory=tmp_path, identity='desktop-one')
    second = Session(directory=tmp_path, identity='desktop-two')
    try:
        assert first.acquire()
        assert second.acquire()
    finally:
        first.close()
        second.close()


def test_crashed_owner_does_not_block_next_launch(tmp_path):
    import os
    import subprocess
    import sys
    result = subprocess.run([sys.executable, '-c',
        'import os, sys; from PySide6.QtCore import QCoreApplication; '
        'from pulse.runtime import Session; app = QCoreApplication([]); '
        'session = Session(directory=sys.argv[1], identity="crash"); '
        'assert session.acquire(); os._exit(0)', str(tmp_path)],
        env=dict(os.environ, PYTHONPATH='src'), capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    restarted = Session(directory=tmp_path, identity='crash')
    try:
        assert restarted.acquire()
    finally:
        restarted.close()
