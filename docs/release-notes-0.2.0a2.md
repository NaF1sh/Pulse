# Pulse 0.2.0a2 — Windows music

Windows music detection now starts automatically with the island. Compatible Windows
media sessions supply the track, artist, available cover art, and play/pause/skip controls.
Playing sessions take priority over paused players; closed or stopped players disappear.
Media requests run outside the UI process with time limits and automatic retries.

Quit Pulse, extract the updated Windows download, rerun `install-windows.cmd`, and launch
Pulse from Start. Reinstalling is necessary to add the Windows media dependencies.
See [Windows setup and troubleshooting](windows.md#music). Python 3.12+ is still required.

Linux continues to use MPRIS. Windows notification capture and volume feedback remain
unimplemented. Automated tests cover simulated Windows sessions and shared UI behavior;
the CI workflow includes a native Windows media API probe. Live playback, artwork, and
controls still require hands-on verification with Windows players.
