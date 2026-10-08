# Notification history

SQLite history is a pure-Python core service attached to the controller at live
observer startup. It records arrivals allowed by Pulse's rules, including cards
that wait in the queue. Each eligible replacement is a separate arrival, and
notification IDs are not treated as unique across restarts. Resuming a queued
card, timeout, and dismissal do not insert new entries. Clearing history does
not dismiss the current card or change the queue.

The default archive is XDG_DATA_HOME/pulse/history.sqlite3 or
~/.local/share/pulse/history.sqlite3. A custom --history-file path works for
both observer mode and history commands. Demo and idle-only mode do not open
the database. --no-history disables saving for a live run without deleting
existing entries. No notification images or action payloads are saved.

History contains app, title, body, UTC arrival time, source ID, priority and
kind. Inserts and retention pruning share a transaction; the latest 1000 rows
are retained. Default listing shows 20 newest entries as JSON lines, with
terminal control characters escaped. --history COUNT changes the listing count.
--clear-history deletes all rows and reports the count. Missing archives return
an empty result without creating a file. History commands require no Qt window
or session bus and cannot be combined with --observe or --demo.

New data directories use mode 0700; new database files use 0600. Existing file
permissions are preserved. SQLite timeout is 200 ms so a locked archive cannot
block the UI for seconds. Database startup/write failure is reported without
stopping live notification rendering; write failure disables recording for the
remaining run. View/clear failures return a command-line error.

Automated checks cover persistence across reconnects, separate replacement
entries, retention, clearing, rules filtering, queue deduplication, storage
failure, display-independent CLI commands and XDG path selection.

Settings → History provides Refresh, Clear, and case-insensitive search across up to 1,000
stored arrivals by app, title, and body. Search treats punctuation literally. Export UI
is not implemented.
