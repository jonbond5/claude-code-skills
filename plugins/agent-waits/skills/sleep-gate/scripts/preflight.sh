#!/usr/bin/env bash
# Pre-sleep advisories. Reports each finding on its own line.
# Always exits 0 — the model decides whether to proceed.
set -uo pipefail

project_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
echo "preflight: project_root=$project_root"

if git -C "$project_root" rev-parse --git-dir &>/dev/null; then
  branch=$(git -C "$project_root" branch --show-current 2>/dev/null)
  [[ -z "$branch" ]] && branch="(detached)"
  head=$(git -C "$project_root" rev-parse --verify --quiet HEAD 2>/dev/null)
  [[ -z "$head" ]] && head="(none)"
  dirty=$(git -C "$project_root" status --porcelain 2>/dev/null | wc -l)
  echo "preflight: git branch=$branch head=$head dirty_files=$dirty"
  if [[ "$dirty" -gt 0 ]]; then
    echo "preflight: WARN dirty working tree — consider committing or stashing before sleep"
  fi
else
  echo "preflight: not a git repo (skipping git checks)"
fi

# Surface anything that looks like an in-flight ad-hoc shell process owned by current user
# (this is a heuristic; the harness's own bg-job ledger is authoritative)
bg_sleeps=$(pgrep -u "$USER" -x sleep 2>/dev/null | wc -l)
if [[ "$bg_sleeps" -gt 0 ]]; then
  echo "preflight: NOTE $bg_sleeps existing 'sleep' process(es) owned by $USER — confirm they are not yours-from-an-earlier-gate"
fi
