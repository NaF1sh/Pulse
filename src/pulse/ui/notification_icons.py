"""Local notification images and installed application icons for QML."""
import base64
import configparser
from pathlib import Path
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QUrl, Qt
from PySide6.QtGui import QIcon, QImage
from pulse.ui.interactions import DesktopApps


def image_url(image):
    if image.isNull():
        return ''
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    if not image.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation).save(buffer, 'PNG'):
        return ''
    return 'data:image/png;base64,' + base64.b64encode(bytes(data)).decode('ascii')


def raw_image_url(value):
    if not isinstance(value, (list, tuple)) or len(value) != 7:
        return ''
    width, height, stride, alpha, bits, channels, pixels = value
    if (any(type(n) is not int for n in (width, height, stride, bits, channels))
            or type(alpha) is not bool or not 0 < width <= 1024 or not 0 < height <= 1024
            or bits != 8 or channels != (4 if alpha else 3)
            or not width * channels <= stride <= 8192
            or not isinstance(pixels, (list, bytes, bytearray))
            or len(pixels) != stride * height or len(pixels) > 4 * 1024 * 1024):
        return ''
    try:
        data = bytes(pixels)
    except (ValueError, TypeError):
        return ''
    return image_url(QImage(data, width, height, stride,
                           QImage.Format_RGBA8888 if alpha else QImage.Format_RGB888))


class NotificationIcons:
    def __init__(self):
        self.apps = None
        self.cache = {}

    def load(self, source):
        if not source or len(source) > 4096:
            return ''
        url = QUrl(source)
        path = url.toLocalFile() if url.isLocalFile() else source
        if Path(path).is_absolute():
            try:
                if Path(path).stat().st_size > 4 * 1024 * 1024:
                    return ''
            except OSError:
                return ''
            return image_url(QImage(path))
        if url.scheme() or '/' in source:
            return ''
        return image_url(QIcon.fromTheme(source).pixmap(64, 64).toImage())

    def resolve(self, item):
        if item.icon_image:
            return item.icon_image
        key = (item.icon, item.desktop_entry, item.app)
        if key in self.cache:
            return self.cache[key]
        result = self.load(item.icon)
        if not result:
            if self.apps is None:
                self.apps = DesktopApps()
            path = self.apps.resolve(item.desktop_entry, item.app)
            if path:
                parser = configparser.ConfigParser(interpolation=None, strict=False)
                try:
                    parser.read_string(path.read_text())
                    result = self.load(parser['Desktop Entry'].get('Icon', ''))
                except (OSError, UnicodeError, configparser.Error, KeyError):
                    pass
        if len(self.cache) >= 256:
            self.cache.clear()
        self.cache[key] = result
        return result
