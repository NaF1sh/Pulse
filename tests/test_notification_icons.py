from PySide6.QtCore import QUrl
from PySide6.QtGui import QImage

from pulse.core.models import Notification
from pulse.sources.dbus_observer import NotificationDecoder
from pulse.ui.interactions import DesktopApps
from pulse.ui.notification_icons import NotificationIcons, raw_image_url
from test_observer import call


def test_browser_image_hint_is_preserved():
    message = call()
    message['payload']['data'][2] = 'firefox'
    message['payload']['data'][6]['image-data'] = {
        'type': '(iiibiiay)', 'data': [1, 1, 4, True, 8, 4, [255, 0, 0, 255]]}
    item = NotificationDecoder().decode(message)
    assert item.icon == 'firefox'
    assert item.icon_image.startswith('data:image/png;base64,')
    assert NotificationIcons().resolve(item) == item.icon_image


def test_malformed_image_data_is_ignored():
    for data in (None, [], [1, 1, 4, True, 8, 4, [256, 0, 0, 0]],
                 [100000, 1, 4, True, 8, 4, []], [1, 1, 1, True, 8, 4, [0]]):
        assert raw_image_url(data) == ''


def test_local_and_desktop_entry_icons(tmp_path):
    image = QImage(4, 4, QImage.Format_RGBA8888)
    image.fill(0xff123456)
    icon = tmp_path / 'site.png'
    assert image.save(str(icon))
    resolver = NotificationIcons()
    assert resolver.load(QUrl.fromLocalFile(str(icon)).toString()).startswith('data:image/png;base64,')
    assert resolver.load('https://example.com/favicon.ico') == ''
    (tmp_path / 'chat.desktop').write_text(
        f'[Desktop Entry]\nType=Application\nName=Chat\nExec=chat\nIcon={icon}\n')
    resolver.apps = DesktopApps([tmp_path])
    assert resolver.resolve(Notification(1, 'Chat', 'Hello')).startswith('data:image/png;base64,')
    assert resolver.resolve(Notification(2, 'Unknown', 'Hello')) == ''
