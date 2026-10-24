#!/bin/bash
# Load only dedicated provider/project variables, never the application .env.
set -euo pipefail
umask 077
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f "$REPO_DIR/terraform/.env" ]]; then
  echo 'Configure terraform/.env from terraform/.env.example first.' >&2
  exit 1
fi
set -a
source "$REPO_DIR/terraform/.env"
set +a
exec terraform -chdir="$REPO_DIR/terraform" "$@"
