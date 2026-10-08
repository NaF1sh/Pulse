"""Verify settings render and keyboard changes reach persisted preferences."""
import os
from pathlib import Path
import subprocess
import sys


def test_settings_pages_and_keyboard_toggle(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = SCRIPT.replace('/tmp/pulse-review', tmp_path.as_posix())
    result = subprocess.run([sys.executable, '-c', script], cwd=root,
                            env=dict(os.environ, PYTHONPATH=str(root / 'src'),
                                     QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software'),
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert 'Error' not in result.stderr
    assert 'ReferenceError' not in result.stderr


SCRIPT = r'''
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from pulse.ui.pets import Pets
from pulse.ui.controller import Controller
from pulse.ui.preferences import Preferences
from pulse.settings import Settings
from pulse.themes.loader import load_theme
from pulse.themes.schema import qml_data
app = QGuiApplication([])
engine = QQmlApplicationEngine()
controller = Controller(engine)
pets = Pets(engine)
preferences = Preferences(controller, Settings(), Path('/tmp/pulse-review/history.db'), engine, path=Path('/tmp/pulse-review/preferences.json'))
for name, value in [('pulseController', controller), ('pulsePets', pets), ('pulseTheme', qml_data(load_theme('default')[0])), ('reviewPreferences', preferences)]:
    engine.rootContext().setContextProperty(name, value)
source = Path('src/pulse/ui/qml').resolve()
engine.loadData(b'import QtQuick\nSettingsWindow { preferences: reviewPreferences }', QUrl.fromLocalFile(str(source / 'Review.qml')))
assert engine.rootObjects()
from shiboken6 import wrapInstance, getCppPointer
from PySide6.QtQuick import QQuickWindow
window = wrapInstance(getCppPointer(engine.rootObjects()[0])[0], QQuickWindow)
window.show()
for tab in range(8):
    window.setProperty('tab', tab)
    QTest.qWait(180)
    assert not window.grabWindow().isNull()
window.setProperty('tab', 0)
QTest.qWait(50)
from PySide6.QtCore import QObject, Qt
# Find the actual switch by its public checked property, then exercise keyboard input.
def visual_items(item):
    yield item
    for child in item.childItems():
        yield from visual_items(child)
switch = next((item for item in visual_items(window.contentItem())
               if item.objectName() == 'preference-music'), None)
assert switch is not None
from PySide6.QtQuick import QQuickItem
switch = wrapInstance(getCppPointer(switch)[0], QQuickItem)
before = preferences.music
switch.forceActiveFocus()
QTest.keyClick(window, Qt.Key_Space)
QTest.qWait(50)
assert preferences.music != before
assert Preferences.read(preferences.path)['music'] == preferences.music
preferences.enable_welcome()
window.setWidth(700)
window.setHeight(560)
QTest.qWait(100)
assert window.property('welcoming')
assert not window.grabWindow().isNull()
preferences.completeWelcome()
QTest.qWait(50)
assert not window.property('welcoming')
window.close()
'''
