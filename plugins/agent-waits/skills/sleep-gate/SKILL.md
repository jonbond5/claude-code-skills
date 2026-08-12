---
name: sleep-gate
description: Bridge an agent across a rate-limit window (or other bounded wait) without burning tokens during the wait. Captures durable resume state, runs a pre-sleep checklist, then kicks off `Bash(command="sleep N", run_in_background=true)` so the harness fires a `<task-notification>` on wake. The agent resumes from a breadcrumb file. Use when work continues across a quota reset and the user is stepping away. Do NOT use for context-window pressure, event-driven waits (use Monitor), inside `/loop` (use ScheduleWakeup), or short waits (< ~1 minute).
---

# Sleep gate

Pauses the session via a backgrounded `sleep`. The agent's turn ends immediately; no tokens flow while `sleep` is running. When the sleep exits, the harness pushes a `<task-notification>` into the session and the agent is re-invoked. The agent resumes from a breadcrumb file written before sleeping.

The mechanism is two lines of tool call. The *value* is in the pre-sleep checklist — without it, the agent wakes into a broken state.

## Invocation

`/sleep-gate <duration> [-- <on-resume payload>]`

Examples:
- `/sleep-gate 5h -- continue PR cleanup from step 4, autonomous mode active, see memory file X`
- `/sleep-gate 3m -- (test) verify wake works; then print "WAKE OK"`
- `/sleep-gate` → asks for duration

`<duration>` accepts `30s`, `3m`, `2h`, or raw seconds. The on-resume payload is everything after `--`; if omitted, ask the user.

## Pre-flight: the self-sufficient-wake rule

**A scheduled wake is armable only when it is self-sufficient** — everything the agent needs to act
correctly on wake must already be on disk or in the task list, because nothing else will be present
to fill a gap when the notification fires. Every check below is this one principle applied at a
different point in the flow:

1. **Duration and on-resume payload must both be present.** Ask for whichever is missing (Phase 0).
2. **No other harness-tracked background job may be in flight.** Wait for it or surface the conflict
   instead of sleeping (Phase 1).
3. **Every pre-sleep checklist item must pass.** Any failure surfaces and blocks the sleep until
   resolved or explicitly waived (Phase 1).
4. **The payload must be actionable without re-prompting.** Never sleep and then ask the user, unless
   the payload itself says "ask first" (Hard rules).
5. **On wake, drift is surfaced before the payload executes.** `resume_check.sh` runs first; any
   drift is reported before proceeding (Phase 4).

`constantly-monitor` is this same rule applied to a recurring cadence instead of a single wait — see
that skill's Phase 0 for its own cadence-specific checks (interval parsing, the 7-day expiry, the
refuse-and-redirect cases).

## Phase 0 — Parse and confirm

1. Parse `<duration>` via `~/.claude/skills/sleep-gate/scripts/parse_duration.sh <arg>`. If parsing fails or `<duration>` is missing, ask the user.
2. If no on-resume payload was passed, ask: *"What should I do when I wake up?"* The answer becomes the payload. If the user wants to be re-prompted on wake, the payload should literally say "ask the user before doing anything".
3. **Refuse and explain** if any of these hold:
   - The wait is event-driven (CI run, queue drain, file change) → use Monitor instead
   - Session is in `/loop` mode → use `ScheduleWakeup`
   - Parsed seconds < 60 → just continue working synchronously
   - Conversation is near the context-window cap → compact first; the session may be terminated mid-sleep

## Phase 1 — Pre-sleep checklist

Run `~/.claude/skills/sleep-gate/scripts/preflight.sh` and read the output (git branch/HEAD, dirty files, any existing `sleep` processes owned by the user).

Then walk this checklist as the model:

- **Task list captured.** Call TaskList. If there is no task that says what to do on wake, create one with subject "Sleep-gate resume" whose description includes the verbatim on-resume payload and the path to the breadcrumb.
- **Pending feedback memory saved.** If the user gave guidance this session that should survive a compact, write it to memory now.
- **Outstanding background work.** If another `run_in_background` job is in flight that you care about, do NOT sleep — wait for it or surface the conflict.
- **Autonomous-mode flag noted.** If the user put the session into an autonomous mode (no questions, chain agents, etc.), make sure that mode is named explicitly in the on-resume payload.
- **In-progress plans on disk.** Anything decision-relevant for post-wake must live in a file, not chat memory alone.

If any check fails, surface it and stop (the self-sufficient-wake rule) — do not sleep until the user resolves it or explicitly waives it.

## Phase 2 — Snapshot

Build a per-sleep state directory and write the breadcrumb:

```bash
ts=$(date -Iseconds | tr ':' '-')
state_dir="$HOME/.claude/sleep-gate/state/$ts-$$"
mkdir -p "$state_dir"

# Save the on-resume payload to a file (use the exact text the user provided)
payload_file="$state_dir/payload.txt"
printf '%s\n' "<verbatim on-resume payload here>" > "$payload_file"

~/.claude/skills/sleep-gate/scripts/snapshot.sh \
  "$state_dir" <duration_seconds> "<short reason>" "$payload_file"
```

`snapshot.sh` writes `$state_dir/on-resume.md` with the payload plus git branch/HEAD snapshots, and updates `~/.claude/sleep-gate/state/current` to point at this dir.

Log the start:

```bash
~/.claude/skills/sleep-gate/scripts/log_event.sh sleep-start <duration_seconds> "<short reason>"
```

Create or update a TaskCreate entry whose description includes:
- `state_dir` path
- Verbatim ON RESUME payload
- The phrase "ON WAKE: read $state_dir/on-resume.md, run scripts/resume_check.sh, then execute the payload"

## Phase 3 — Kick off the background sleep

Call Bash exactly once:

```
Bash(
  command = "sleep <duration_seconds>",
  run_in_background = true,
  description = "sleep-gate <duration_seconds>s — state at <state_dir>"
)
```

After Bash returns the job/task id, write one short user-facing line: paused for X, ETA Y, breadcrumb at `<state_dir>`. **Then stop.** Do not call any other tool this turn. Do not poll.

## Phase 4 — On wake (handle the task-notification)

When you receive a `<task-notification>` that the sleep job has completed, this is the first thing you do:

1. **Acknowledge briefly.** One sentence to the user: "Sleep-gate woke up."
2. **Locate the breadcrumb.** Read `~/.claude/sleep-gate/state/current/on-resume.md` (it's a symlink to the most recent state dir). If `current` is missing or stale, find the newest directory under `~/.claude/sleep-gate/state/`.
3. **Drift check.**
   ```bash
   ~/.claude/skills/sleep-gate/scripts/resume_check.sh current
   ```
   Exit 0 = clean, 1 = drift, 2 = breadcrumb missing. On drift, surface it to the user as a finding before proceeding.
4. **Log wake.**
   ```bash
   ~/.claude/skills/sleep-gate/scripts/log_event.sh sleep-wake <duration_seconds> ok
   ```
5. **Execute the ON RESUME payload from the breadcrumb.** If the payload literally says "ask the user", ask. Otherwise resume per the payload — including any autonomous-mode chaining that was named.

## Hard rules

1. **Background sleep only.** Never `time.sleep()` inside agent code. Never foreground `sleep` in Bash. Never `sleep N && <work>` — chaining converts the wait into a foreground operation and defeats the technique.
2. **No polling during the wait.** No "check if it's done" Bash calls. The harness fires `<task-notification>` on exit. Trust it.
3. **Breadcrumb is the source of truth.** Anything decision-relevant post-wake must be in `on-resume.md`, not chat memory alone — chat may be compacted across the wait.
4. **Don't sleep across a context-window cliff.** Long sessions near the cap may be terminated mid-sleep. Compact first if so.
5. **One sleep at a time** — the self-sufficient-wake rule's background-job check (Phase 1); notifications can interleave otherwise.
6. **Echo long sleeps back.** ≥ 1h: state the wall-clock wake time in Phase 0.
7. **Don't sleep, then ask the user.** Per the self-sufficient-wake rule, the payload must be specific enough that the agent can act on wake without re-prompting (unless the payload itself is "ask first").

## Anti-patterns to refuse

- "Sleep, then ping me when you wake up." Agent should keep time, not delegate the wakeup back to the user.
- "Sleep, then check if X is done." That's an event wait — use Monitor on the event source.
- "Sleep, but actually I just want to compact." Use the compaction skill instead; sleep does not shrink context.
- Sleeping inside a subagent. Always sleep from the main session.
- Sleeping without a breadcrumb. If there's nothing on disk, the wake has no resume target.

## Telemetry

Events append to `~/.claude/sleep-gate/telemetry.log` as TSV: `<iso_ts>\t<event>\t<duration_s>\t<reason_or_status>`. Events emitted: `sleep-start`, `sleep-wake`.

## Files

- `~/.claude/skills/sleep-gate/SKILL.md` — this file
- `~/.claude/skills/sleep-gate/scripts/parse_duration.sh` — duration → seconds
- `~/.claude/skills/sleep-gate/scripts/preflight.sh` — pre-sleep advisories
- `~/.claude/skills/sleep-gate/scripts/snapshot.sh` — writes breadcrumb
- `~/.claude/skills/sleep-gate/scripts/resume_check.sh` — drift detection on wake
- `~/.claude/skills/sleep-gate/scripts/log_event.sh` — telemetry
- `~/.claude/sleep-gate/state/<ts>-<pid>/on-resume.md` — per-sleep breadcrumbs
- `~/.claude/sleep-gate/state/current` — symlink to the most recent breadcrumb dir
- `~/.claude/sleep-gate/telemetry.log` — append-only event log
