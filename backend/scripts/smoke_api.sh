#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEFAULT_PYTHON_BIN="/home/pulkitv52/miniconda3/envs/valuation-poc/bin/python"
PYTHON_BIN="${PYTHON_BIN:-$DEFAULT_PYTHON_BIN}"

cd "$ROOT_DIR"

if [[ ! -x "$PYTHON_BIN" && -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python interpreter not found." >&2
  echo "Tried: $DEFAULT_PYTHON_BIN and $ROOT_DIR/.venv/bin/python" >&2
  echo "Set PYTHON_BIN explicitly if your project interpreter lives elsewhere." >&2
  exit 1
fi

MPLCONFIGDIR=/tmp/matplotlib "$PYTHON_BIN" - <<'PY'
from fastapi.testclient import TestClient

from backend.src.api import app

with TestClient(app) as client:
    response = client.get('/health')
    print('status:', response.status_code)
    print('body:', response.json())
PY
