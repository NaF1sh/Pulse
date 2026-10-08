# Pulse 0.2.0a1 — Linux and Windows preview

Pulse remains a floating island. This preview adds local task and agent status,
custom notification backgrounds, and a Windows source installer alongside Linux.

## Downloads

- Windows: download `Pulse-Windows-preview.zip`, extract it, and run
  `install-windows.cmd`. Python 3.12+ and internet access are required. Open Pulse
  from Start after installation. This is not a standalone or signed executable.
- Linux: download `pulse_island-0.2.0a1.tar.gz`, extract it, and run `./install.sh`.
  Python 3.12+ is required. Existing Linux features and data paths are preserved.

## Included

- Running-task counts, progress, persistent input/permission/failure alerts, brief
  completion alerts, and an expandable activity list inside the island.
- Local task CLI/API and a terminal-preserving command wrapper.
- A Claude Code hook adapter and setup example; approvals stay in the original tool.
- Solid/random colors and local image backgrounds, including pasted file paths,
  live preview, crop positioning, and darkness controls.
- Searchable notification history, music playback controls on Linux, and an optional
  focus/break timer.
- Windows backend selection, user-profile storage, installer/uninstaller, Start-menu
  shortcut, and console/GUI launchers.

## Preview limits

Windows desktop notification capture, music controls, and volume feedback are not
implemented. The Windows preview centers on tasks, agents, pets, and backgrounds.
A working task represents the latest published state, not a process heartbeat.
Agent integrations require setup; Pulse does not discover agents automatically or
approve permission requests.

205 automated tests passed in the Linux development environment. The release
workflow also requires Linux and Windows CI checks, including Windows startup and
installer checks, before uploading assets. Hands-on Windows desktop, compositor,
and live-agent verification remain necessary; CI alone does not establish those.
