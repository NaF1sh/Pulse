"""Bounded, user-local task state shared by CLI publishers and the island."""
import os
from pathlib import Path
import re
import sqlite3
import time
from urllib.parse import urlparse

STATES = ('working', 'needs-input', 'needs-permission', 'done', 'failed', 'cancelled')
TERMINAL = ('done', 'failed', 'cancelled')


def default_path():
    from pulse.platforms import data_dir
    return data_dir() / 'tasks.sqlite3'


def validate_target(value):
    if not value:
        return ''
    if len(value) > 2048 or any(ord(char) < 32 for char in value):
        raise ValueError('Invalid open target.')
    if Path(value).is_absolute():
        return Path(value).as_uri()
    parsed = urlparse(value)
    if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password:
        return value
    # Only local files/folders or HTTPS links. Never run shell commands from events.
    if parsed.scheme == 'file' and parsed.netloc in ('', 'localhost') and parsed.path.startswith('/'):
        return value
    raise ValueError('Open target must be an absolute local path or an HTTPS URL.')


class TaskStore:
    def __init__(self, path=None, *, clock=time.time, limit=200):
        self.path = Path(path or default_path())
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(fd)
        self.connection = sqlite3.connect(self.path, timeout=.2)
        self.connection.row_factory = sqlite3.Row
        self.clock = clock
        self.limit = limit
        with self.connection:
            self.connection.execute('''CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, source TEXT NOT NULL,
                state TEXT NOT NULL, message TEXT NOT NULL, target TEXT NOT NULL,
                progress REAL, created REAL NOT NULL, updated REAL NOT NULL,
                revision INTEGER NOT NULL, dismissed INTEGER NOT NULL DEFAULT 0)''')

    def publish(self, task_id, *, title=None, source=None, state='working', message='', target=None, progress=None):
        if not isinstance(task_id, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', task_id):
            raise ValueError('Task ID must use 1–80 letters, digits, dots, underscores or hyphens.')
        if state not in STATES:
            raise ValueError('Unknown task state.')
        for label, value, maximum in [('Title', title, 160), ('Source', source, 80), ('Message', message, 2000)]:
            if value is not None and (not isinstance(value, str) or len(value) > maximum or '\x00' in value):
                raise ValueError(f'{label} must be text up to {maximum} characters.')
        if progress is not None and (type(progress) not in (int, float) or not 0 <= progress <= 1):
            raise ValueError('Progress must be a number between 0 and 1.')
        target = validate_target(target) if target is not None else None
        with self.connection:
            self.connection.execute('BEGIN IMMEDIATE')
            previous = self.connection.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
            if previous is None:
                if not title or not title.strip():
                    raise ValueError('New tasks need a title.')
                count = self.connection.execute('SELECT count(*) FROM tasks').fetchone()[0]
                if count >= self.limit:
                    oldest = self.connection.execute("SELECT id FROM tasks WHERE state IN ('done','failed','cancelled') AND dismissed=1 ORDER BY updated LIMIT 1").fetchone()
                    if oldest is None:
                        raise ValueError('Task list is full. Dismiss a finished task before starting another.')
                    self.connection.execute('DELETE FROM tasks WHERE id=?', (oldest[0],))
            now = self.clock()
            self.connection.execute('''INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,0)
                ON CONFLICT(id) DO UPDATE SET title=excluded.title, source=excluded.source,
                state=excluded.state, message=excluded.message, target=excluded.target,
                progress=excluded.progress, updated=excluded.updated,
                revision=excluded.revision, dismissed=0''',
                (task_id, title if title is not None else previous['title'],
                 source if source is not None else previous['source'] if previous else 'Local task',
                 state, message, target if target is not None else previous['target'] if previous else '',
                 progress, previous['created'] if previous else now, now,
                 previous['revision'] + 1 if previous else 1))
        return task_id

    def list(self):
        return [dict(row) for row in self.connection.execute('SELECT * FROM tasks ORDER BY updated DESC, id')]

    def dismiss(self, task_id):
        with self.connection:
            self.connection.execute('UPDATE tasks SET dismissed=1 WHERE id=?', (task_id,))

    def clear_finished(self):
        with self.connection:
            self.connection.execute("DELETE FROM tasks WHERE state IN ('done','failed','cancelled')")

    def close(self):
        self.connection.close()
