#!/usr/bin/env python3
"""Install Pulse for the current user without sudo or modifying desktop settings."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MARKER = 'pulse-island-installer-v1'


def locations():
    data = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share').absolute()
    binary = Path(os.environ.get('PULSE_BIN_DIR') or Path.home() / '.local/bin').absolute()
    return {'root': data / 'pulse/app', 'launcher': binary / 'pulse',
            'desktop': data / 'applications/io.github.NaF1sh.Pulse.desktop',
            'icon': data / 'icons/hicolor/scalable/apps/io.github.NaF1sh.Pulse.svg'}


def launcher_text(python):
    return ('#!/bin/sh\n# ' + MARKER + '\n'
            'if [ "$#" -eq 0 ]; then set -- --observe; fi\n'
            f'exec {shlex.quote(str(python))} -m pulse.main "$@"\n')


def desktop_text(launcher):
    # Desktop Exec quoting has its own grammar; it is not shell syntax.
    escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%')
    return f'''[Desktop Entry]
Type=Application
Name=Pulse
Comment=A quiet companion for notifications, music, and volume
Exec="{escaped}" --observe
Icon=io.github.NaF1sh.Pulse
Terminal=false
Categories=Utility;
Keywords=notifications;music;companion;
StartupNotify=false
X-Pulse-Installer={MARKER}
Actions=Settings;

[Desktop Action Settings]
Name=Settings
Exec="{escaped}" --observe --settings
'''


def owned(path):
    try:
        return MARKER in path.read_text()
    except (OSError, UnicodeError):
        return False


def install(paths, *, python, system_packages=False):
    root = paths['root']
    manifest = root / 'install.json'
    if root.exists() and not owned(manifest):
        raise ValueError(f'{root} already exists and was not created by this installer')
    for key in ('launcher', 'desktop'):
        if paths[key].exists() and not owned(paths[key]):
            raise ValueError(f'Refusing to replace an existing file: {paths[key]}')
    if paths['icon'].exists() and not owned(manifest):
        raise ValueError(f'Refusing to replace an existing icon: {paths["icon"]}')
    root.mkdir(parents=True, exist_ok=True)
    # Track ownership before dependency installation so interrupted installs can be retried.
    manifest.write_text(json.dumps({'installer': MARKER}))
    env = root / 'venv'
    command = [python, '-m', 'venv']
    if system_packages:
        command.append('--system-site-packages')
    subprocess.run([*command, str(env)], check=True)
    interpreter = env / 'bin/python'
    pip = [str(interpreter), '-m', 'pip', 'install']
    if system_packages:
        # Offline development route: dependencies and build tools must already be available.
        pip += ['--no-deps', '--no-build-isolation']
    subprocess.run([*pip, str(ROOT)], check=True)
    for key in ('launcher', 'desktop', 'icon'):
        paths[key].parent.mkdir(parents=True, exist_ok=True)
    paths['launcher'].write_text(launcher_text(interpreter))
    paths['launcher'].chmod(0o755)
    paths['desktop'].write_text(desktop_text(paths['launcher']))
    shutil.copyfile(ROOT / 'assets/pulse.svg', paths['icon'])
    manifest.write_text(json.dumps({'installer': MARKER, 'paths': {key: str(value) for key, value in paths.items()}}))
    if shutil.which('update-desktop-database'):
        subprocess.run(['update-desktop-database', str(paths['desktop'].parent)], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f'Installed. Open Pulse from your app menu, or run {paths["launcher"]}')
    print('Run this installer again to update. Login startup is not enabled automatically.')


def uninstall(paths):
    root = paths['root']
    manifest = root / 'install.json'
    if not owned(manifest):
        raise ValueError(f'No installer-owned Pulse installation found at {root}')
    installed = json.loads(manifest.read_text())
    for key in ('launcher', 'desktop'):
        path = Path(installed.get('paths', {}).get(key, paths[key]))
        if owned(path):
            path.unlink()
    icon = Path(installed.get('paths', {}).get('icon', paths['icon']))
    if icon.exists() and icon.read_bytes() == (ROOT / 'assets/pulse.svg').read_bytes():
        icon.unlink()
    shutil.rmtree(root)
    print('Pulse uninstalled. Your preferences and notification history were kept.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uninstall', action='store_true')
    parser.add_argument('--dry-run', action='store_true', help='show paths without changing anything')
    parser.add_argument('--python', default=sys.executable, help='Python 3.12+ interpreter for the isolated environment')
    parser.add_argument('--system-site-packages', action='store_true',
                        help='reuse an existing compatible Python/Qt installation without dependency downloads')
    args = parser.parse_args(argv)
    paths = locations()
    if args.dry_run:
        print('Uninstall' if args.uninstall else 'Install')
        for name, path in paths.items():
            print(f'{name}: {path}')
        return 0
    try:
        if args.uninstall:
            uninstall(paths)
        else:
            version = subprocess.check_output([args.python, '-c', 'import sys; print(sys.version_info >= (3, 12))'], text=True).strip()
            if version != 'True':
                raise ValueError('Pulse requires Python 3.12 or newer')
            install(paths, python=args.python, system_packages=args.system_site_packages)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'Install error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
