"""Read-only Claude Code hook adapter. Emits no decisions and never reads transcripts."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

from pulse.tasks.store import TaskStore


def event(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('session_id'), str):
        return None
    cwd = payload.get('cwd', '')
    project = Path(cwd).name if isinstance(cwd, str) and cwd else 'Session'
    kind = payload.get('hook_event_name')
    state, message = None, ''
    if kind in ('UserPromptSubmit', 'PostToolUse', 'PostToolUseFailure'):
        state, message = 'working', 'Claude is working. Return to its terminal for details.'
    elif kind == 'Notification':
        notification = payload.get('notification_type')
        if notification == 'permission_prompt':
            state, message = 'needs-permission', 'Review the requested permission in Claude Code. Pulse cannot approve it.'
        elif notification in ('elicitation_dialog', 'agent_needs_input'):
            state, message = 'needs-input', 'Claude needs your answer. Return to its conversation.'
    elif kind == 'Stop':
        state, message = 'done', 'Turn finished. Review the result in Claude Code.'
    elif kind == 'StopFailure':
        state, message = 'failed', 'Claude could not finish its turn. Check the error in its terminal.'
    if state is None:
        return None
    task_id = 'claude-' + hashlib.sha256(payload['session_id'].encode()).hexdigest()[:32]
    return task_id, dict(title=('Claude · ' + project)[:160], source='Claude Code', state=state, message=message)


def main():
    store = None
    try:
        raw = sys.stdin.buffer.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            return 0
        mapped = event(json.loads(raw))
        if mapped:
            store = TaskStore()
            store.publish(mapped[0], **mapped[1])
    except (ValueError, OSError, sqlite3.Error):
        # Monitoring must never block a prompt, approve a request, or alter a tool result.
        print('Pulse could not record this hook event.', file=sys.stderr)
    finally:
        if store:
            store.close()
    return 0
