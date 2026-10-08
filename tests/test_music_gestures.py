import os
from pathlib import Path
import subprocess
import sys


def test_double_click_and_panel_toggle_music(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = '''
from pathlib import Path
from PySide6.QtCore import QTimer, QUrl, QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from pulse.core.models import Notification, Kind
from pulse.ui.controller import Controller
from pulse.ui.pets import Pets
from pulse.themes.schema import Theme, qml_data
app = QGuiApplication([])
engine = QQmlApplicationEngine()
controller = Controller(engine)
pets = Pets(engine)
engine.rootContext().setContextProperty("pulseController", controller)
engine.rootContext().setContextProperty("pulsePets", pets)
engine.rootContext().setContextProperty("pulseTheme", qml_data(Theme()))
controller.set_media(Notification(-2000001, "Music", "Track", "Artist", timeout=0, kind=Kind.MEDIA, status="Playing"))
engine.load(QUrl.fromLocalFile(str(Path("src/pulse/ui/qml/Island.qml").resolve())))
window = engine.rootObjects()[0]
window.setProperty("reducedMotion", True)
window.show()
result = [1]
def check():
    try:
        QTest.mouseDClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(210, 45))
        assert not controller.musicVisible, "Double-click should hide music"
        QTest.qWait(180)
        QTest.mouseDClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(210, 27))
        assert controller.musicVisible, "Double-click pet should restore music"
        QTest.qWait(180)
        QTest.mouseClick(window, Qt.RightButton, Qt.NoModifier, QPoint(210, 45))
        picker = next(item for item in app.topLevelWindows() if "choose your pet" in item.title())
        assert picker.isVisible()
        QTest.mouseClick(picker, Qt.LeftButton, Qt.NoModifier, QPoint(87, picker.height() - 32))
        assert not controller.musicVisible, "Panel should hide music"
        assert not picker.isVisible()
        result[0] = 0
    finally:
        app.quit()
QTimer.singleShot(500, check)
QTimer.singleShot(4000, app.quit)
app.exec()
raise SystemExit(result[0])
'''
    env = dict(os.environ, PYTHONPATH=str(root / "src"), XDG_CONFIG_HOME=str(tmp_path),
               QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software")
    result = subprocess.run([sys.executable, "-c", script], cwd=root, env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    for error in ("ReferenceError", "TypeError", "Unable to assign", "AssertionError"):
        assert error not in result.stderr
