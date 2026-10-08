"""Exercise real QML geometry through an opening and closing notification."""
import os
from pathlib import Path
import subprocess
import sys


def test_compact_notification_animation_and_hidden_app_label():
    root = Path(__file__).resolve().parents[1]
    script = r'''
from pathlib import Path
from PySide6.QtCore import QObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from pulse.core.models import Notification
from pulse.ui.controller import Controller
from pulse.ui.notification_icons import raw_image_url
from pulse.ui.pets import Pets
from pulse.themes.loader import load_theme
from pulse.themes.schema import qml_data
app = QGuiApplication([])
engine = QQmlApplicationEngine()
controller = Controller(engine)
pets = Pets(engine)
for name, value in [('pulseController', controller), ('pulsePets', pets),
                    ('pulseTheme', qml_data(load_theme('default')[0]))]:
    engine.rootContext().setContextProperty(name, value)
engine.load(str(Path('src/pulse/ui/qml/Island.qml').resolve()))
window = engine.rootObjects()[0]
window.show()
QTest.qWait(50)
surface = window.findChild(QObject, 'islandSurface')
icon = raw_image_url([1, 1, 4, True, 8, 4, [255, 0, 0, 255]])
controller.submit(Notification(1, 'notify-send', 'Alex', 'Hey! Are you joining us tonight?', icon_image=icon))
widths = []
for _ in range(20):
    QTest.qWait(20)
    widths.append(surface.property('width'))
assert all(a <= b + 0.1 for a, b in zip(widths, widths[1:])), widths
assert abs(widths[-1] - 280) < 0.1
assert surface.property('height') == 54
source_icon = window.findChild(QObject, 'notificationSourceIcon')
assert source_icon.property('visible')
assert source_icon.property('source').toString() == icon
assert window.property('displayed').toVariant()['title'] == 'Alex'
assert not any(child.property('text') == 'notify-send' for child in window.findChildren(QObject))
controller.dismiss()
widths = []
for _ in range(25):
    QTest.qWait(20)
    widths.append(surface.property('width'))
assert all(a + 0.1 >= b for a, b in zip(widths, widths[1:])), widths
assert abs(widths[-1] - 30) < 0.1
window.close()
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=root,
                            env=dict(os.environ, PYTHONPATH=str(root / 'src'),
                                     QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software'),
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert 'Error' not in result.stderr


def test_close_button_collapses_manual_bar_notifications_and_task_drawer(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = r'''
import sys
from pathlib import Path
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from shiboken6 import wrapInstance, getCppPointer
from pulse.core.models import Notification
from pulse.ui.controller import Controller
from pulse.ui.pets import Pets
from pulse.themes.loader import load_theme
from pulse.themes.schema import qml_data
app = QGuiApplication([])
engine = QQmlApplicationEngine()
controller = Controller(engine)
pets = Pets(engine, preference_path=Path(sys.argv[1]) / 'pet.json')
for name, value in [('pulseController', controller), ('pulsePets', pets),
                    ('pulseTheme', qml_data(load_theme('default')[0]))]:
    engine.rootContext().setContextProperty(name, value)
engine.load(str(Path('src/pulse/ui/qml/Island.qml').resolve()))
window = wrapInstance(getCppPointer(engine.rootObjects()[0])[0], QQuickWindow)
window.setProperty('reducedMotion', True)
window.show()
QTest.qWait(100)
button = window.findChild(QObject, 'dismissNotification')
surface = window.findChild(QObject, 'islandSurface')
def click_close():
    QTest.qWait(180)
    assert button.property('visible')
    point = button.mapToScene(QPointF(button.width()/2, button.height()/2)).toPoint()
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
    QTest.qWait(180)
def collapsed():
    assert not window.property('expanded')
    assert not window.property('tasksExpanded')
    assert not window.property('open')
    assert surface.property('width') == 30

# Empty manual expansion previously sent close(-1) without folding the bar.
window.setProperty('expanded', True)
click_close()
collapsed()

# Dismiss the visible notification without discarding the next queued alert.
window.setProperty('expanded', True)
controller.submit(Notification(1, 'Chat', 'First', timeout=0))
controller.submit(Notification(2, 'Chat', 'Second', timeout=0))
click_close()
assert controller.manager.current.id == 2
assert window.property('displayed').toVariant()['id'] == 2
assert not window.property('expanded')
click_close()
collapsed()

# Closing a task card also closes its drawer, without cancelling the task.
controller.tasks.start(Path(sys.argv[1]) / 'tasks.sqlite3')
controller.tasks.store.publish('agent', title='Agent review', state='needs-permission')
controller.tasks.poll()
window.setProperty('tasksExpanded', True)
click_close()
assert controller.tasks.card is None
assert controller.tasks.rows[0]['state'] == 'needs-permission'
collapsed()

# Recent tasks can open an otherwise empty drawer; its cross must fold it too.
window.setProperty('tasksExpanded', True)
click_close()
collapsed()
controller.tasks.stop()
controller.timer.stop()
window.close()
'''
    result = subprocess.run([sys.executable, '-c', script, str(tmp_path)], cwd=root,
                            env=dict(os.environ, PYTHONPATH=str(root / 'src'),
                                     QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software'),
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert 'Error' not in result.stderr
