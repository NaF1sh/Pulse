"""Bounded local image import and a rounded background that works with software Qt."""
import hashlib
from pathlib import Path
import re
import secrets

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Property, QRectF, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QImage, QImageReader, QLinearGradient, QPainter, QPainterPath
from PySide6.QtQml import qmlRegisterType
from PySide6.QtQuick import QQuickPaintedItem

COLORS = ['#594a86', '#b8d9dc', '#e8b9a9', '#263c48', '#d4c4e5', '#375946', '#daa65d', '#6e334b']
MODES = ('theme', 'solid', 'random', 'image')


def valid_color(value):
    return isinstance(value, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', value) is not None


def luminance(color):
    rgb = QColor(color)
    values = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
              for value in (rgb.redF(), rgb.greenF(), rgb.blueF())]
    return sum(a * b for a, b in zip(values, (.2126, .7152, .0722)))


def contrast(first, second):
    a, b = sorted((luminance(first), luminance(second)))
    return (b + .05) / (a + .05)


def readable_colors(background):
    light = contrast(background, '#ffffff') >= contrast(background, '#000000')
    title = '#ffffff' if light else '#000000'
    body = '#ededf2' if light else '#30303a'
    accent = '#ddd0ff' if light else '#423076'
    return dict(background=background, title=title,
                body=body if contrast(background, body) >= 4.5 else title,
                muted=body if contrast(background, body) >= 4.5 else title,
                accent=accent if contrast(background, accent) >= 4.5 else title,
                progress=title, border='#807b90' if light else '#8a8692')


def random_color(previous=''):
    return secrets.choice([color for color in COLORS if color != previous])


def import_image(value, directory):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]
    if value.startswith('~/'):
        value = str(Path(value).expanduser())
    url = QUrl(value)
    if Path(value).is_absolute():
        path = Path(value)
    elif url.isLocalFile() and not url.host():
        path = Path(url.toLocalFile())
    else:
        raise ValueError('Choose an image saved on this computer.')
    try:
        if path.is_dir():
            raise ValueError('This is a folder. Paste the full path including the image filename.')
        if not path.is_file():
            raise ValueError('Image not found. Check the path and filename.')
        if path.stat().st_size > 32 * 1024 * 1024:
            raise ValueError('Choose an image smaller than 32 MB.')
    except OSError:
        raise ValueError('This image is no longer available.') from None
    reader = QImageReader(str(path))
    if bytes(reader.format()).lower() not in (b'png', b'jpeg', b'jpg', b'webp'):
        raise ValueError('Choose a PNG, JPEG, or WebP image.')
    size = reader.size()
    if not size.isValid() or size.width() * size.height() > 24_000_000:
        raise ValueError('Choose an image up to 24 megapixels.')
    reader.setAutoTransform(True)
    if max(size.width(), size.height()) > 1600:
        reader.setScaledSize(size.scaled(1600, 1600, Qt.KeepAspectRatio))
    image = reader.read()
    if image.isNull():
        raise ValueError('This image could not be opened. Try another file.')
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    if not image.save(buffer, 'PNG'):
        raise ValueError('Could not prepare the image.')
    filename = hashlib.sha256(bytes(data)).hexdigest() + '.png'
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    from PySide6.QtCore import QSaveFile
    output = QSaveFile(str(directory / filename))
    if not output.open(QIODevice.WriteOnly) or output.write(data) != data.size() or not output.commit():
        raise OSError('Could not save the background image.')
    (directory / filename).chmod(0o600)
    return filename


class BarBackground(QQuickPaintedItem):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor('#101014')
        self._source = ''
        self._radius = 18.0
        self._dim = .2
        self._position = .5
        self.image = QImage()
        self.setAntialiasing(True)

    def set_color(self, value):
        if value != self._color:
            self._color = QColor(value)
            self.changed.emit()
            self.update()

    backgroundColor = Property(QColor, lambda self: self._color, set_color, notify=changed)

    def set_source(self, value):
        if value != self._source:
            self._source = value
            url = QUrl(value)
            self.image = QImage(url.toLocalFile()) if url.isLocalFile() and not url.host() else QImage()
            self.changed.emit()
            self.update()

    imageSource = Property(str, lambda self: self._source, set_source, notify=changed)

    def set_radius(self, value):
        self._radius = max(0, value)
        self.changed.emit()
        self.update()

    cornerRadius = Property(float, lambda self: self._radius, set_radius, notify=changed)

    def set_dim(self, value):
        self._dim = max(0, min(.8, value))
        self.changed.emit()
        self.update()

    dim = Property(float, lambda self: self._dim, set_dim, notify=changed)

    def set_position(self, value):
        self._position = max(0, min(1, value))
        self.changed.emit()
        self.update()

    imagePosition = Property(float, lambda self: self._position, set_position, notify=changed)

    def paint(self, painter):
        rect = self.boundingRect()
        if rect.isEmpty():
            return
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        radius = min(self._radius, rect.width() / 2, rect.height() / 2)
        path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(path)
        painter.fillRect(rect, self._color)
        if not self.image.isNull():
            scale = max(rect.width() / self.image.width(), rect.height() / self.image.height())
            w, h = rect.width() / scale, rect.height() / scale
            crop = QRectF((self.image.width() - w) / 2,
                          (self.image.height() - h) * self._position, w, h)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawImage(rect, self.image, crop)
            painter.fillRect(rect, QColor.fromRgbF(0, 0, 0, self._dim))
            # Keep the picture visible at the edges and text legible over bright photos.
            shade = QLinearGradient(0, 0, rect.width(), 0)
            shade.setColorAt(0, QColor.fromRgbF(0, 0, 0, .12))
            shade.setColorAt(.18, QColor.fromRgbF(0, 0, 0, .68))
            shade.setColorAt(1, QColor.fromRgbF(0, 0, 0, .68))
            painter.fillRect(rect, shade)


_registered = False


def register_background():
    global _registered
    if not _registered:
        qmlRegisterType(BarBackground, 'Pulse.Appearance', 1, 0, 'BarBackground')
        _registered = True
