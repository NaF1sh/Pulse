import os
from pathlib import Path
import subprocess
import sys

import pytest

from pulse.sources.artwork import artwork_url


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?v=abcdefghijk",
    "https://music.youtube.com/watch?v=abcdefghijk&list=123",
    "https://youtu.be/abcdefghijk?t=30", "https://youtube.com/shorts/abcdefghijk",
    "https://www.youtube.com/embed/abcdefghijk",
])
def test_youtube_thumbnail_from_known_video_url(url):
    assert artwork_url(None, url) == "https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg"


def test_player_image_wins_and_local_paths_are_normalized():
    cover = "https://i.scdn.co/image/example"
    assert artwork_url(cover, "https://youtu.be/abcdefghijk") == cover
    assert artwork_url("/tmp/album cover.png") == "file:///tmp/album%20cover.png"


@pytest.mark.parametrize("url", [
    "https://youtube.com.evil.example/watch?v=abcdefghijk", "https://youtu.be/too-short",
    "https://youtube.com/playlist?list=123", "https://open.spotify.com/track/123",
    "javascript:alert(1)", "https://user:pass@youtube.com/watch?v=abcdefghijk",
])
def test_missing_or_unusable_links_do_not_invent_a_cover(url):
    assert artwork_url(None, url) == ""


def test_album_image_is_actually_rendered_in_music_card(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = '''
from pathlib import Path
from PySide6.QtCore import QTimer, QUrl, QObject
from PySide6.QtGui import QGuiApplication, QImage, QColor
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine
from pulse.core.models import Notification, Kind
from pulse.ui.controller import Controller
from pulse.ui.pets import Pets
from pulse.themes.schema import Theme, qml_data
import os
app = QGuiApplication([])
path = Path(os.environ["XDG_CONFIG_HOME"]) / "cover.png"
image = QImage(40, 40, QImage.Format_ARGB32)
image.fill(QColor("#19efb2"))
assert image.save(str(path))
engine = QQmlApplicationEngine()
controller = Controller(engine)
pets = Pets(engine)
engine.rootContext().setContextProperty("pulseController", controller)
engine.rootContext().setContextProperty("pulsePets", pets)
engine.rootContext().setContextProperty("pulseTheme", qml_data(Theme()))
controller.set_media(Notification(-2000001, "Music", "Track", "Artist", timeout=0,
    kind=Kind.MEDIA, status="Playing", artwork=path.as_uri()))
engine.load(QUrl.fromLocalFile(str(Path("src/pulse/ui/qml/Island.qml").resolve())))
window = engine.rootObjects()[0]
window.setProperty("reducedMotion", True)
window.show()
result = [1]
def check():
    try:
        cover = window.findChild(QObject, "albumCover")
        assert cover is not None
        assert cover.property("loaded"), "Cover must finish loading"
        pixel = window.grabWindow().pixelColor(70, 38)
        assert pixel.green() > 220 and pixel.red() < 50, "Actual cover pixels must be visible"
        result[0] = 0
    finally:
        app.quit()
QTimer.singleShot(900, check)
QTimer.singleShot(3000, app.quit)
app.exec()
raise SystemExit(result[0])
'''
    env = dict(os.environ, PYTHONPATH=str(root / "src"), XDG_CONFIG_HOME=str(tmp_path),
               QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software")
    result = subprocess.run([sys.executable, "-c", script], cwd=root, env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    for error in ("ReferenceError", "TypeError", "AssertionError"):
        assert error not in result.stderr
