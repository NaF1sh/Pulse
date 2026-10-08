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
import tomllib

ROOT = Path(__file__).resolve().parents[1]
MARKER = 'pulse-windows-installer-v1'
UNINSTALL_KEY = r'Software\Microsoft\Windows\CurrentVersion\Uninstall\PulseIsland'


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


def register_uninstaller(paths, python):
    import winreg
    root = paths['root'].resolve()
    # Use base Python so removal never tries to delete its own interpreter.
    base = Path(subprocess.check_output([python, '-c',
        'import sys; print(sys._base_executable)'], text=True).strip()).resolve()
    if base.is_relative_to(root):
        raise ValueError('The uninstaller requires a Python installation outside the Pulse app folder.')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
        try:
            previous = winreg.QueryValueEx(key, 'InstallLocation')[0]
        except FileNotFoundError:
            previous = str(root)
        if Path(previous).resolve() != root:
            raise ValueError('An uninstall entry already belongs to another Pulse installation.')
        shutil.copyfile(Path(__file__).resolve(), root / 'uninstall.py')
        version = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
        values = dict(DisplayName='Pulse', DisplayVersion=version, Publisher='NaF1sh',
                      DisplayIcon=str(root / 'pulse.ico'), InstallLocation=str(root),
                      UninstallString=subprocess.list2cmdline([str(base), str(root / 'uninstall.py'),
                                                              '--uninstall', '--interactive']),
                      URLInfoAbout='https://github.com/NaF1sh/Pulse')
        for name, value in values.items():
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        for name in ('NoModify', 'NoRepair'):
            winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, 1)


def unregister_uninstaller(paths):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
            location = winreg.QueryValueEx(key, 'InstallLocation')[0]
        if Path(location).resolve() == paths['root'].resolve():
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
    except FileNotFoundError:
        pass  # Older previews did not register an uninstall entry.


def ensure_not_running(paths):
    # Inspect executable paths, never terminate unrelated Python apps or task processes.
    script = ('$root=$env:PULSE_APP_ROOT;'
              '$running=@(Get-Process | Where-Object { $_.Path -and '
              '$_.Path.StartsWith($root,[System.StringComparison]::OrdinalIgnoreCase) });'
              'if ($running.Count) { Write-Output "running" }')
    env = dict(os.environ, PULSE_APP_ROOT=str(paths['root'].resolve()) + os.sep)
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                            env=env, capture_output=True, text=True, check=True, timeout=15)
    if result.stdout.strip():
        raise ValueError('Pulse is still running. Right-click the island, choose Quit Pulse in Settings, '
                         'and let any Pulse task commands finish. Then run uninstall again')


def install(paths, python):
    root = paths['root']
    owned = manifest_at(root)
    if root.exists() and not owned:
        raise ValueError(f'Refusing to replace an existing non-Pulse folder: {root}')
    if paths['shortcut'].exists() and not owned:
        raise ValueError(f'Refusing to replace an existing shortcut: {paths["shortcut"]}')
    if owned:
        ensure_not_running(paths)
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / 'install.json'
    manifest.write_text(json.dumps(owned or {'installer': MARKER}), encoding='utf-8')
    subprocess.run([python, '-m', 'venv', str(root / 'venv')], check=True)
    interpreter = root / 'venv/Scripts/python.exe'
    subprocess.run([str(interpreter), '-m', 'pip', 'install', str(ROOT)], check=True)
    shutil.copyfile(ROOT / 'assets/pulse.ico', root / 'pulse.ico')
    paths['shortcut'].parent.mkdir(parents=True, exist_ok=True)
    shortcut(paths)
    manifest.write_text(json.dumps({'installer': MARKER,
                        'shortcut_sha256': hashlib.sha256(paths['shortcut'].read_bytes()).hexdigest()}), encoding='utf-8')
    register_uninstaller(paths, python)
    print('Installed. Open Pulse from the Start menu.')
    print('Uninstall through Windows Settings > Apps > Installed apps > Pulse.')
    print(f'Task CLI: {root / "venv/Scripts/pulse.exe"}')
    print('No administrator access or system PATH changes are required.')


def uninstall(paths):
    owned = manifest_at(paths['root'])
    if owned is None:
        raise ValueError('No installer-owned Windows Pulse installation was found.')
    ensure_not_running(paths)
    root = paths['root']
    # Keep ownership and the uninstall entry available if Windows refuses a file.
    for entry in root.iterdir():
        if entry.name in ('install.json', 'uninstall.py'):
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()
    link = paths['shortcut']
    if link.exists() and hashlib.sha256(link.read_bytes()).hexdigest() == owned.get('shortcut_sha256'):
        link.unlink()
    unregister_uninstaller(paths)
    (root / 'uninstall.py').unlink(missing_ok=True)
    (root / 'install.json').unlink()
    root.rmdir()
    print('Uninstalled. Preferences, backgrounds, and task records were kept.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uninstall', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--interactive', action='store_true', help='keep the result visible when launched from Installed Apps')
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
        print(f'Pulse error: {error}', file=sys.stderr)
        if args.interactive:
            input('Press Enter to close this window…')
        return 1
    if args.interactive:
        input('Press Enter to close this window…')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
