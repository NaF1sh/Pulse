"""Pet selection and a small, separate saved preference."""
import json
import os
from pathlib import Path
import tempfile

from PySide6.QtCore import QObject, Property, Signal, Slot

from pulse.settings import default_config_path
from pulse.ui.pet_catalog import PETS, BY_ID


class Pets(QObject):
    changed = Signal()
    failed = Signal(str)

    def __init__(self, parent=None, *, selected=None, preference_path=None):
        super().__init__(parent)
        self.path = Path(preference_path) if preference_path else default_config_path().with_name("pet.json")
        self.selected = "lavender"
        if selected:
            self.selected = selected if selected in BY_ID else "lavender"
        else:
            try:
                saved = json.loads(self.path.read_text())
                if isinstance(saved, dict) and saved.get("pet") in BY_ID:
                    self.selected = saved["pet"]
            except (OSError, ValueError, TypeError):
                pass

    @Property("QVariantList", constant=True)
    def catalog(self):
        return PETS

    @Property("QVariantMap", notify=changed)
    def current(self):
        return BY_ID[self.selected]

    @Slot(str)
    def select(self, id):
        if id not in BY_ID:
            return
        self.selected = id
        self.changed.emit()
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with tempfile.NamedTemporaryFile(mode="w", dir=self.path.parent, delete=False) as stream:
                temporary = stream.name
                json.dump({"pet": id}, stream)
                stream.write("\n")
            os.replace(temporary, self.path)
        except OSError as error:
            self.failed.emit(f"Pet changed, but could not save preference: {error}")
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
