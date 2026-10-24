#!/bin/bash
# Same SSH -> remote Git pull -> rebuild/restart workflow as the n8n project.
set -euo pipefail
MERCY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$MERCY_ROOT/deploy/redeploy.py" "$@"
