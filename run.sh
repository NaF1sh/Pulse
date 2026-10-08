#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -x .venv/bin/python ]]; then
    echo "Pulse's development environment is missing. Run ./install.sh to install, or follow docs/development.md." >&2
    exit 1
fi
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
exec .venv/bin/python -m pulse.main "$@"
