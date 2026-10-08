"""Read and validate startup settings without writing user configuration."""
from dataclasses import dataclass, field
import math
import os
from pathlib import Path
import tomllib

from pulse.core.rules import Rules


@dataclass(frozen=True)
class Settings:
    rules: Rules = field(default_factory=Rules)
    default_timeout: float = 5.0
    reduced_motion: bool = False
    theme: str = "default"


def default_config_path():
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "pulse" / "config.toml"


def load_settings(path, *, required=False):
    try:
        with Path(path).open("rb") as source:
            data = tomllib.load(source)
    except FileNotFoundError:
        if required:
            raise ValueError(f"Settings file does not exist: {path}") from None
        return Settings()
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"Cannot read settings {path}: {error}") from error
    unknown = data.keys() - {"notifications", "appearance"}
    if unknown:
        raise ValueError(f"Unknown settings sections: {', '.join(sorted(unknown))}")
    notifications = data.get("notifications", {})
    appearance = data.get("appearance", {})
    if not isinstance(notifications, dict) or not isinstance(appearance, dict):
        raise ValueError("notifications and appearance must be TOML tables")
    unknown = notifications.keys() - {"dnd", "allow_critical", "muted_apps", "default_timeout"}
    unknown |= appearance.keys() - {"reduced_motion", "theme"}
    if unknown:
        raise ValueError(f"Unknown settings: {', '.join(sorted(unknown))}")
    dnd = notifications.get("dnd", False)
    critical = notifications.get("allow_critical", True)
    reduced = appearance.get("reduced_motion", False)
    if any(type(value) is not bool for value in (dnd, critical, reduced)):
        raise ValueError("dnd, allow_critical and reduced_motion must be true or false")
    muted = notifications.get("muted_apps", [])
    if not isinstance(muted, list) or any(not isinstance(name, str) or not name.strip() for name in muted):
        raise ValueError("muted_apps must be an array of nonempty app names")
    timeout = notifications.get("default_timeout", 5.0)
    if type(timeout) not in (float, int) or not math.isfinite(timeout) or not 0 < timeout <= 3600:
        raise ValueError("default_timeout must be a number greater than 0 and at most 3600 seconds")
    theme = appearance.get("theme", "default")
    if not isinstance(theme, str) or not theme.strip():
        raise ValueError("theme must be a nonempty built-in name or JSON file path")
    return Settings(Rules(dnd, critical, tuple(name.strip() for name in muted)), float(timeout), reduced, theme)
