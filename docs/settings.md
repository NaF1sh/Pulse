# Notification settings

Implemented startup-only TOML settings, independent pure-Python visibility
rules, and one-run CLI flags. No user config is created or overwritten.

Rules apply in the core before queue insertion. App mute takes precedence over
the DND critical exemption. A suppressed replacement removes its existing card
so stale content does not remain. Suppressed notifications are not queued for
replay. Settings apply to demo and live sources; default_timeout applies only
to live Notify calls with a negative timeout and normal/low urgency.

Current controls: dnd, allow_critical, muted_apps, default_timeout, reduced_motion.
The repo's config.example.toml documents defaults. The default user config is
XDG_CONFIG_HOME/pulse/config.toml or ~/.config/pulse/config.toml. Explicit config
paths must exist. Invalid types, invalid ranges, malformed TOML and unknown keys
fail before creating a window. Settings take effect after restart.

Live observer capture was confirmed working by the user. Pending: automatic Plasma DND integration,
fullscreen detection, runtime reload and a settings UI. None are implied by
these startup settings.
