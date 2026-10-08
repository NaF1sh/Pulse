import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from PySide6.QtCore import QCoreApplication
from pulse.tasks.store import TaskStore, validate_target
from pulse.tasks.claude import event
from pulse.ui.tasks import Tasks

_APP = QCoreApplication.instance() or QCoreApplication([])


def test_task_updates_survive_restart_and_reopen_dismissed_alert(tmp_path):
    path = tmp_path / 'tasks.db'
    first = TaskStore(path)
    first.publish('build', title='Build', source='Terminal', progress=.3)
    first.dismiss('build')
    first.publish('build', state='needs-permission', message='Review in terminal')
    first.close()
    second = TaskStore(path)
    row = second.list()[0]
    assert row['title'] == 'Build'
    assert row['revision'] == 2 and not row['dismissed']
    assert row['state'] == 'needs-permission'
    if os.name != 'nt':
        assert path.stat().st_mode & 0o777 == 0o600
    second.close()


def test_task_limit_never_discards_unhandled_work(tmp_path):
    store = TaskStore(tmp_path / 'tasks.db', limit=2)
    store.publish('a', title='First')
    store.publish('b', title='Second', state='done')
    with pytest.raises(ValueError, match='full'):
        store.publish('c', title='Third')
    store.dismiss('b')
    store.publish('c', title='Third')
    assert {row['id'] for row in store.list()} == {'a', 'c'}
    store.clear_finished()
    assert len(store.list()) == 2
    store.close()


@pytest.mark.parametrize('target', ['javascript:alert(1)', 'http://example.com', 'https://user:pass@example.com', 'file://remote/tmp/test', 'relative/path', 'https://example.com/\nfoo'])
def test_untrusted_targets_rejected(target):
    with pytest.raises(ValueError):
        validate_target(target)


def test_invalid_updates_leave_previous_state_intact(tmp_path):
    store = TaskStore(tmp_path / 'tasks.db')
    store.publish('build', title='Build')
    for values in [dict(progress=float('nan')), dict(state='unknown'), dict(message='x'*2001), dict(target='sh:command')]:
        with pytest.raises(ValueError):
            store.publish('build', **values)
    assert store.list()[0]['revision'] == 1
    store.close()


def test_attention_persists_completion_expires_and_dismiss_does_not_approve(tmp_path):
    now = [100]
    writer = TaskStore(tmp_path / 'tasks.db', clock=lambda: now[0])
    tasks = Tasks(clock=lambda: now[0])
    tasks.start(tmp_path / 'tasks.db')
    tasks.timer.stop()
    writer.publish('run', title='Job')
    writer.publish('agent', title='Agent', state='needs-permission')
    tasks.poll()
    assert tasks.head['id'] == 'agent'
    now[0] += 60
    tasks.poll()
    assert tasks.head['id'] == 'agent'
    tasks.dismiss('agent')
    assert writer.list()[0]['state'] == 'needs-permission'
    assert tasks.head['id'] == 'run'
    writer.publish('run', state='done')
    tasks.poll()
    assert tasks.head['state'] == 'done'
    now[0] += 7
    tasks.poll()
    assert tasks.card is None and len(tasks.entries) == 2
    tasks.stop()
    writer.close()


def test_targets_open_only_on_click_and_executables_are_rejected(tmp_path):
    opened = []
    tasks = Tasks(opener=lambda url: opened.append(url.toString()) or True)
    tasks.start(tmp_path / 'tasks.db')
    tasks.timer.stop()
    writer = TaskStore(tmp_path / 'tasks.db')
    writer.publish('a', title='Task', target='https://example.com/result')
    tasks.poll()
    assert not opened
    tasks.open('a')
    assert opened == ['https://example.com/result']
    executable = tmp_path / 'launch.desktop'
    executable.write_text('do not launch')
    writer.publish('a', target=str(executable))
    tasks.poll()
    tasks.open('a')
    assert len(opened) == 1 and tasks.summary['error']
    tasks.stop()
    writer.close()


def test_claude_adapter_filters_idle_and_never_copies_prompt_or_transcript():
    payload = dict(session_id='session', cwd='/work/project', prompt='secret', transcript_path='/private/file')
    mapped = event(dict(payload, hook_event_name='UserPromptSubmit'))
    assert mapped[1]['state'] == 'working'
    assert 'secret' not in str(mapped) and '/private' not in str(mapped)
    assert event(dict(payload, hook_event_name='Notification', notification_type='idle_prompt')) is None
    permission = event(dict(payload, hook_event_name='Notification', notification_type='permission_prompt'))
    assert permission[0] == mapped[0] and permission[1]['state'] == 'needs-permission'
    assert event(dict(payload, hook_event_name='Stop'))[1]['state'] == 'done'
    assert event(dict(payload, hook_event_name='StopFailure'))[1]['state'] == 'failed'


def test_cli_real_job_exit_status_and_hook_without_gui(tmp_path):
    env = dict(os.environ, XDG_DATA_HOME=str(tmp_path), PYTHONPATH=str(Path('src').resolve()), QT_QPA_PLATFORM='not-a-platform')
    def run(*args, input=None):
        return subprocess.run([sys.executable, '-m', 'pulse.main', *args], env=env, input=input, capture_output=True, text=True, timeout=10)
    result = run('run', '--title', 'Passing job', '--', sys.executable, '-c', 'print("job output")')
    assert result.returncode == 0 and 'job output' in result.stdout
    result = run('run', '--title', 'Failing job', '--', sys.executable, '-c', 'raise SystemExit(7)')
    assert result.returncode == 7
    result = run('task', 'claude-hook', input=json.dumps(dict(session_id='abc', hook_event_name='Notification', notification_type='permission_prompt')))
    assert result.returncode == 0 and result.stdout == ''
    rows = json.loads(run('task', 'list').stdout)
    assert {row['state'] for row in rows} == {'done', 'failed', 'needs-permission'}
    result = run('task', 'claude-hook', input='not json')
    assert result.returncode == 0 and result.stdout == ''
