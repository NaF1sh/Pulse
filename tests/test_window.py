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
