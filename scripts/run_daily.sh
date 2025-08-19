#!/usr/bin/env bash
set -euo pipefail

# Ensure Docker is found in cron environment
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Start analyzer" >> "$LOG_DIR/cron.log"
docker compose -f "$PROJECT_DIR/docker-compose.yml" run --rm analyzer >> "$LOG_DIR/cron.log" 2>&1 || {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Analyzer failed" >> "$LOG_DIR/cron.log"
  exit 1
}
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Done" >> "$LOG_DIR/cron.log"
