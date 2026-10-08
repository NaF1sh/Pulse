#!/usr/bin/env python3
"""Per-user Windows installer. Keeps Linux installation and user data separate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MARKER = 'pulse-windows-installer-v1'


def locations():
    local = Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData/Local')
    roaming = Path(os.environ.get('APPDATA') or Path.home() / 'AppData/Roaming')
    return {'root': local / 'Pulse/app',
            'shortcut': roaming / 'Microsoft/Windows/Start Menu/Programs/Pulse.lnk'}


def manifest_at(root):
    try:
        value = json.loads((root / 'install.json').read_text(encoding='utf-8'))
        return value if value.get('installer') == MARKER else None
    except (OSError, ValueError, AttributeError):
        return None


def shortcut(paths):
    # Values travel as environment data; user-controlled paths never enter PowerShell source.
    script = ('$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:PULSE_SHORTCUT);'
              '$s.TargetPath=$env:PULSE_TARGET;$s.WorkingDirectory=$env:PULSE_WORKDIR;'
              '$s.IconLocation=$env:PULSE_ICON;$s.Description="Pulse floating island";$s.Save()')
    env = dict(os.environ, PULSE_SHORTCUT=str(paths['shortcut']),
               PULSE_TARGET=str(paths['root'] / 'venv/Scripts/pulse-island.exe'),
               PULSE_WORKDIR=str(paths['root']), PULSE_ICON=str(paths['root'] / 'pulse.ico'))
    subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                   env=env, check=True)


def install(paths, python):
    root = paths['root']
    owned = manifest_at(root)
    if root.exists() and not owned:
        raise ValueError(f'Refusing to replace an existing non-Pulse folder: {root}')
    if paths['shortcut'].exists() and not owned:
        raise ValueError(f'Refusing to replace an existing shortcut: {paths["shortcut"]}')
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / 'install.json'
    manifest.write_text(json.dumps({'installer': MARKER}), encoding='utf-8')
    subprocess.run([python, '-m', 'venv', str(root / 'venv')], check=True)
    interpreter = root / 'venv/Scripts/python.exe'
    subprocess.run([str(interpreter), '-m', 'pip', 'install', str(ROOT)], check=True)
    shutil.copyfile(ROOT / 'assets/pulse.ico', root / 'pulse.ico')
    paths['shortcut'].parent.mkdir(parents=True, exist_ok=True)
    shortcut(paths)
    manifest.write_text(json.dumps({'installer': MARKER,
                        'shortcut_sha256': hashlib.sha256(paths['shortcut'].read_bytes()).hexdigest()}), encoding='utf-8')
    print('Installed. Open Pulse from the Start menu.')
    print(f'Task CLI: {root / "venv/Scripts/pulse.exe"}')
    print('No administrator access or system PATH changes are required.')


def uninstall(paths):
    owned = manifest_at(paths['root'])
    if owned is None:
        raise ValueError('No installer-owned Windows Pulse installation was found.')
    link = paths['shortcut']
    if link.exists() and hashlib.sha256(link.read_bytes()).hexdigest() == owned.get('shortcut_sha256'):
        link.unlink()
    shutil.rmtree(paths['root'])
    print('Uninstalled. Preferences, backgrounds, and task records were kept.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uninstall', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--python', default=sys.executable)
    args = parser.parse_args(argv)
    paths = locations()
    if args.dry_run:
        print('Uninstall' if args.uninstall else 'Install')
        for key, value in paths.items():
            print(f'{key}: {value}')
        return 0
    if sys.platform != 'win32':
        parser.error('Use install.sh on Linux; this installer is for Windows.')
    try:
        if args.uninstall:
            uninstall(paths)
        else:
            version = subprocess.check_output([args.python, '-c', 'import sys; print(sys.version_info >= (3,12))'], text=True).strip()
            if version != 'True':
                raise ValueError('Install Python 3.12 or newer first.')
            install(paths, args.python)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'Install error: {error}. Close Pulse before updating or uninstalling.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
