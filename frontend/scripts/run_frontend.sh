#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
LOG_DIR="${ROOT_DIR}/logs/frontend"
DEV_LOG="${LOG_DIR}/vite-dev.log"

mkdir -p "$LOG_DIR"
cd "$FRONTEND_DIR"
npm install
exec npm run dev 2>&1 | tee -a "$DEV_LOG"
