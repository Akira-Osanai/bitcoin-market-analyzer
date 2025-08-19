#!/usr/bin/env bash
set -euo pipefail

# Daily cron setup for running the analyzer via Docker Compose

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
SCRIPTS_DIR="$PROJECT_DIR/scripts"
RUN_SCRIPT="$SCRIPTS_DIR/run_daily.sh"
LOG_DIR="$PROJECT_DIR/logs"

# Default: run at 06:00 every day. Override by exporting SCHEDULE before running this script.
SCHEDULE="${SCHEDULE:-0 6 * * *}"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

mkdir -p "$SCRIPTS_DIR" "$LOG_DIR"

cat > "$RUN_SCRIPT" <<'EOS'
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
EOS

chmod +x "$RUN_SCRIPT"

# Install or update crontab entry
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

# Preserve existing entries excluding ours
(crontab -l 2>/dev/null || true) | grep -v "$RUN_SCRIPT" > "$TMP_CRON"

echo "$SCHEDULE $RUN_SCRIPT" >> "$TMP_CRON"

crontab "$TMP_CRON"

echo "Installed cron entry:"
echo "$SCHEDULE $RUN_SCRIPT"
echo "Logs will be written to: $LOG_DIR/cron.log"


