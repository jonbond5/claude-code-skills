#!/usr/bin/env bash
# Write the resume breadcrumb file.
# Args: <state_dir> <duration_seconds> <reason> [<on_resume_payload_file>]
set -euo pipefail

state_dir="${1:?state_dir required}"
duration="${2:?duration_seconds required}"
reason="${3:-bridge rate-limit window}"
payload_file="${4:-}"

mkdir -p "$state_dir"
now=$(date -Iseconds)
# Prefer GNU date; fall back to BSD date if GNU is absent.
if wake_at=$(date -d "+$duration seconds" -Iseconds 2>/dev/null); then
  :
else
  wake_at=$(date -v+"${duration}S" -Iseconds 2>/dev/null || echo "(could not compute)")
fi

project_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
branch=""; head=""; dirty=0
if git -C "$project_root" rev-parse --git-dir &>/dev/null; then
  branch=$(git -C "$project_root" branch --show-current 2>/dev/null || true)
  head=$(git -C "$project_root" rev-parse --verify --quiet HEAD 2>/dev/null || true)
  dirty=$(git -C "$project_root" status --porcelain 2>/dev/null | wc -l || echo 0)
fi

payload="(no on-resume payload provided)"
if [[ -n "$payload_file" && -f "$payload_file" ]]; then
  payload=$(cat "$payload_file")
fi

cat > "$state_dir/on-resume.md" <<EOF
# Sleep-gate breadcrumb

started_at: $now
wake_eta:   $wake_at
duration_s: $duration
reason:     $reason
project:    $project_root
git_branch: $branch
git_head:   $head
dirty_files_at_sleep: $dirty

## ON RESUME

$payload
EOF

# Also drop a pointer to "current" for easy lookup on wake
ln -sfn "$state_dir" "$HOME/.claude/sleep-gate/state/current"

echo "$state_dir/on-resume.md"
