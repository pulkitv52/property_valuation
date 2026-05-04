#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
LOG_DIR="${ROOT_DIR}/logs/frontend"
BUILD_LOG="${LOG_DIR}/vite-build.log"

mkdir -p "$LOG_DIR"
cd "$FRONTEND_DIR"
exec npm run build 2>&1 | tee -a "$BUILD_LOG"
