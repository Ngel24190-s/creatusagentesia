#!/bin/bash
# NosVers Nightly Agent Run + Dashboard
# Scheduled via crontab to run at 2:00 AM daily
#
# After the agents finish, it generates the HTML dashboard
# and sends a Telegram notification.

set -euo pipefail

PROJECT_DIR="/home/user/creatusagentesia"
VENV="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"
LOGFILE="$LOG_DIR/nightly_$(date +%Y-%m-%d).log"

mkdir -p "$LOG_DIR"

echo "=== NosVers Nightly Run — $(date) ===" >> "$LOGFILE"

# Activate venv
source "$VENV/bin/activate"

cd "$PROJECT_DIR"

# Run all agents
echo "[$(date +%H:%M:%S)] Running all agents..." >> "$LOGFILE"
python orchestrator.py --run-all >> "$LOGFILE" 2>&1 || true

# Generate HTML dashboard
echo "[$(date +%H:%M:%S)] Generating dashboard..." >> "$LOGFILE"
python dashboard.py --no-open >> "$LOGFILE" 2>&1 || true

# Note: --run-all already sends a Telegram notification via notifier,
# so we skip the separate --notify call to avoid duplicate messages.

echo "[$(date +%H:%M:%S)] Nightly run complete." >> "$LOGFILE"
echo "=======================================" >> "$LOGFILE"
