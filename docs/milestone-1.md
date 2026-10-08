# Milestone 1 — fake notifications

In progress. Milestone 0 was accepted by the user on 2026-10-08.

Implemented: pure Python notification model and priority queue; FIFO for equal
priorities; preemption; active and queued ID replacement; monotonic timeouts;
Qt controller; scripted fake source; content-sized message cards with two-line
bodies and plain-text rendering. Interrupted cards return to the queue and get
a fresh timeout when resumed. Zero or negative timeout means persistent.

Run `./run.sh --demo --debug`. The 22-second loop exercises queueing, a battery
interruption, download progress and completion, a media card, volume changes,
timeouts and return to idle. Left-click
dismisses the active card; right-click opens the pet picker (with a Quit Pulse button). Without `--demo`, click the idle
pill to manually expand/collapse.

Progress and level cards include animated percentage meters; media cards show
track, artist and a now-playing label. All values are simulated. Different
cards use fade-out/swap/fade-in transitions; updates with the same ID preserve
content visibility and animate meter values. Exit fades content before shrinking
the shape; arrivals during exit cancel the pending collapse. Reduced motion
uses short fades and immediate meter updates. Card height still fits content.

Still to do before accepting M1: desktop visual tuning and checks for
interruptions, long text, and reduced motion. Overlapping content cross-fades
are not implemented; the current transition is sequential. The
debug phase is derived from rendered width; the controller currently exposes
content and queue state rather than an animation lifecycle state machine.

Real D-Bus notifications, themes, history and system integrations are later work.
