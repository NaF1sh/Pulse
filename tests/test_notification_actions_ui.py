import os
from pathlib import Path
import subprocess
import sys


def test_notification_click_action_and_separate_dismiss(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = r'''
from pathlib import Path
from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from pulse.core.models import Notification
from pulse.sources.dbus_observer import NotificationDecoder
from pulse.ui.controller import Controller
from pulse.ui.interactions import Interactions, DesktopApps
from pulse.ui.pets import Pets
from pulse.themes.schema import Theme, qml_data
app = QGuiApplication([])
engine = QQmlApplicationEngine()
controller = Controller(engine)
interactions = Interactions(NotificationDecoder(), engine, apps=DesktopApps([]))
interactions.supported = True
interactions.decoder.server_ids[42] = 1
commands = []
interactions.command.start = lambda program, args: commands.append(args) or True
controller.set_interactions(interactions)
pets = Pets(engine)
for name, value in [('pulseController', controller), ('pulsePets', pets), ('pulseTheme', qml_data(Theme()))]:
    engine.rootContext().setContextProperty(name, value)
engine.load(str(Path('src/pulse/ui/qml/Island.qml').resolve()))
window = engine.rootObjects()[0]
window.setProperty('reducedMotion', True)
window.show()
controller.submit(Notification(1, 'Chat', 'Alex', 'Hello', timeout=0,
                               actions=(('default', 'Open'), ('mark', 'Mark read'))))
QTest.qWait(180)
surface = window.findChild(QObject, 'islandSurface')
assert surface.property('height') == 86
QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(210, 35))
assert commands[-1][-1] == 'default'
interactions.completed(1, '', 'failed')
assert controller.active
QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier,
                 QPoint(int(surface.x()) + 81, int(surface.y()) + 65))
assert len(commands) == 2, commands
assert commands[-1][-1] == 'mark'
interactions.completed(0, '', '')
assert not controller.active
QTest.qWait(180)
controller.submit(Notification(2, 'Chat', 'Second', 'Dismiss only', timeout=0))
QTest.qWait(180)
QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier,
                 QPoint(int(surface.x() + surface.width()) - 17, int(surface.y()) + 16))
assert not controller.active
assert len(commands) == 2
window.close()
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=root,
                            env=dict(os.environ, PYTHONPATH=str(root / 'src'),
                                     XDG_CONFIG_HOME=str(tmp_path), QT_QPA_PLATFORM='offscreen',
                                     QT_QUICK_BACKEND='software'),
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    for error in ('ReferenceError', 'TypeError', 'Unable to assign', 'AssertionError'):
        assert error not in result.stderr
