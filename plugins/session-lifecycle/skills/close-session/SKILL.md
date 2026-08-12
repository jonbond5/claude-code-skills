---
name: close-session
description: Officially close the current session — disclose anything still running, write the closing summary, then rename the session to CLOSED_<name> so the agent list shows the thread is finished. Renames both the job state and the session registry, verifies against `claude agents`, and records the close. Reversible with reopen. Use when a session's work is done and you want it filed rather than left open.
disable-model-invocation: true
argument-hint: [optional one-line note recorded with the close]
---

# /close-session

Filing, not killing. This marks a thread **finished** so the agent list stops looking like it has
seven live conversations in it, and it leaves a record of when and from what name.

**It does not stop the session.** The process keeps running and can still take messages. Closing is
a label on the work, not a kill — say so if the user seems to expect the session to end.

## Step 1 — Do not close over live work

Check, in this order, and **report what you find before doing anything else**:

1. **Tracked agents and background jobs.** `TaskList` for anything `in_progress`; any background
   Bash you started this session. **A live tracked agent is the one blocking condition** — closing
   over it files the thread as done while its result is still in flight, and nobody will look at a
   CLOSED_ session again. Say what is running and ask before proceeding.
2. **Orphan processes you spawned** — a training run, a batch job, a container, anything that
   outlives the session that started it. These do not block, but a close that hides one is a close
   that lies. Name them with their PIDs.
3. **Uncommitted work** in any repo this session touched. `git status --porcelain`. Name the paths,
   and name the branch if a merge decision is still open.

If the user has already said "close it" a second time after hearing the above, that is their
decision. Proceed.

## Step 2 — Capture before you file

Two of your existing session-end skills earn their keep here, and neither runs automatically:

- **`/distill`** — if this session produced a correction, a stated rationale, or a repeated
  workflow, it belongs on a rules surface *before* the transcript stops being read. It needs the
  live transcript, so it cannot run after the fact and cannot be delegated.
- **`/docker-sweep`** — if this session built images or ran throwaway containers.

A session with nothing to capture skips both.

## Step 3 — Close it

```
python3 ~/.claude/skills/close-session/scripts/close_session.py status
python3 ~/.claude/skills/close-session/scripts/close_session.py close --note "<one line>"
```

Run `status` first — it prints the current name, both surfaces, what `claude agents` reports, and
any prior close record. **Gate the close on its exit status.** Non-zero from `close` means the
session is NOT closed:

| Exit | Meaning |
|---|---|
| 0 | renamed and verified — both surfaces re-read, and `claude agents` agrees |
| 2 | already closed; nothing changed. `--force` re-closes, `reopen` undoes |
| 3 | nothing renamed, or the files and the CLI disagree — **report the failure, do not claim it closed** |

### The naming rule

`CLOSED_` + the current name, with one deliberate exception: **a leading `OPEN_` is swapped, not
stacked.** `OPEN_edge-frontier-followons` becomes `CLOSED_edge-frontier-followons`, because that is
how sessions are filed under this convention — `OPEN_x` and `CLOSED_x` are the same thread in two
states, never `CLOSED_OPEN_x`. Pass `--literal` for the strict reading (prefix whatever is there).

The close also pins `nameSource: user`, which is what stops the harness auto-renaming a closed
session back to a summary of its first prompt.

### Where the name lives

| Surface | Applies to |
|---|---|
| `~/.claude/jobs/<jobId>/state.json` | background sessions (`$CLAUDE_JOB_DIR`) |
| `~/.claude/sessions/<pid>.json` | any session with a registry entry (`$CLAUDE_PID`) |
| `~/.claude/session-closes/<sessionId>.json` | the close record this skill writes and reads |

Both name surfaces are written and each is verified by re-reading, because **the live session
process rewrites them on its own schedule.** MEASURED 2026-08-01 on a busy background session: the
rename held across two subsequent process rewrites, so the process merges rather than overwriting
from memory. An interactive session with no registry entry cannot be renamed this way — the script
exits 3 and says so rather than reporting a success it did not achieve.

## Step 4 — Report

The four fields, and the new name. Nothing else:

```
status:    done | stuck | partial
headline:  one sentence
open:      <what was left unfinished>
needs_you: <orphan processes, uncommitted paths, unmerged branches, parked items>
closed as: CLOSED_<name>
```

**The new name is stated in full** — this is the case where the identifier *is* the answer, so the
usual ban on identifiers in summaries does not apply. Nothing else about the mechanics belongs in
the reply: no file paths, no exit codes, no surface-by-surface narration. A rename that only
partially landed is decision-relevant and stays.

## Undo

```
python3 ~/.claude/skills/close-session/scripts/close_session.py reopen [--open-prefix]
```

Strips `CLOSED_` and deletes the close record. `--open-prefix` files it back as `OPEN_<name>`.
Closing is meant to be cheap to reverse — if a closed thread turns out to have one more question in
it, reopen rather than starting a session that has lost the context.

## Bounds

- **Closing does not end the process, free its memory, or stop a cron/monitor loop it started.**
  Anything on a recurring wake keeps waking. If the user wants it stopped, that is a separate act —
  name it in `needs_you`.
- **It does not archive or delete the transcript.** The session remains resumable under its new name.
- **It renames one session: the one running the skill.** It has no way to reach a sibling session,
  and it should not — closing someone else's live thread from inside this one is exactly the
  shared-state accident these rules exist to prevent.
