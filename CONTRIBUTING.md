# Contributing

Pulse is an early preview. Small changes with a clear user benefit are easiest to review.

1. Describe the problem and your desktop environment in an issue.
2. Make a focused change and follow [the development setup](docs/development.md).
3. Run the checks relevant to the change. Include a screenshot or short recording for visual work.
4. In your pull request, explain the before/after behavior, validation, and desktop limitations.

Never include real notification text, tokens, or personal configuration in fixtures and screenshots. Use synthetic data.

The most useful testing right now covers notification replacement, reconnects, app activation, multiple monitors, display scaling, and suspend/resume. See [release readiness](docs/release-readiness.md).
