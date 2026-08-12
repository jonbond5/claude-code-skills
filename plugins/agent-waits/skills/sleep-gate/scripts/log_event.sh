#!/usr/bin/env bash
# Append a telemetry line.
# Args: <event> <duration_s> <reason_or_status>
set -uo pipefail
log="$HOME/.claude/sleep-gate/telemetry.log"
mkdir -p "$(dirname "$log")"
printf '%s\t%s\t%s\t%s\n' \
  "$(date -Iseconds)" \
  "${1:-?}" \
  "${2:-?}" \
  "${3:-?}" \
  >> "$log"
