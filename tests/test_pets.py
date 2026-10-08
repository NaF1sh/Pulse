import json
import os
from pathlib import Path
import subprocess
import sys

from PySide6.QtCore import QCoreApplication

from pulse.ui.pet_catalog import PETS, BY_ID
from pulse.ui.pets import Pets


def test_all_reference_choices_have_unique_ids():
    assert len(PETS) == len(BY_ID) == 38
    assert len([pet for pet in PETS if pet["species"] != "round"]) == 19
    assert all(pet["name"] and pet["coat"].startswith("#") for pet in PETS)


def test_selection_is_saved_and_restored(tmp_path):
    app = QCoreApplication.instance() or QCoreApplication([])
    path = tmp_path / "pulse" / "pet.json"
    pets = Pets(preference_path=path)
    changes = []
    pets.changed.connect(lambda: changes.append(pets.current["id"]))
    pets.select("lavender-cat")
    assert changes == ["lavender-cat"]
    assert json.loads(path.read_text()) == {"pet": "lavender-cat"}
    assert Pets(preference_path=path).current["id"] == "lavender-cat"
    assert path.stat().st_mode & 0o777 == 0o600
    pets.select("not-a-pet")
    assert pets.current["id"] == "lavender-cat"


def test_cli_override_does_not_overwrite_saved_choice(tmp_path):
    app = QCoreApplication.instance() or QCoreApplication([])
    path = tmp_path / "pet.json"
    path.write_text('{"pet": "panda"}')
    pets = Pets(selected="frog", preference_path=path)
    assert pets.current["id"] == "frog"
    assert json.loads(path.read_text())["pet"] == "panda"


def test_bad_preferences_fall_back_to_lavender(tmp_path):
    app = QCoreApplication.instance() or QCoreApplication([])
    path = tmp_path / "pet.json"
    for data in ('not json', '[]', '{"pet": "missing"}', '{"pet": []}'):
        path.write_text(data)
        assert Pets(preference_path=path).current["id"] == "lavender"


def test_selection_survives_save_failure(tmp_path):
    app = QCoreApplication.instance() or QCoreApplication([])
    blocker = tmp_path / "file"
    blocker.write_text("not a directory")
    pets = Pets(preference_path=blocker / "pet.json")
    errors = []
    pets.failed.connect(errors.append)
    pets.select("frog")
    assert pets.current["id"] == "frog"
    assert len(errors) == 1


def test_picker_renders_all_pets_and_click_selects(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = '''
from pathlib import Path
from PySide6.QtCore import QTimer, QUrl, QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from pulse.ui.pets import Pets
app = QGuiApplication([])
engine = QQmlApplicationEngine()
pets = Pets(engine)
engine.rootContext().setContextProperty("pulsePets", pets)
engine.load(QUrl.fromLocalFile(str(Path("src/pulse/ui/qml/PetPicker.qml").resolve())))
window = engine.rootObjects()[0]
window.setHeight(950)
window.show()
result = [1]
def check():
    try:
        assert not window.grabWindow().isNull()
        # Second tile in the first row is Panda.
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(185, 130))
        assert pets.current["id"] == "panda"
        assert not window.isVisible()
        result[0] = 0
    finally:
        app.quit()
QTimer.singleShot(700, check)
QTimer.singleShot(3000, app.quit)
app.exec()
raise SystemExit(result[0])
'''
    env = dict(os.environ, PYTHONPATH=str(root / "src"), XDG_CONFIG_HOME=str(tmp_path),
               QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software")
    result = subprocess.run([sys.executable, "-c", script], cwd=root, env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    for error in ("ReferenceError", "TypeError", "Unable to assign", "Error"):
        assert error not in result.stderr
    assert json.loads((tmp_path / "pulse" / "pet.json").read_text())["pet"] == "panda"
