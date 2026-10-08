import pytest
from PySide6.QtCore import QPoint

from pulse.ui.window import island_region


def test_mask_covers_pill_but_excludes_transparent_corners():
    region = island_region(195, 12, 30, 30, 15)
    assert region.contains(QPoint(210, 27))
    assert not region.contains(QPoint(195, 12))
    assert not region.contains(QPoint(100, 27))


def test_expanded_mask_moves_with_centered_island():
    collapsed = island_region(195, 12, 30, 30, 15)
    expanded = island_region(60, 12, 300, 64, 32)
    assert not collapsed.contains(QPoint(80, 44))
    assert expanded.contains(QPoint(80, 44))
    assert expanded.contains(QPoint(340, 44))
    assert not expanded.contains(QPoint(60, 12))


def test_primary_screen_switch_and_geometry_change_reposition_window():
    from PySide6.QtCore import QObject, Signal, QRect
    from pulse.ui.window import WindowIntegration

    class Screen(QObject):
        availableGeometryChanged = Signal()
        def __init__(self, geometry):
            super().__init__()
            self.geometry = geometry
        def availableGeometry(self):
            return self.geometry

    class Window(QObject):
        screenChanged = Signal(object)
        maskChanged = Signal(float, float, float, float, float)
        def __init__(self, screen):
            super().__init__()
            self.current = screen
            self.position = None
        def screen(self): return self.current
        def width(self): return 420
        def setPosition(self, x, y): self.position = (x, y)
        def setScreen(self, screen):
            self.current = screen
            self.screenChanged.emit(screen)
        def setMask(self, region): pass

    first = Screen(QRect(0, 32, 1920, 1048))
    second = Screen(QRect(1920, 24, 1280, 1000))
    window = Window(first)
    integration = WindowIntegration(window, 'xcb')
    assert window.position == (750, 32)
    integration.follow_primary(second)
    assert window.position == (2350, 24)
    first.geometry = QRect(0, 0, 800, 600)
    first.availableGeometryChanged.emit()
    assert window.position == (2350, 24)
    second.geometry = QRect(1920, 0, 960, 700)
    second.availableGeometryChanged.emit()
    assert window.position == (2190, 0)


def test_drag_bounds_use_visible_card_and_negative_monitor_coordinates():
    from PySide6.QtCore import QPointF, QRect
    from pulse.ui.window import bounded_anchor
    screen = QRect(-1920, 40, 1920, 1040)
    assert bounded_anchor(QPointF(-3000, -100), screen, 30, 30) == QPointF(-1905, 40)
    assert bounded_anchor(QPointF(900, 2000), screen, 350, 370) == QPointF(-175, 710)
    assert bounded_anchor(QPointF(-960, 300), screen, 350, 370) == QPointF(-960, 300)


@pytest.mark.parametrize('scale', ['1', '1.5', '2'])
def test_drag_circle_and_bar_preserves_clicks_and_resets_on_launch(tmp_path, scale):
    import os
    from pathlib import Path
    import subprocess
    import sys
    root = Path(__file__).resolve().parents[1]
    script = r'''
from pathlib import Path
from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from shiboken6 import wrapInstance, getCppPointer
from pulse.core.models import Notification, Kind
from pulse.ui.controller import Controller
from pulse.ui.pets import Pets
from pulse.ui.window import WindowIntegration
from pulse.themes.schema import Theme, qml_data
app = QGuiApplication([])
engine = QQmlApplicationEngine()
controller = Controller(engine)
pets = Pets(engine)
for name, value in [('pulseController', controller), ('pulsePets', pets), ('pulseTheme', qml_data(Theme()))]:
    engine.rootContext().setContextProperty(name, value)
source = str(Path('src/pulse/ui/qml/Island.qml').resolve())
engine.load(source)
window = wrapInstance(getCppPointer(engine.rootObjects()[0])[0], QQuickWindow)
integration = WindowIntegration(window, 'offscreen')
window.show()
QTest.qWait(150)
geometry = window.screen().availableGeometry()
initial = window.position()
assert initial == QPoint(geometry.x() + (geometry.width() - window.width()) // 2, geometry.y())
def drag(local, delta):
    global_target = window.mapToGlobal(local) + delta
    QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, local)
    QTest.mouseMove(window, window.mapFromGlobal(global_target), 30)
    QTest.qWait(40)
    QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, window.mapFromGlobal(global_target))
    QTest.qWait(200)
# Move the pet without opening it or toggling music.
drag(QPoint(210, 27), QPoint(100, 120))
assert window.position() == initial + QPoint(100, 120), (window.position(), initial)
assert not window.property('open')
assert controller.musicVisible
# A normal click still opens the card.
QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(210, 27))
QTest.qWait(350)
assert window.property('open')
controller.submit(Notification(1, 'Chat', 'Drag me', timeout=0))
QTest.qWait(250)
position = window.position()
drag(QPoint(180, 32), QPoint(-60, 50))
assert window.position() == position + QPoint(-60, 50)
assert controller.manager.current.id == 1, 'Dragging must not activate or dismiss the notification'
# Metadata changes wait until release instead of swapping content under the pointer.
local = QPoint(180, 32)
target = window.mapToGlobal(local) + QPoint(20, 0)
QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, local)
QTest.mouseMove(window, window.mapFromGlobal(target), 30)
assert window.property('dragging')
controller.submit(Notification(1, 'Chat', 'Updated while dragging', timeout=0))
assert window.property('displayed').toVariant()['title'] == 'Drag me'
QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, window.mapFromGlobal(target))
QTest.qWait(200)
assert window.property('displayed').toVariant()['title'] == 'Updated while dragging'
# The close control remains a click target, not a drag handle.
button = window.findChild(QObject, 'dismissNotification')
point = button.mapToScene(QPoint(14, 14)).toPoint()
QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
QTest.qWait(450)
assert controller.manager.current is None
assert not window.property('open')
# Drag near the bottom/right, then expand: the entire card must fit.
drag(QPoint(210, 27), QPoint(5000, 5000))
controller.submit(Notification(2, 'Chat', 'Still reachable', timeout=0))
QTest.qWait(450)
surface = window.findChild(QObject, 'islandSurface')
left = window.x() + surface.property('x')
top = window.y() + surface.property('y')
assert left >= geometry.x() - 1
assert top >= geometry.y() - 1
assert left + surface.property('width') <= geometry.x() + geometry.width() + 1
assert top + surface.property('height') <= geometry.y() + geometry.height() + 1
# A new window/integration has no persisted drag position.
window.close()
engine.load(source)
restarted = wrapInstance(getCppPointer(engine.rootObjects()[-1])[0], QQuickWindow)
fresh = WindowIntegration(restarted, 'offscreen')
assert fresh.anchor is None
assert restarted.position() == initial
controller.timer.stop()
restarted.close()
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=root,
                            env=dict(os.environ, PYTHONPATH=str(root/'src'), XDG_CONFIG_HOME=str(tmp_path), QT_SCALE_FACTOR=scale,
                                     QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software'),
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    for message in ('TypeError', 'ReferenceError', 'binding loop', 'Unable to assign'):
        assert message not in result.stderr


def test_layer_shell_uses_margins_and_tracks_position_without_window_coordinates():
    from PySide6.QtCore import QObject, Property, Signal, QRect, QMargins, QPointF
    from pulse.ui.window import WindowIntegration
    class Screen(QObject):
        availableGeometryChanged = Signal()
        def availableGeometry(self): return QRect(1920, 32, 1280, 1000)
        def geometry(self): return QRect(1920, 0, 1280, 1080)
    class Layer(QObject):
        def __init__(self, parent):
            super().__init__(parent)
            self.value = QMargins()
        @Property(str, constant=True)
        def scope(self): return 'pulse'
        @Property(QMargins)
        def margins(self): return self.value
        @margins.setter
        def margins(self, value): self.value = value
    class Window(QObject):
        screenChanged = Signal(object)
        maskChanged = Signal(float, float, float, float, float)
        def __init__(self):
            super().__init__()
            self.current = Screen(self)
            self.layer = Layer(self)
            self.updates = 0
        def screen(self): return self.current
        def width(self): return 420
        def x(self): return 0  # Wayland does not provide a usable global window position.
        def y(self): return 0
        def setMask(self, region): pass
        def update(self): self.updates += 1
    window = Window()
    integration = WindowIntegration(window, 'layer-shell')
    assert window.layer.value == QMargins(430, 32, 0, 0)
    assert window.property('desktopPosition') == QPointF(2350, 32)
    integration.begin_move(2560, 59)
    integration.move_to(2640, 159)
    integration.end_move()
    assert window.layer.value == QMargins(510, 132, 0, 0)
    assert window.updates >= 2
