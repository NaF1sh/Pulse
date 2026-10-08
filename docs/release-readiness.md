# Release readiness

Pulse is an early preview, not a claim of broad Linux compatibility.

## Implemented

- [x] User-level installation, app-menu entry, update path, and uninstall preserving data.
- [x] First-run guidance, companion selection, and a notification preview.
- [x] Duplicate-launch protection with settings activation.
- [x] Visible notification connection failures and automatic retry.
- [x] Local dependency diagnostics and source status.
- [x] Keyboard-accessible settings, scrolling, and reduced-motion support.
- [x] Real-interface README demo with simulated content.
- [x] Repository CI configuration for tests, package build, and packaged startup.

- [x] Experimental connection-scoped Plasma popup control with failure/reconnect checks.
- [x] Guided desktop check using synthetic notifications.

## Verify on real desktops before a wider release

- [ ] Clean online installation on supported distributions, including required Qt platform libraries.
- [ ] Repeated app-menu launches focus the existing Settings window under the compositor.
- [ ] Verify ordinary popup suppression and restoration, including Pulse crashes and monitor disconnects.
- [ ] Actual Discord/browser messages show appropriate source images and perform the advertised actions.
- [ ] Notification bursts, replacements, dismissals, and source reconnection during a full-day session.
- [ ] Screen unplug/reconnect, primary-screen changes, 100%/150%/200% scaling, and suspend/resume.
- [ ] Input passes through transparent window regions and fullscreen apps are handled acceptably.
- [ ] Measure idle CPU, memory growth, and animation frame times on modest hardware.
- [ ] Native Wayland with compatible Qt and LayerShellQt; document successful distributions separately.
- [x] License original code under MIT; document asset exclusions and omit reference images from release packages.
- [ ] Establish the provenance of supplied reference images before redistributing them.
- [ ] Run CI on GitHub and review its first result; local success is not evidence of a hosted run.

Keep unresolved checks visible. A preview release should describe exactly which desktop combinations were tested.
