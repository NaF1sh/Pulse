"""Bounded SQLite history with no Qt dependencies."""
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3


def default_history_path():
    from pulse.platforms import data_dir
    return data_dir() / "history.sqlite3"


class History:
    def __init__(self, path, *, limit=1000, clock=None):
        if type(limit) is not int or limit < 1:
            raise ValueError("History limit must be a positive integer")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(descriptor)
        self.connection = sqlite3.connect(path, timeout=0.2)
        self.connection.row_factory = sqlite3.Row
        self.limit = limit
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
        try:
            with self.connection:
                self.connection.execute("""CREATE TABLE IF NOT EXISTS notifications (
                    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    received_at TEXT NOT NULL,
                    notification_id INTEGER NOT NULL,
                    app TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    kind TEXT NOT NULL
                )""")
        except Exception:
            self.connection.close()
            raise

    def record(self, notification):
        with self.connection:
            self.connection.execute(
                """INSERT INTO notifications
                (received_at, notification_id, app, title, body, priority, kind)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (self.clock(), notification.id, notification.app, notification.title,
                 notification.body, int(notification.priority), str(notification.kind)),
            )
            self.connection.execute("""DELETE FROM notifications WHERE entry_id NOT IN
                (SELECT entry_id FROM notifications ORDER BY entry_id DESC LIMIT ?)""", (self.limit,))

    def recent(self, limit=20):
        if type(limit) is not int or limit < 1:
            raise ValueError("History count must be a positive integer")
        return [dict(row) for row in self.connection.execute(
            "SELECT * FROM notifications ORDER BY entry_id DESC LIMIT ?", (limit,))]

    def clear(self):
        with self.connection:
            count = self.connection.execute("SELECT count(*) FROM notifications").fetchone()[0]
            self.connection.execute("DELETE FROM notifications")
        return count

    def close(self):
        self.connection.close()
