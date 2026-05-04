#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOST="${API_HOST:-127.0.0.1}"
PORT="${API_PORT:-8000}"
LOG_DIR="${ROOT_DIR}/logs/backend"
CONSOLE_LOG="${LOG_DIR}/api-console.log"
DEFAULT_PYTHON_BIN="/home/pulkitv52/miniconda3/envs/valuation-poc/bin/python"
PYTHON_BIN="${PYTHON_BIN:-$DEFAULT_PYTHON_BIN}"

cd "$ROOT_DIR"
mkdir -p "$LOG_DIR"

# Fix PROJ database path for conda environments (geopandas/pyproj)
CONDA_PROJ="${DEFAULT_PYTHON_BIN%/bin/python}/share/proj"
SYSTEM_PROJ="/usr/share/proj"
if [[ -d "$CONDA_PROJ" ]]; then
  export PROJ_LIB="$CONDA_PROJ"
elif [[ -d "$SYSTEM_PROJ" ]]; then
  export PROJ_LIB="$SYSTEM_PROJ"
fi

if [[ ! -x "$PYTHON_BIN" && -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python interpreter not found." >&2
  echo "Tried: $DEFAULT_PYTHON_BIN and $ROOT_DIR/.venv/bin/python" >&2
  echo "Set PYTHON_BIN explicitly if your project interpreter lives elsewhere." >&2
  exit 1
fi

exec "$PYTHON_BIN" -m uvicorn backend.src.api:app --reload --host "$HOST" --port "$PORT" 2>&1 | tee -a "$CONSOLE_LOG"
