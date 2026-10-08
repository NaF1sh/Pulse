from pathlib import Path
import pytest
from PySide6.QtGui import QColor, QImage
from PySide6.QtCore import QUrl
from pulse.ui.backgrounds import COLORS, contrast, readable_colors, random_color, import_image
from test_preferences import make_preferences
from pulse.core.models import Notification


@pytest.mark.parametrize('color', COLORS + ['#ffffff', '#000000', '#777777'])
def test_readable_text_on_custom_colors(color):
    colors = readable_colors(color)
    for name in ('title', 'body', 'accent'):
        assert contrast(color, colors[name]) >= 4.5


def test_import_survives_original_removal_and_persists(tmp_path):
    original = tmp_path / 'wallpaper with spaces.png'
    image = QImage(2000, 1000, QImage.Format_RGB32)
    image.fill(QColor('#e8b9a9'))
    assert image.save(str(original))
    controller, prefs = make_preferences(tmp_path / 'config')
    prefs.importBackground(QUrl.fromLocalFile(str(original)).toString())
    assert prefs.backgroundMode == 'image'
    original.unlink()
    _, restored = make_preferences(tmp_path / 'config')
    path = Path(QUrl(restored.background['image']).toLocalFile())
    assert QImage(str(path)).size().width() == 1600
    assert path.stat().st_mode & 0o777 == 0o600
    restored.importBackground('https://example.com/wallpaper.png')
    assert restored.backgroundError
    assert restored.background['image'] == prefs.background['image']
    restored.setBackgroundMode('theme')
    assert not restored.background['custom']


def test_invalid_image_preserves_old_color_and_random_only_changes_on_new_card(tmp_path):
    controller, prefs = make_preferences(tmp_path)
    prefs.setBackgroundColor('#b8d9dc')
    invalid = tmp_path / 'bad.png'
    invalid.write_text('not an image')
    prefs.importBackground(str(invalid))
    assert prefs.backgroundMode == 'solid'
    prefs.setBackgroundColor('invalid')
    assert prefs.backgroundColor == '#b8d9dc'
    prefs.setBackgroundMode('random')
    controller.submit(Notification(1, 'App', 'First'))
    first = prefs.background['color']
    controller.submit(Notification(1, 'App', 'Updated'))
    assert prefs.background['color'] == first
    controller.dismiss()
    controller.submit(Notification(2, 'App', 'Second'))
    assert prefs.background['color'] != first


def test_untrusted_background_preferences_are_filtered(tmp_path):
    _, prefs = make_preferences(tmp_path)
    prefs.path.write_text('{"background_image":"../../outside.png", "background_dim":2, "background_position":-1, "background_color":"red", "background_mode":[]}')
    assert prefs.read(prefs.path) == {}
