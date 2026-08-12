#!/usr/bin/env bash
# On wake: detect drift between snapshot and current state.
# Args: <state_dir>   (use "current" to follow the symlink)
# Exit 0 if clean, 1 if drift, 2 if breadcrumb missing.
set -uo pipefail

raw="${1:?state_dir required}"
if [[ "$raw" == "current" ]]; then
  state_dir="$HOME/.claude/sleep-gate/state/current"
else
  state_dir="$raw"
fi
breadcrumb="$state_dir/on-resume.md"
if [[ ! -f "$breadcrumb" ]]; then
  echo "resume: ERROR breadcrumb missing at $breadcrumb" >&2
  exit 2
fi

# Extract snapshot values
snap_branch=$(awk -F': *' '/^git_branch:/{print $2; exit}' "$breadcrumb")
snap_head=$(awk -F': *' '/^git_head:/{print $2; exit}' "$breadcrumb")
project_root=$(awk -F': *' '/^project:/{print $2; exit}' "$breadcrumb")

drift=0
cur_branch=""; cur_head=""
if [[ -n "$project_root" ]] && git -C "$project_root" rev-parse --git-dir &>/dev/null; then
  cur_branch=$(git -C "$project_root" branch --show-current 2>/dev/null || true)
  cur_head=$(git -C "$project_root" rev-parse --verify --quiet HEAD 2>/dev/null || true)
fi

echo "resume: project=$project_root"
echo "resume: branch snap='$snap_branch'  current='$cur_branch'"
echo "resume: head   snap='$snap_head'  current='$cur_head'"

if [[ -n "$snap_branch" && "$snap_branch" != "$cur_branch" ]]; then
  echo "resume: DRIFT branch changed"
  drift=1
fi
if [[ -n "$snap_head" && "$snap_head" != "$cur_head" ]]; then
  echo "resume: DRIFT git HEAD changed"
  drift=1
fi

if [[ "$drift" -eq 0 ]]; then
  echo "resume: state matches snapshot (no drift)"
fi
exit "$drift"
