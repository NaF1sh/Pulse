#!/usr/bin/env python3
"""Guided desktop check using only synthetic notifications; run outside restricted shells."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import subprocess
import sys


def run(argv, *, timeout=15):
    return subprocess.run(argv, text=True, capture_output=True, timeout=timeout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('desktop-check.md'))
    args = parser.parse_args()
    for tool in ('busctl', 'notify-send'):
        if not shutil.which(tool):
            parser.error(f'{tool} is required')
    if run(['busctl', '--user', '--timeout=2', '--no-pager', 'list'], timeout=3).returncode:
        parser.error('Cannot access the desktop bus. Run this from your regular desktop terminal.')
    if not sys.stdin.isatty():
        parser.error('This guided check needs an interactive terminal')
    rows = []
    def record(title):
        answer = input(f'{title} [y/n/s=skip]: ').strip().lower()
        rows.append((title, {'y': 'PASS', 'n': 'FAIL'}.get(answer, 'NOT TESTED')))
    def notify(title, body, *extra):
        result = run(['notify-send', '-a', 'Pulse Check', '-i', 'dialog-information',
                      '-t', '10000', *extra, title, body])
        if result.returncode:
            raise RuntimeError('The desktop rejected a synthetic notification')
        return result.stdout.strip()
    print('Open Pulse from the app menu first. These checks do not change Plasma settings.')
    print('Use only synthetic messages. The report stores test results, not notification content.')
    input('Press Enter when Pulse is running…')
    record('Launch Pulse a second time: did the existing Settings window open without a second pet?')
    notify('Source icon check', 'An information icon should appear beside this synthetic message.')
    record('Did Pulse show the source icon and readable text?')
    identity = notify('Replacement check', 'This message should update in place.', '-p')
    if not identity.isdecimal():
        raise RuntimeError('The desktop did not return a notification ID')
    notify('Replacement updated', 'There should be one updated Pulse card.', '-r', identity)
    record('Did the replacement update the existing card without creating a duplicate?')
    run(['busctl', '--user', '--timeout=2', 'call', 'org.freedesktop.Notifications',
         '/org/freedesktop/Notifications', 'org.freedesktop.Notifications', 'CloseNotification', 'u', identity])
    record('Did closing the synthetic notification remove its Pulse card?')
    print('For the next notification, click the Pulse card within ten seconds.')
    result = run(['notify-send', '-a', 'Pulse Check', '-t', '10000', '--wait', '--action=default=Open',
                  'Action check', 'Click this Pulse card to exercise its default action.'], timeout=15)
    rows.append(('Default action dispatched', 'PASS' if result.stdout.strip() == 'default' else 'NOT CONFIRMED'))
    print('In General, enable Quiet Plasma popups. In Status, wait for inhibition to become active.')
    input('Press Enter to send the duplicate-popup check…')
    notify('Single popup check', 'Pulse should show this; ordinary Plasma popups should be paused.')
    record('Did you see only the Pulse popup?')
    print('Disable Quiet Plasma popups, or quit Pulse, before continuing.')
    input('Press Enter to check restoration…')
    notify('Restoration check', 'Your normal Plasma popup should be back.')
    record('Did Plasma notification popups return?')
    print('Reopen Pulse if needed. The following checks are manual.')
    for item in (
        'Play music, send a message, and dismiss it: did the current track return?',
        'Change volume and mute: was the displayed value correct?',
        'Suspend/resume: did notifications and music recover?',
        'Change the primary monitor: did Pulse move to its top center?',
        'At 100%, 150%, and 200% display scaling: were text and controls clear?',
        'Can you click the desktop through the transparent area around Pulse?',
    ):
        record(item)
    report = ['# Pulse desktop check', '', f'Date: {datetime.now(timezone.utc).isoformat()}',
              f'Desktop: {os.environ.get("XDG_CURRENT_DESKTOP", "unknown")}',
              f'Session: {os.environ.get("XDG_SESSION_TYPE", "unknown")}', '', '| Check | Result |', '| --- | --- |']
    report.extend(f'| {title} | {result} |' for title, result in rows)
    args.output.write_text('\n'.join(report) + '\n')
    print(f'Report saved to {args.output}. Review it before sharing.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.TimeoutExpired, KeyboardInterrupt, EOFError) as error:
        print(f'Check stopped: {error}', file=sys.stderr)
        raise SystemExit(1)
