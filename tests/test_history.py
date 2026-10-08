import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

from PySide6.QtCore import QCoreApplication

from pulse.core.history import History, default_history_path
from pulse.core.models import Notification
from pulse.core.rules import Rules
from pulse.ui.controller import Controller


def test_history_survives_restart_and_preserves_received_updates(tmp_path):
    path = tmp_path / "history.sqlite3"
    history = History(path, clock=lambda: "2026-10-08T12:00:00+00:00")
    history.record(Notification(1, "Chat", "First", "It's a message"))
    history.record(Notification(1, "Chat", "Updated", "<plain>"))
    history.close()
    history = History(path)
    rows = history.recent()
    assert [row["title"] for row in rows] == ["Updated", "First"]
    assert rows[0]["received_at"] == "2026-10-08T12:00:00+00:00"
    assert rows[1]["body"] == "It's a message"
    assert rows[0]["entry_id"] != rows[1]["entry_id"]
    assert path.stat().st_mode & 0o777 == 0o600
    history.close()


def test_retention_and_clear_do_not_prevent_future_writes(tmp_path):
    history = History(tmp_path / "history.sqlite3", limit=2)
    for id in range(4):
        history.record(Notification(id, "Chat", str(id)))
    assert [row["title"] for row in history.recent()] == ["3", "2"]
    assert history.clear() == 2
    assert history.recent() == []
    history.record(Notification(1, "Chat", "After clear"))
    assert history.recent()[0]["title"] == "After clear"
    history.close()


def test_history_records_eligible_arrivals_but_not_muted_or_replayed_cards(tmp_path):
    app = QCoreApplication.instance() or QCoreApplication([])
    history = History(tmp_path / "history.sqlite3")
    controller = Controller(history=history, rules=Rules(muted_apps=("Muted",)))
    controller.submit(Notification(1, "Chat", "First"))
    controller.submit(Notification(2, "Chat", "Queued"))
    controller.submit(Notification(3, "Muted", "Hidden"))
    controller.dismiss()
    controller.dismiss()
    assert [row["title"] for row in history.recent()] == ["Queued", "First"]
    controller.timer.stop()
    history.close()


def test_failed_write_keeps_notifications_working_and_reports_once():
    app = QCoreApplication.instance() or QCoreApplication([])
    class BrokenHistory:
        def record(self, notification):
            raise sqlite3.OperationalError("disk full")
    controller = Controller(history=BrokenHistory())
    errors = []
    controller.historyFailed.connect(errors.append)
    controller.submit(Notification(1, "Chat", "First"))
    controller.submit(Notification(2, "Chat", "Next"))
    assert controller.title == "First"
    assert controller.queued == 1
    assert len(errors) == 1
    assert "disk full" in errors[0]
    controller.timer.stop()


def run_cli(path, *args):
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=str(root / "src"), QT_QPA_PLATFORM="invalid-test-platform")
    return subprocess.run([sys.executable, "-m", "pulse.main", "--history-file", str(path), *args],
                          env=env, capture_output=True, text=True, timeout=10)


def test_history_cli_can_view_and_clear_without_a_display(tmp_path):
    path = tmp_path / "history.sqlite3"
    history = History(path)
    history.record(Notification(1, "Chat", "First", "Line\n\x1b[31m"))
    history.record(Notification(2, "Mail", "Second"))
    history.close()
    result = run_cli(path, "--history", "1")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["title"] == "Second"
    result = run_cli(path, "--history")
    assert "\x1b" not in result.stdout
    assert len(result.stdout.splitlines()) == 2
    result = run_cli(path, "--clear-history")
    assert result.returncode == 0
    assert "Cleared 2" in result.stdout
    assert "No saved" in run_cli(path, "--history").stdout


def test_missing_history_does_not_create_database_and_invalid_count_fails(tmp_path):
    path = tmp_path / "missing" / "history.sqlite3"
    assert run_cli(path, "--history").returncode == 0
    assert run_cli(path, "--clear-history").returncode == 0
    assert not path.exists()
    assert run_cli(path, "--history", "0").returncode == 2


def test_history_path_uses_xdg_data_home(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert default_history_path() == tmp_path / "pulse" / "history.sqlite3"


def test_system_cards_do_not_fill_notification_history(tmp_path):
    app = QCoreApplication.instance() or QCoreApplication([])
    history = History(tmp_path / "history.sqlite3")
    controller = Controller(history=history)
    controller.submit_system(Notification(-1, "Audio", "Volume"))
    controller.submit(Notification(1, "Chat", "Message"))
    assert [row["title"] for row in history.recent()] == ["Message"]
    controller.timer.stop()
    history.close()
