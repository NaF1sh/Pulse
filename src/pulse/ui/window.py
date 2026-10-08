"""Session-only island placement, dragging and desktop input regions."""
from PySide6.QtCore import QObject, QPoint, QPointF, QRectF, QMargins, QTimer, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QGuiApplication, QPainterPath, QRegion


def island_region(x, y, width, height, radius):
    path = QPainterPath()
    path.addRoundedRect(QRectF(x, y, width, height), radius, radius)
    return QRegion(path.toFillPolygon().toPolygon())


def bounded_anchor(anchor, geometry, width, height):
    """Clamp the visible island, not its transparent window padding (logical pixels)."""
    left, top = geometry.x(), geometry.y()
    x = max(left + width / 2, min(anchor.x(), left + geometry.width() - width / 2))
    y = max(top, min(anchor.y(), top + geometry.height() - height))
    if width > geometry.width():
        x = left + geometry.width() / 2
    return QPointF(x, y)


class WindowIntegration(QObject):
    def __init__(self, window, backend):
        super().__init__(window)
        self.window = window
        self.backend = backend
        self.screen = None
        self.anchor = None
        self.press = None
        self.origin = None
        self.moving = False
        self.layer = None
        self.layer_position = QPoint()
        if backend == 'layer-shell':
            self.layer = next((child for child in window.findChildren(QObject)
                               if child.metaObject().indexOfProperty('margins') >= 0
                               and child.property('scope') == 'pulse'), None)
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(180)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.valueChanged.connect(self.apply_position)
        self.layout_timer = QTimer(self)
        self.layout_timer.setSingleShot(True)
        self.layout_timer.timeout.connect(lambda: self.place(animate=True))
        if backend != "offscreen":
            window.maskChanged.connect(self.update_mask)
        for name in ('openChanged', 'cardWidthChanged', 'cardHeightChanged'):
            if hasattr(window, name):
                getattr(window, name).connect(lambda: self.layout_timer.start(0))
        if hasattr(window, 'moveStarted'):
            window.moveStarted.connect(self.begin_move)
            window.moveRequested.connect(self.move_to)
            window.moveFinished.connect(self.end_move)
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
                pass
        self.screen = screen
        if screen is not None:
            self.screen.availableGeometryChanged.connect(self.place)
            self.place()

    def follow_primary(self, screen):
        if screen is not None and self.anchor is None:
            self.window.setScreen(screen)
            self.bind_screen(screen)

    def begin_move(self, x, y):
        self.animation.stop()
        self.press = QPointF(x, y)
        position = self.current_position()
        self.origin = QPointF(position.x() + self.window.width() / 2, position.y() + 12)

    def move_to(self, x, y):
        if self.press is None:
            return
        self.moving = True
        self.anchor = self.origin + QPointF(x, y) - self.press
        app = QGuiApplication.instance()
        target = app.screenAt(QPoint(round(x), round(y))) if isinstance(app, QGuiApplication) else None
        if target is not None and target is not self.screen:
            self.window.setScreen(target)
            self.bind_screen(target)
        self.place()

    def end_move(self):
        self.press = None
        self.moving = False
        # Remember the actual drop point, not an off-screen pointer overshoot.
        if self.anchor is not None and self.screen is not None:
            self.anchor = self.clamped_anchor()
        self.place()

    def clamped_anchor(self):
        geometry = self.screen.availableGeometry()
        anchor = self.anchor or QPointF(geometry.x() + geometry.width() / 2, geometry.y() + 12)
        opened = self.window.property('open')
        width = float(self.window.property('cardWidth') or 30) if opened else 30
        height = float(self.window.property('cardHeight') or 30) if opened else 30
        return bounded_anchor(anchor, geometry, width, height)

    def place(self, *_, animate=False):
        if self.screen is None:
            return
        anchor = self.clamped_anchor()
        position = QPoint(round(anchor.x() - self.window.width() / 2), round(anchor.y() - 12))
        self.animation.stop()
        if animate and self.anchor is not None and not self.moving and not self.window.property('reducedMotion'):
            self.animation.setStartValue(self.current_position())
            self.animation.setEndValue(position)
            self.animation.start()
        else:
            self.apply_position(position)

    def current_position(self):
        return self.layer_position if self.backend == 'layer-shell' else QPoint(self.window.x(), self.window.y())

    def apply_position(self, position):
        if self.backend == 'layer-shell':
            if self.layer is not None and self.screen is not None:
                geometry = self.screen.geometry()
                self.layer_position = position
                self.window.setProperty('desktopPosition', QPointF(position))
                self.layer.setProperty('margins', QMargins(position.x() - geometry.x(), position.y() - geometry.y(), 0, 0))
                self.window.update()  # Commit margin changes even when idle animation is disabled.
        else:
            self.window.setPosition(position.x(), position.y())
