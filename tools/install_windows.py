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
APP_USER_MODEL_ID = 'NaF1sh.Pulse.FloatingIsland'


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
    # The AppUserModelID is required for Windows to grant Pulse access to the notification
    # listener (WinRT UserNotificationListener); without it on both the shortcut and the
    # running process, the OS silently refuses the permission request.
    script = ('$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:PULSE_SHORTCUT);'
              '$s.TargetPath=$env:PULSE_TARGET;$s.WorkingDirectory=$env:PULSE_WORKDIR;'
              '$s.IconLocation=$env:PULSE_ICON;$s.Description="Pulse floating island";$s.Save()')
    env = dict(os.environ, PULSE_SHORTCUT=str(paths['shortcut']),
               PULSE_TARGET=str(paths['root'] / 'venv/Scripts/pulse-island.exe'),
               PULSE_WORKDIR=str(paths['root']), PULSE_ICON=str(paths['root'] / 'pulse.ico'))
    subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                   env=env, check=True)
    set_shortcut_aumid(paths['shortcut'], APP_USER_MODEL_ID)


def set_shortcut_aumid(path, aumid):
    """Stamp System.AppUserModel.ID onto the .lnk via IPropertyStore (WScript.Shell cannot set it)."""
    source = r'''
using System;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;

public static class PulseAumid {
    [DllImport("shell32.dll", CharSet = CharSet.Unicode, PreserveSig = true)]
    static extern int SHGetPropertyStoreFromParsingName(
        string path, IntPtr pbc, int flags, ref Guid iid, out IPropertyStore store);

    [ComImport, Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"),
     InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IPropertyStore {
        void GetCount(out uint count);
        void GetAt(uint index, out PROPERTYKEY key);
        void GetValue(ref PROPERTYKEY key, out PROPVARIANT value);
        void SetValue(ref PROPERTYKEY key, ref PROPVARIANT value);
        void Commit();
    }

    [StructLayout(LayoutKind.Sequential)]
    struct PROPERTYKEY { public Guid fmtid; public int pid; }

    [StructLayout(LayoutKind.Sequential)]
    struct PROPVARIANT {
        public ushort vt; public ushort r1; public ushort r2; public ushort r3;
        public IntPtr p; public int extra;
    }

    public static void Set(string path, string aumid) {
        var iid = typeof(IPropertyStore).GUID;
        const int GPS_READWRITE = 2;
        IPropertyStore store;
        int hr = SHGetPropertyStoreFromParsingName(path, IntPtr.Zero, GPS_READWRITE, ref iid, out store);
        if (hr != 0) throw new COMException("SHGetPropertyStoreFromParsingName failed", hr);
        var key = new PROPERTYKEY { fmtid = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"), pid = 5 };
        var value = new PROPVARIANT { vt = 31 /* VT_LPWSTR */, p = Marshal.StringToCoTaskMemUni(aumid) };
        try {
            store.SetValue(ref key, ref value);
            store.Commit();
        } finally {
            Marshal.FreeCoTaskMem(value.p);
        }
    }
}
'''
    script = ('Add-Type -TypeDefinition $env:PULSE_AUMID_SOURCE -Language CSharp;'
               '[PulseAumid]::Set($env:PULSE_SHORTCUT, $env:PULSE_AUMID)')
    # SHGetPropertyStoreFromParsingName requires native backslash separators.
    env = dict(os.environ, PULSE_SHORTCUT=str(path).replace('/', '\\'),
               PULSE_AUMID=aumid, PULSE_AUMID_SOURCE=source)
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


def python_info(python):
    output = subprocess.check_output([python, '-c',
        'import json, platform, struct, sys; print(json.dumps(dict('
        'version=list(sys.version_info[:3]), executable=sys.executable, '
        'implementation=platform.python_implementation(), bits=struct.calcsize("P")*8)))'], text=True)
    info = json.loads(output)
    if tuple(info['version']) < (3, 12):
        raise ValueError(f"Selected Python {'.'.join(map(str, info['version']))} at {info['executable']}; "
                         'Pulse requires Python 3.12 or newer')
    return info


def install_step(label, command, log):
    print(f'\n{label}…', flush=True)
    with log.open('a', encoding='utf-8') as output:
        output.write(f'\n{label}\n')
        output.flush()
        # Keep pip's real error visible and saved, including on dependency/network failures.
        env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1')
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, encoding='utf-8', errors='replace', env=env) as process:
            for line in process.stdout:
                output.write(line)
                output.flush()
                print(line, end='', flush=True)
            code = process.wait()
        if code:
            raise ValueError(f'{label} failed (exit {code}). See the error above and {log}')


def is_pulse_shortcut(paths):
    """Recognize an old Pulse link even if its installation manifest is gone."""
    script = ('[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false);'
              '$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:PULSE_SHORTCUT);'
              '@{target=$s.TargetPath;arguments=$s.Arguments} | ConvertTo-Json -Compress')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                            env=dict(os.environ, PULSE_SHORTCUT=str(paths['shortcut'])),
                            capture_output=True, text=True, encoding='utf-8', check=True, timeout=15)
    try:
        link = json.loads(result.stdout.lstrip('\ufeff'))
        target = link.get('target')
        return (isinstance(target, str) and bool(target) and not link.get('arguments')
                and Path(target).resolve() == (paths['root'] / 'venv/Scripts/pulse-island.exe').resolve())
    except (ValueError, AttributeError, OSError):
        return False


def install(paths, python):
    root = paths['root']
    owned = manifest_at(root)
    if root.exists() and not owned:
        raise ValueError(f'Refusing to replace an existing non-Pulse folder: {root}')
    if paths['shortcut'].exists() and not owned:
        if not is_pulse_shortcut(paths):
            raise ValueError(f'The existing shortcut does not point to this Pulse installation; '
                             f'leaving it untouched: {paths["shortcut"]}')
        print('Found a leftover Pulse shortcut. It will be repaired after installation.', flush=True)
    if owned:
        ensure_not_running(paths)
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / 'install.json'
    manifest.write_text(json.dumps(owned or {'installer': MARKER}), encoding='utf-8')
    log = root.parent / 'install.log'
    install_step('Creating the Pulse environment', [python, '-m', 'venv', str(root / 'venv')], log)
    interpreter = root / 'venv/Scripts/python.exe'
    install_step('Updating pip', [str(interpreter), '-m', 'pip', 'install', '--upgrade', 'pip'], log)
    install_step('Installing Pulse and its dependencies', [str(interpreter), '-m', 'pip', 'install', str(ROOT)], log)
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
            info = python_info(args.python)
            description = (f"Using {info['implementation']} {'.'.join(map(str, info['version']))} "
                           f"({info['bits']}-bit): {info['executable']}")
            print(description, flush=True)
            log = paths['root'].parent / 'install.log'
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(description + '\n', encoding='utf-8')
            install(paths, info['executable'])
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        detail = f'Pulse error: {error}'
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            detail += '\n' + str(error.stderr)
        print(detail, file=sys.stderr)
        if not args.uninstall:
            log = paths['root'].parent / 'install.log'
            try:
                log.parent.mkdir(parents=True, exist_ok=True)
                with log.open('a', encoding='utf-8') as output:
                    output.write(detail + '\n')
                print(f'Installation log: {log}', file=sys.stderr)
            except OSError:
                pass
        if args.interactive:
            input('Press Enter to close this window…')
        return 1
    if args.interactive:
        input('Press Enter to close this window…')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
