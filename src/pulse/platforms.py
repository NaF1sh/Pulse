"""Platform defaults; explicit XDG overrides remain useful for isolated runs."""
import os
from pathlib import Path
import sys


def is_windows():
    return sys.platform == 'win32'


def config_dir():
    if os.environ.get('XDG_CONFIG_HOME'):
        return Path(os.environ['XDG_CONFIG_HOME']) / 'pulse'
    if is_windows():
        return Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData/Local') / 'Pulse/config'
    return Path.home() / '.config/pulse'


def data_dir():
    if os.environ.get('XDG_DATA_HOME'):
        return Path(os.environ['XDG_DATA_HOME']) / 'pulse'
    if is_windows():
        return Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData/Local') / 'Pulse/data'
    return Path.home() / '.local/share/pulse'


def runtime_dir():
    if os.environ.get('XDG_RUNTIME_DIR'):
        return Path(os.environ['XDG_RUNTIME_DIR'])
    if is_windows():
        return Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData/Local') / 'Pulse/runtime'
    return Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'pulse'
