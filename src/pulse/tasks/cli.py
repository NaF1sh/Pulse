"""Publish explicit task events without starting Qt or reading agent conversations."""
import argparse
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import uuid

from pulse.tasks.store import STATES, TaskStore, default_path


def main(argv):
    parser = argparse.ArgumentParser(prog='pulse ' + argv[0])
    if argv[0] == 'run':
        parser.add_argument('--title', help='short task label; defaults to executable name')
        parser.add_argument('--source', default='Terminal')
        parser.add_argument('command', nargs=argparse.REMAINDER)
        args = parser.parse_args(argv[1:])
        command = args.command
        if command and command[0] == '--':
            command = command[1:]
        if not command:
            parser.error('provide a command after --')
        return run(command, args.title, args.source)
    sub = parser.add_subparsers(dest='operation', required=True)
    emit = sub.add_parser('emit', help='create or update a task by stable ID')
    emit.add_argument('id')
    emit.add_argument('--title')
    emit.add_argument('--source')
    emit.add_argument('--state', choices=STATES, default='working')
    emit.add_argument('--message', default='')
    emit.add_argument('--open', dest='target')
    emit.add_argument('--progress', type=float, help='0 to 1; omit for indeterminate progress')
    sub.add_parser('claude-hook', help='read a Claude Code hook event from stdin')
    sub.add_parser('list', help='list tasks as JSON')
    dismiss = sub.add_parser('dismiss', help='hide an alert without approving or stopping its task')
    dismiss.add_argument('id')
    remove = sub.add_parser('remove', help='delete a task record regardless of its state')
    remove.add_argument('id')
    sub.add_parser('clear-finished', help='delete completed, failed and cancelled task records')
    args = parser.parse_args(argv[1:])
    if args.operation == 'claude-hook':
        from pulse.tasks.claude import main as claude_main
        return claude_main()
    store = None
    try:
        store = TaskStore()
        if args.operation == 'emit':
            print(store.publish(args.id, title=args.title, source=args.source, state=args.state,
                                message=args.message, target=args.target, progress=args.progress))
        elif args.operation == 'list':
            print(json.dumps(store.list(), ensure_ascii=False))
        elif args.operation == 'dismiss':
            store.dismiss(args.id)
        elif args.operation == 'remove':
            store.remove(args.id)
        else:
            store.clear_finished()
        return 0
    except (ValueError, OSError, sqlite3.Error) as error:
        print(f'Pulse: {error}', file=sys.stderr)
        return 2
    finally:
        if store is not None:
            store.close()


def run(command, title, source):
    task_id = uuid.uuid4().hex
    store = None
    process = None
    try:
        store = TaskStore()
        store.publish(task_id, title=title or Path(command[0]).name, source=source,
                      message='Running in your terminal.')
        print(f'Pulse task: {task_id}', file=sys.stderr)
        # Inherit the terminal: interactive agents retain their own prompts and permissions.
        process = subprocess.Popen(command)
        try:
            code = process.wait()
        except KeyboardInterrupt:
            # The terminal delivers SIGINT to the child as well; cover non-terminal callers.
            if process.poll() is None:
                if os.name == 'nt':
                    process.terminate()
                else:
                    process.send_signal(signal.SIGINT)
            code = process.wait()
            if code == 0:
                code = 130
        result = code if code >= 0 else 128 - code
        state = 'done' if result == 0 else 'cancelled' if result in (130, 143) else 'failed'
        try:
            store.publish(task_id, state=state, message=f'Exited with status {result}. Output remains in your terminal.')
        except (OSError, sqlite3.Error):
            print('Pulse could not record completion. The command exit status is preserved.', file=sys.stderr)
        return result
    except (ValueError, OSError, sqlite3.Error) as error:
        if process is None and store is not None:
            try:
                store.publish(task_id, state='failed', message=str(error)[:2000])
            except (ValueError, OSError, sqlite3.Error):
                pass
        print(f'Pulse: {error}', file=sys.stderr)
        return 127 if isinstance(error, FileNotFoundError) else 2
    finally:
        if store is not None:
            store.close()
