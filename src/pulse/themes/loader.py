from importlib.resources import files
from pathlib import Path

from pydantic import ValidationError

from pulse.themes.schema import Theme

BUILTINS = ("default", "ocean", "rose")


def load_theme(selection="default", *, base_dir=None):
    """Return (validated theme, optional diagnostic), always falling back safely."""
    try:
        if selection in BUILTINS:
            source = files("pulse.themes").joinpath("presets", selection + ".json")
        else:
            source = Path(selection).expanduser()
            if base_dir is not None and not source.is_absolute():
                source = Path(base_dir) / source
        with source.open("rb") as stream:
            data = stream.read(65537)
        if len(data) > 65536:
            raise ValueError("theme must be at most 64 KiB")
        return Theme.model_validate_json(data), None
    except (OSError, ValueError, ValidationError) as error:
        if isinstance(error, ValidationError):
            details = "; ".join(f"{'.'.join(map(str, item['loc'])) or 'theme'}: {item['msg']}"
                                for item in error.errors(include_url=False)[:3])
        else:
            details = str(error)
        return Theme(), f"Cannot load theme {selection!r}: {details}. Using Default."
