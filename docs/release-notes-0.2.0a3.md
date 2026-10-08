# Pulse 0.2.0a3 — Close button and Windows uninstall fixes

The island’s cross now collapses manually expanded bars and task drawers when dismissing
the displayed alert. Empty bars close correctly, queued notifications remain available,
and dismissing a task alert does not cancel its task. The cross also has a larger click area.

Windows installations now register in Installed Apps and include a double-click
`uninstall-windows.cmd`. Older installations can be removed with the new script without
reinstalling. Uninstall checks for running Pulse processes before deleting anything and
keeps preferences, backgrounds, and task records.

Includes the [Windows music integration from 0.2.0a2](release-notes-0.2.0a2.md).
Quit Pulse, extract the updated download, and rerun the installer to update.

Real QML mouse-click regression tests cover empty bars, queued notifications, task alerts,
and recent-task drawers. Native Windows desktop verification remains outstanding.
