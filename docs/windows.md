# Pulse for Windows — preview

The Linux version remains available through `install.sh`. Windows uses the same floating
island and task model with a separate per-user installer and native Windows Qt backend.
This is a source-installer preview, not a signed, self-contained executable.

## Install on Windows

Target: Windows 10/11 x64 with Python 3.12 or newer available through `py` or `python`. Python 3.14 passes the version requirement.
Internet access is required to download Python dependencies during installation.

1. Download the [Windows source ZIP](https://github.com/NaF1sh/Pulse/archive/refs/heads/main.zip), extract it, and open `Pulse-main`. A separately published `Pulse-Windows-preview.zip` release bundle can also be used.
2. Double-click `install-windows.cmd` in the extracted folder.
3. Open **Pulse** from the Start menu.

From PowerShell, the same installation is:

```powershell
py -3 tools/install_windows.py
```

If the `py` launcher is unavailable, use a compatible Python executable directly:

```powershell
python tools/install_windows.py
```

The installer creates `%LOCALAPPDATA%\Pulse\app\venv` and a Start-menu shortcut.
It does not require administrator privileges, change PATH, or register login startup.
Launching Pulse again opens Settings in the existing instance.

## Moving the island

Drag the circle or an empty area of the expanded bar to move it. Buttons keep their
normal actions; dragging does not open or dismiss a notification. Cards stay within the
screen’s available area and ease inward when opening near an edge. Reduce motion disables
this adjustment animation. Every launch starts at top-middle again; positions are never
saved, including across a PC restart.

## Installation troubleshooting

The installer prints the exact Python version and executable it selects. Installation
output is saved to `%LOCALAPPDATA%\Pulse\install.log`; the final error identifies the
failed step. Dependency downloads require internet access. If an older installer says
“Python 3.12 or newer is required” after another error, read the preceding error: that
older launcher incorrectly used the same message for every failure.

A leftover Start-menu shortcut from an earlier Pulse installation is repaired automatically
when its target is the expected Pulse launcher and it has no extra arguments. Unrelated
shortcuts and unowned app folders are preserved. If the Python launcher selects a different
interpreter from the one you intended, run `py -3.14 tools/install_windows.py` from the
extracted folder, or invoke the desired Python executable by its full path.

## Music

Music detection starts automatically (except in demo mode or with `--no-music`).
Players must expose a [Windows media session](https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssessionmanager).
Pulse shows the track, artist, and available cover art, with play/pause and skip controls
when the player supports them. A playing session takes priority over paused sessions.
Stopped or closed sessions disappear. Windows 10 version 1809 or later is required.

To update an older installation, quit Pulse completely, extract a fresh download, and
rerun `install-windows.cmd`. This installs the Windows media dependencies as well as the app.
Open Pulse from Start, play a track, and allow a few seconds for discovery. Enable
**Now playing** in General settings if you previously hid music. The Music page displays
the active track; Status shows the music connection or dependency error. Notifications
and active task cards can temporarily take priority over music in the island.
If Status says it is waiting for a player, check that the player/browser is sharing
system media controls. Audio output alone does not supply track metadata.

## Try a task

In PowerShell:

```powershell
$pulse = "$env:LOCALAPPDATA\Pulse\app\venv\Scripts\pulse.exe"
& $pulse run --title "First Windows task" -- py -3 -c "import time; time.sleep(5)"
& $pulse task emit review --title "Agent review" --source "My agent" --state needs-input --message "Return to the agent to answer its question"
& $pulse task emit review --state done --message "Review finished"
```

The task drawer expands inside the island. CLI events work without a graphical session;
they are shown when Pulse is running. Approvals remain in the originating agent.

The wrapper executes programs directly and preserves the terminal. For a Windows command
script such as `npm.cmd`, explicitly invoke the command processor rather than expecting
Pulse to interpret shell syntax:

```powershell
& $pulse run --title "Tests" -- cmd.exe /d /c npm test
```

For agent integrations, call the installed `pulse.exe task emit ...` from the tool's own
supported hooks. The Claude adapter can also be invoked as `pulse.exe task claude-hook`
with its event JSON on stdin. The repository's sample hook command uses a Linux install
path: replace it with the fully quoted Windows executable path appropriate to the shell
your agent uses. Live Windows agent-hook setup has not been verified here.

## Feature scope

| Feature | Windows preview | Linux |
| --- | --- | --- |
| Floating island and expandable task list | Implemented; needs native desktop verification | Available |
| Local task CLI/API and command wrapper | Implemented | Available |
| Explicit agent hook events | Adapter included; integration setup required | Adapter included; integration setup required |
| Pets, colors, downloaded-image backgrounds | Implemented | Available |
| Optional focus/break timer | Implemented | Available |
| Desktop notification mirroring | Not implemented | D-Bus observer |
| Music detection, artwork and controls | Implemented with Windows media sessions; native player validation pending | MPRIS |
| Volume feedback | Not implemented | PipeWire |
| Plasma popup inhibition | Not applicable | Experimental opt-in |

Unsupported Linux integration switches are hidden in Windows General settings. Status
explains the Windows scope. Passing Linux-only source flags such as `--observe` on Windows
returns an explanatory error rather than trying to start missing Linux tools.

Paste Windows image paths directly, including spaces, e.g. `C:\Users\You\Pictures\island.jpg`.
Local task result paths work the same way. URLs and supported documents open only on click.

## Data, updates, and removal

- Preferences and imported backgrounds: `%LOCALAPPDATA%\Pulse\config`
- Task records: `%LOCALAPPDATA%\Pulse\data\tasks.sqlite3`
- Instance lock and activation: `%LOCALAPPDATA%\Pulse\runtime`

Storage uses your Windows user profile and its access controls. Unix mode bits are not a
Windows ACL guarantee. Explicit XDG overrides are also supported for isolated testing.

Right-click the island, open Settings, and choose **Quit Pulse** before updating or
uninstalling. Closing the notification bar only dismisses the card; it does not exit Pulse.
Obtain the new source bundle and rerun the installer to update.

New installations appear in **Windows Settings → Apps → Installed apps → Pulse → Uninstall**.
The installed uninstaller works even after deleting the downloaded ZIP/folder.
For an older installation without an Installed Apps entry, extract the latest download and
double-click **uninstall-windows.cmd**; you do not need to reinstall first. Or run:

```powershell
py -3 tools/install_windows.py --uninstall
```

Uninstall checks for running Pulse processes before deleting files. It removes the
installer-owned app environment, its Installed Apps entry, and unchanged shortcut, while keeping
preferences, images, and task data. `--dry-run` prints paths without changing anything.

## Validation and remaining checks

Linux tests cover the shared UI, command wrapper, task database, Windows path selection,
platform gating, and installer ownership guards. The Windows GitHub Actions job runs native
path/image tests, QML interaction tests, an actual Windows-backend startup, and an installer
round trip. It uploads the Windows source-installer ZIP only after those steps succeed.
That workflow is configured, not claimed to have run successfully from this Linux workspace.

Before treating this as a stable Windows release, verify the installer on a Windows PC,
transparency, mouse pass-through outside the island, scaling and monitor changes, restart
activation, local image selection, and agent events. Qt's Windows deployment guidance is
available in the [official Qt documentation](https://doc.qt.io/qt-6/windows.html).
