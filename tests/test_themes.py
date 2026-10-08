import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from pydantic import ValidationError

from pulse.settings import load_settings
from pulse.themes.loader import BUILTINS, load_theme
from pulse.themes.schema import Theme, qml_data


def test_builtin_and_repo_theme_files_match():
    root = Path(__file__).resolve().parents[1]
    for name in BUILTINS:
        theme, error = load_theme(name)
        assert error is None
        example, error = load_theme(str(root / "themes" / name / "theme.json"))
        assert error is None
        assert theme == example
        assert qml_data(theme)["animation"]["fade"] > 0


@pytest.mark.parametrize("data", [
    {"colors": {"background": "red"}}, {"colors": {"title": "#nothex"}},
    {"layout": {"min_width": 380, "max_width": 300}},
    {"layout": {"max_width": 900}}, {"layout": {"padding_y": -1}},
    {"layout": {"min_width": "300"}}, {"layout": {"spacing": True}},
    {"typography": {"body_size": 50}}, {"animation": "execute_script"},
    {"colors": {"script": "anything"}}, {"plugin": "anything"}, {"version": 2},
])
def test_invalid_theme_falls_back_with_diagnostic(tmp_path, data):
    path = tmp_path / "theme.json"
    path.write_text(json.dumps(data))
    theme, error = load_theme(str(path))
    assert theme == Theme()
    assert "Using Default" in error


def test_missing_malformed_and_oversized_themes_fall_back(tmp_path):
    path = tmp_path / "theme.json"
    assert load_theme(str(path))[1]
    for content in ("not json", "[1,2,3]", " " * 65537):
        path.write_text(content)
        assert load_theme(str(path))[1]


def test_custom_theme_relative_to_config_and_partial_defaults(tmp_path):
    (tmp_path / "custom.json").write_text('{"name": "Custom", "colors": {"accent": "#aabbcc"}}')
    config = tmp_path / "config.toml"
    config.write_text('[appearance]\ntheme = "custom.json"\n')
    settings = load_settings(config)
    theme, error = load_theme(settings.theme, base_dir=config.parent)
    assert error is None
    assert theme.colors.accent == "#aabbcc"
    assert theme.layout.min_height == 70


@pytest.mark.parametrize("name", BUILTINS + ("missing-theme.json",))
def test_themed_qml_loads_without_errors(name, tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=str(root / "src"), XDG_CONFIG_HOME=str(tmp_path))
    result = subprocess.run([sys.executable, "-m", "pulse.main", "--backend", "offscreen",
                             "--renderer", "software", "--demo", "--theme", name,
                             "--quit-after", "1.5"],
                            env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    for error in ("ReferenceError", "TypeError", "Unable to assign", "failed to load"):
        assert error not in result.stderr
    if name == "missing-theme.json":
        assert "Using Default" in result.stderr
