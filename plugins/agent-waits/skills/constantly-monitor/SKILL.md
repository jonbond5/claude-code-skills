---
name: constantly-monitor
description: Set up a recurring, self-healing wake loop that re-invokes you every N minutes to run a user-defined task (poll a log, watch a job, babysit a process), then go idle until the next tick. Uses a recurring CronCreate job as the wake trigger — survives rate-limit windows because each scheduled fire is independent (a wake lost to a quota window is picked up by the next). Use for constant/periodic monitoring where you must keep checking on a fixed cadence. Do NOT use for a single bounded wait (use /sleep-gate), for waking the instant a specific event happens (use Monitor / a backgrounded `until` loop), or for sub-minute cadence (cron is minute-granular).
---

# Constantly monitor

Arms a **recurring cron job** (`CronCreate`) that re-injects a task prompt into this
session every N minutes. On each fire you run the task, append one log line, and go
idle. The cron keeps firing on wall-clock time regardless of what happened on the
previous tick — so the loop is **self-healing**: a wake swallowed by a rate-limit
window is simply followed by the next scheduled fire once quota returns.

This is the recurring counterpart to `/sleep-gate` (which is a *single* `sleep`→wake
bridge). Pick this when the answer to "how often?" is "again and again, forever, until I
stop it" — not "once, after this wait."

## Invocation

`/constantly-monitor <interval> -- <task>`

Examples:
- `/constantly-monitor 15m -- run ./poll.sh, and if it prints HALT, clear it and restart the service`
- `/constantly-monitor 5m -- check the CI run for PR 412; note any newly-failed check in monitor_log.md`
- `/constantly-monitor 30m -- tail the training log; if loss is NaN, stop the run and alert me`
- `/constantly-monitor` → ask for interval and task

`<interval>` is in minutes/hours (`5m`, `15m`, `1h`, or a bare number = minutes). The
task is everything after `--`.

## Phase 0 — parse & confirm

This follows the self-sufficient-wake rule (`sleep-gate/SKILL.md`) — a wake is armable only when it
is self-sufficient. The checks below are this skill's own cadence-specific instances of it: interval
parsing, the 7-day expiry, and the refuse-and-redirect cases.

1. Parse `<interval>` to a minute count. **Refuse and redirect** if:
   - Sub-minute (`< 1m`) → cron is minute-granular; use a backgrounded `until` loop or `Monitor`.
   - The user actually wants to wake *the instant* a specific event occurs (file change, job
     completion, "tell me when X is ready") → that's event-driven; use `Monitor` or
     `Bash(run_in_background=true)` with an `until` loop, not a polling cron.
   - It's truly a one-shot "wait then do X once" → use `/sleep-gate`.
2. If interval or task is missing, ask for it — the task text must additionally be self-contained
   across ticks, since chat context may be compacted between wakes and it can't rely on "what we
   were just discussing."
3. Confirm the cadence + the 7-day auto-expiry (see Hard rules) back to the user in one line.

## Phase 1 — arm the monitor

### 1a. Choose the cron expression (avoid the top-of-minute pileup)

For "every N minutes", do NOT use `*/N * * * *` (fires on :00, which every cron on the
planet also does). Offset it: `<M>-59/<N> * * * *` where `M` is a small offset `1..9`
(and `M < N`). Examples:
- 15m → `7,22,37,52 * * * *` (i.e. `7-59/15`)
- 5m  → `2-59/5 * * * *`
- 10m → `3-59/10 * * * *`
- 60m → `17 * * * *`
(N that doesn't divide 60, e.g. 7, leaves a short gap at each hour boundary — fine for monitoring.)

### 1b. Write the state dir + breadcrumb (survives context compaction)

```bash
label="<short-kebab-label-for-this-monitor>"
state_dir="$HOME/.claude/constantly-monitor/$label"
mkdir -p "$state_dir"
```
Write `$state_dir/breadcrumb.md` containing, verbatim: the task, the interval/cron, the
per-wake procedure (below), the decision rules, any paths involved, and a "STOP: CronDelete
<id>" line (fill the id in after 1c). Initialize `$state_dir/monitor_log.md` with a header.
If the task involves acting on a target's state, also write a one-shot, **token-free**
`poll.sh` into the state dir that dumps every signal the task needs in a single run, so each
wake is one cheap Bash call rather than many.

### 1c. Create the recurring cron

```
CronCreate(
  cron: "<expr from 1a>",
  recurring: true,
  durable: true,          # persist to .claude/scheduled_tasks.json so it survives a
                          # session restart. NOTE: may report "session-only" if the
                          # durable lock is contended; that's acceptable — the session
                          # process must be alive for fires to run either way.
  prompt: "<WAKE PROMPT, see Phase 2 — fully self-contained>"
)
```
Record the returned **job id** in the breadcrumb's STOP line. If a prior stale
`.claude/scheduled_tasks.lock` (dead pid) blocks durable persistence, remove it and retry.

### 1d. (optional) faster-than-cadence event catch

If the user also wants to react the *instant* something happens between ticks (e.g. a
service comes back up), additionally arm a one-shot detector that wakes you immediately:
```
Bash(run_in_background=true, command='base=...; while :; do <cond> && { echo HIT; break; }; sleep 15; done')
```
Re-arm a fresh one each time it fires. This complements (does not replace) the cron.

After arming, write the user one line: cadence, job id, where the log lives. **Then stop.**

## Phase 2 — the wake prompt / per-wake procedure

The `prompt` you pass to CronCreate is what gets re-injected each tick. It must be
self-contained. Template:

> [MONITOR WAKE — <label>] Recurring task, every <interval>. Do exactly this, conserving
> tokens: (1) If this is your first wake this session or context looks unfamiliar/compacted,
> read `<state_dir>/breadcrumb.md` first. (2) <THE USER'S TASK, verbatim — incl. running
> `<state_dir>/poll.sh` if one exists>. (3) Append ONE line to `<state_dir>/monitor_log.md`
> via `printf '...' >>` (do not read the whole file). (4) If something needs the user's
> attention, surface it (update a summary file and/or PushNotification per the task). (5)
> Then STOP and stay idle until the next wake.

On each actual fire, follow that procedure. Keep a healthy wake to ~2–3 tool calls —
the monitor shares the account's quota with whatever it's watching, so cheap wakes matter.
If several wakes queued up while you were busy/rate-limited, **collapse them into one**
poll rather than repeating the task N times.

## Stopping

`CronDelete <job-id>` (the id is in the breadcrumb's STOP line, or via `CronList`). Also
`TaskStop` any one-shot detector from 1d. Tell the user it's stopped.

## Hard rules / gotchas

1. **Cron fires only while the REPL is idle.** If a fire lands mid-turn it's deferred, not
   lost — it runs when you next go idle. This is why rate-limit windows are survivable.
2. **Recurring jobs auto-expire after 7 days** (one final fire, then deleted). Tell the
   user. For longer, recreate before expiry.
3. **Jitter:** recurring fires land up to 10% of the period late (max 15 min). Don't design
   the task to need exact wall-clock precision.
4. **The session process must stay alive.** Any in-session wake mechanism (cron, ScheduleWakeup,
   sleep-gate) needs the Claude process running. `durable: true` survives a *restart* (reloads
   from `.claude/scheduled_tasks.json`) but does not by itself relaunch a dead process.
5. **Self-heal:** if you're ever awake and `CronList` shows the monitor job missing while the
   task still needs running, recreate it with the same expression + wake prompt.
6. **One task per wake; idempotent.** Don't let a long task overrun the interval such that
   wakes pile up faster than you clear them. If they do, collapse and consider a longer interval.
7. **Don't use this for a single wait** (→ `/sleep-gate`) **or to catch an event the moment it
   happens** (→ `Monitor` / backgrounded `until` loop). Cron is for *fixed-cadence* polling.

## Files
- `~/.claude/skills/constantly-monitor/SKILL.md` — this file
- `~/.claude/constantly-monitor/<label>/breadcrumb.md` — durable task + policy + STOP line
- `~/.claude/constantly-monitor/<label>/monitor_log.md` — one line per wake
- `~/.claude/constantly-monitor/<label>/poll.sh` — optional token-free per-wake poll
