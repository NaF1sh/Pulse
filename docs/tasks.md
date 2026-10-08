# Tasks in the floating island

Pulse shows explicitly reported jobs and agent events alongside notifications and music.
It does not watch terminal text, read conversations, or guess whether an agent needs permission.
The island remains the main interface: click its task count to open the compact activity drawer.

## Try it

Reopen Pulse after installing this update. In another terminal:

```bash
~/.local/bin/pulse run --title "Demo job" -- sleep 5
```

The island shows the running job, then a completion card for six seconds. Click the pet
or task count to review it later. Try a command in your own project:

```bash
pulse run --title "API tests" -- npm test
pulse run --title "Build" -- make
```

`run` launches the command directly without a shell, preserves its exit status, and inherits
your terminal so interactive prompts and output remain there. Quote shell syntax explicitly
only when you intend to use a shell, e.g. `pulse run -- sh -c 'command1 && command2'`.
Pulse records the label and exit status, not the command arguments or terminal output.
A zero exit means the process succeeded; it does not prove the agent met your requirements.
Wrapping an interactive agent reports process start/exit only. Its individual turns and
permission requests require hooks or another explicit integration.

## Publish from a script or agent

Use a stable ID for updates to the same task:

```bash
pulse task emit api-review --title "Review API changes" --source "My agent" \
  --state working --message "Reviewing endpoints"
pulse task emit api-review --state working --progress 0.6 --message "Tests in progress"
pulse task emit api-review --state needs-permission \
  --message "Review the migration command in your agent" \
  --open https://example.com/your-approval-request
pulse task emit api-review --state done --message "Review ready" --open /absolute/path/to/results
```

Replace example links and paths with real destinations. Omit `--open` when your tool does
not provide a reliable destination. `needs-input` requests an answer; `failed` reports a
failure; `cancelled` records cancellation. New IDs need `--title`. Progress is optional and
ranges from 0 to 1. Omitting it shows no invented progress estimate.

Working jobs stay compact. Input, permission, and failure alerts persist until dismissed
or updated. Opening a request never clears or approves it; the originating tool must report
the next state. Dismissing hides the current alert without stopping a process. A new event
for that ID makes it visible again. Normal notifications can temporarily cover task status.
Task events are independent of the desktop-notification DND setting.

```bash
pulse task list                 # JSON for your own scripts
pulse task dismiss api-review  # Hide the alert; do not approve or cancel it
pulse task clear-finished      # Delete done, failed, and cancelled records
```

Python callers can use the same local API:

```python
from pulse.tasks.store import TaskStore
store = TaskStore()
try:
    store.publish("review", title="Review", source="My tool", state="needs-input",
                  message="Choose an approach in the original conversation")
finally:
    store.close()
```

## Claude Code hook adapter

The adapter uses Claude Code's [documented command hooks](https://code.claude.com/docs/en/hooks).
A mergeable configuration example is at
[`integrations/claude-code/settings.example.json`](../integrations/claude-code/settings.example.json).
Merge its `hooks` entries into your Claude Code settings, preserving any existing hooks.
The example assumes Pulse's standard `~/.local/bin/pulse` installation. Restart or review
hook settings in Claude Code according to its version's instructions.

The mapping is intentionally narrow:

| Event | Pulse status |
| --- | --- |
| UserPromptSubmit | Working |
| PostToolUse / PostToolUseFailure | Working; an individual tool failure may be recoverable |
| Notification: permission_prompt | Needs permission |
| Notification: elicitation_dialog / agent_needs_input | Needs your answer |
| Stop | Turn finished; review the result |
| StopFailure | Failed |

Idle reminders and unrelated notifications are ignored. Availability and timing of hook
events depend on your Claude Code version and host. The hook reads bounded JSON from stdin,
uses session ID and project name to correlate updates, and never reads the transcript or
stores the prompt/tool payload. It emits no JSON decisions and exits successfully even if
Pulse cannot record the event, so monitoring does not block the agent or answer approvals.
There is no standard terminal/conversation link in these hook events; return to the named
Claude session manually. The generic API accepts a link when an integration can supply one.

## Storage and limits

Tasks live in `$XDG_DATA_HOME/pulse/tasks.sqlite3` (normally `~/.local/share/pulse/tasks.sqlite3`),
created with owner-only permissions. The GUI polls this local database every half second;
there is no network server or cloud account. Any program running as your user can publish
an event, so the originating tool remains the authority for approval details.

Up to 200 tasks are retained. Only dismissed terminal records are evicted automatically;
when no such slot exists, publishers get a clear error instead of silently losing active
work. Clear finished tasks in the drawer to remove those records. Pending and working
records survive a Pulse restart. They represent the last reported state, not a heartbeat:
if a publisher crashes or is killed before sending a final event, dismiss or update that
record manually. This first version does not reconnect to or inspect the running process.

Local folders, supported documents/logs, and HTTPS links can be opened by explicit click.
Executable files and arbitrary command/deep-link schemes are rejected. No action is opened
automatically. `--no-tasks` disables the GUI task feed for a run. Demo mode disables it too.
`--no-history` controls desktop notification history; explicitly published task records are
separate. Clear them with the task controls. No generic agent auto-discovery is claimed.

## Verification

Tests cover separate-process publishing, persistence, bounds, state replacement, wrapper exit
codes, hook filtering, no hook decision output, click-only opening, executable rejection, and
the actual QML drawer and expanding input mask. `tools/render_tasks.py` captures the actual
island with isolated sample events. Live Claude Code hooks still require verification in
an installed Claude session; desktop stacking and link launching require a real desktop.
