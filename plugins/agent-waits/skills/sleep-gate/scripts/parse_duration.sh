#!/usr/bin/env bash
# Convert a human-friendly duration to seconds.
# Accepts: "30s", "3m", "1h", "5h", or raw seconds ("90").
# Prints the integer seconds on stdout. Exits non-zero on bad input.
set -euo pipefail
arg="${1:-}"
if [[ -z "$arg" ]]; then
  echo "ERROR: missing duration (use 30s, 3m, 1h, etc.)" >&2
  exit 2
fi
if [[ "$arg" =~ ^([0-9]+)(s|m|h)?$ ]]; then
  n="${BASH_REMATCH[1]}"
  u="${BASH_REMATCH[2]:-s}"
  case "$u" in
    s) echo "$n" ;;
    m) echo $(( n * 60 )) ;;
    h) echo $(( n * 3600 )) ;;
  esac
else
  echo "ERROR: bad duration '$arg' (use 30s, 3m, 1h, etc.)" >&2
  exit 2
fi
