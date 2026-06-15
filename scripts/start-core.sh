#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

export CORE_HOST="${CORE_HOST:-127.0.0.1}"
export CORE_PORT="${CORE_PORT:-3040}"
export CORE_DB_PATH="${CORE_DB_PATH:-$ROOT/data/conversations.db}"

exec uvicorn main:app --host "$CORE_HOST" --port "$CORE_PORT" --workers 1
