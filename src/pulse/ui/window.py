"""Desktop placement and input regions for the fixed-size island window."""
from PySide6.QtCore import QObject, QRectF
from PySide6.QtGui import QGuiApplication, QPainterPath, QRegion


def island_region(x, y, width, height, radius):
    path = QPainterPath()
    path.addRoundedRect(QRectF(x, y, width, height), radius, radius)
    return QRegion(path.toFillPolygon().toPolygon())


class WindowIntegration(QObject):
    def __init__(self, window, backend):
        super().__init__(window)
        self.window = window
        self.backend = backend
        self.screen = None
        if backend != "offscreen":
            window.maskChanged.connect(self.update_mask)
        window.screenChanged.connect(self.bind_screen)
        app = QGuiApplication.instance()
        if isinstance(app, QGuiApplication):
            app.primaryScreenChanged.connect(self.follow_primary)
        self.bind_screen(window.screen())

    def update_mask(self, x, y, width, height, radius):
        self.window.setMask(island_region(x, y, width, height, radius))

    def bind_screen(self, screen):
        if self.screen is screen:
            self.place()
            return
        if self.screen is not None:
            try:
                self.screen.availableGeometryChanged.disconnect(self.place)
            except (RuntimeError, TypeError):
                pass  # The compositor may already have removed this screen.
        self.screen = screen
        if screen is not None:
            screen.availableGeometryChanged.connect(self.place)
            self.place()

    def follow_primary(self, screen):
        if screen is not None:
            self.window.setScreen(screen)
            self.bind_screen(screen)

    def place(self, *_):
        if self.backend != "layer-shell" and self.screen is not None:
            geometry = self.screen.availableGeometry()
            self.window.setPosition(
                geometry.x() + (geometry.width() - self.window.width()) // 2,
                geometry.y(),
            )
