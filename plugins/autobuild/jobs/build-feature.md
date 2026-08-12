# Job: build a feature

The main recipe. Everything here runs on git, the task list, and subagents. There is no CLI to call
and no state to register — if a step below reads like bookkeeping, it is a git command.

## 1. Anchor the ask

Open the run note (`SKILL.md` step 4) and record the user's ask **verbatim**. Pick a `<slug>` — two
or three words from the ask plus four random characters, e.g. `retry-backoff-k7f2`. That slug is your
branch namespace and your run note's filename, and its uniqueness is the only thing separating you
from another session building in this same repository.

Derive **1–5 binary, observable** acceptance criteria — "done when the endpoint returns 200 for a
valid payload", never "improve the API".

If the ask is too vague to yield a single observable criterion, that is the one question worth asking
— see the asking rule at the top of `SKILL.md`, which owns it. Otherwise derive the criteria, state
the assumption you made, and carry on.

Then record the base:

```
git -C <repo> rev-parse HEAD
```

Every later diff is against that SHA. Write it in the run note. **Do not re-derive it later from
`HEAD`** — another session may have committed in the meantime, and a moving base silently shrinks
every diff you are about to inspect.

## 2. Scout, once

One `Explore` subagent, `model: sonnet`, thoroughness `medium`. Ask for, in one brief:

- where this lands (1–3 files);
- what already does part of it (with `file:line`, labelled use-as-is / extend / avoid);
- the test files nearest the change;
- anything that makes the feature impossible as scoped;
- **how this project's code is EXECUTED** — is there a running service container, and does it
  bind-mount the checkout? Ask for the container name and the output of
  `docker inspect -f '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}' <name>`.
  A container that mounts the main checkout and not `.claude/worktrees` means **no implementer can
  execute its own code without syncing first** — it will run the suite against the main checkout and
  report a false pass. Carry the container name and the mount list into every implementer brief. If
  there is no such container the scout must say so explicitly; silence is not the same answer.
- **the binding constraints** — read `<repo>/.claude/rules/*.md` and `<repo>/CLAUDE.md` if present
  and return, verbatim, only the entries that touch this area. If none apply it must say so
  explicitly; silence is not the same answer.

Fold the constraint sweep into this dispatch rather than reading those files yourself — it is bulk
extraction with a fixed output, and a second agent would pay the context setup twice.
**Constraints are load-bearing, so treat the returned list as a claim:** spot-check that each quoted
entry exists where the scout says it does before carrying it into a brief.

**If it already exists, stop and say so with evidence.** Do not invent a justification to build it
anyway.

## 3. Cut the work into units

A unit is a coherent change with its own file list and its own criteria.

**Cutting units so they do not share files is the entire concurrency mechanism.** There is no lock to
fall back on. Two units that touch the same file cannot run in parallel, and if you dispatch them
anyway you get a cherry-pick conflict at integration instead of a clean refusal at write time. Cut
for disjointness first and elegance second.

Create one task per unit (`TaskCreate`) and set real dependencies with `addBlockedBy`. Record in the
run note, per unit: id, one-line goal, **the complete list of files it may touch**, and the branch
name `autobuild/<slug>/<unit-id>`.

Then compute the **file-overlap graph** over those file lists and write the **widest legal fan-out**
into the run note — the largest set of units sharing no file. You will dispatch at least that many in
one message. A number you wrote down is checkable; an intention is not.

*(Added 2026-08-07 because the prose alone did not produce the behaviour: "I went one at a time to be
careful" is the failure this rule exists to catch, and it is what turns a 6-unit build into six
serial dispatches.)*

**Before the first fan-out, make sure `.claude/worktrees/` is gitignored.** The harness creates agent
worktrees *inside* the repo, so any later wildcard add stages each one as an embedded gitlink — a
commit that reads clean in `git status` and is broken for every clone. Verified live 2026-07-31.

## 4. Per unit

### 4a. Build — parallel by default

Dispatch `implementer` (`sonnet` by default; see `SKILL.md` step 3b) with `isolation: "worktree"`.
**Escalate this unit to `opus` in the dispatch itself** if it is a new subsystem, touches data
correctness, or is the second attempt after a failed check. Name the escalation and its reason in the
run note — an unexplained tier change is indistinguishable from drift.

The brief carries: the unit id, the goal, **the declared file list**, the binary criteria, the branch
name to create, the base SHA, every binding constraint from the scout, the container name and mount
facts if there is one, and the run's safety constraints.

**PARALLEL IS THE DEFAULT. Disjoint units go out in ONE message**, one `Agent` call each. Serial
execution is a consequence of units genuinely sharing files, never a starting posture. When every
unit touches the same files there is no parallelism to buy — run those sequentially, each branching
from the previous unit's commit. That shape is correct, not a failure mode. Reaching for it when the
units are disjoint throws away the whole point of worktree isolation.

A ready unit never waits on an unrelated one. Blocking is per-file, not per-wave.

### 4b. Check that the unit actually landed — git, not the report

**A dispatch's `status: completed` says nothing.** The harness reports the same word for a delivered
brief and one abandoned mid-sentence. Do not read the report to decide this. Run:

```
git -C <worktree> status --porcelain
git -C <worktree> log --oneline <base-sha>..<branch>
```

- **Dirty tree, or zero commits → the unit stalled.** Resume it yourself with `SendMessage` to that
  agent — *collect your results now, finish the report, commit with explicit paths* — immediately and
  without surfacing it as a question. **Budget one automatic resume per dispatch; a second failure is
  a real finding**, not another retry.
- **Clean tree with commits → it delivered.** Proceed.

*(MEASURED 2026-07-31: 8 of 8 dispatches in one run ended mid-sentence with work intact on disk and
nothing reported. Every one recovered on a single nudge and no work was ever lost — but each nudge
was hand-written by the user, which is exactly the babysitting this skill exists to remove. MEASURED
2026-08-02: one implementer of four ended parked on a wake that could never fire, holding uncommitted
work on a branch with zero commits, and the notification said `completed`. Merging on that status
would have carried an empty branch forward and reported the unit done.)*

### 4c. Check the unit stayed in its lane

```
git -C <worktree> diff --name-only <base-sha>..<branch>
```

Compare that list against the unit's declared files.

- **A path outside the list is a discovery, not an error.** Send it to `scope-arbiter` and honour the
  verdict: `build` (scope it as a new unit), `backlog` (log it, move on), `park` (the rule and its
  triggers live in `agents/scope-arbiter.md`). Do not retroactively widen the file list to make the
  difference disappear — that is how a run stops being able to say what it changed.
- **A path claimed by another unit is a collision**, not a discovery. Your units overlap. The arbiter
  cannot help; re-cut them, or serialise those two.

This check replaces a write-time guard, and the trade is deliberate: it catches the same drift one
step later, costs one command, and cannot reach outside this run.

### 4d. Verify — adversarially, in one message

This is the part that makes the run worth its cost, so it does not get skipped and it does not get
softened. Dispatch, **in a single message**:

- **one `skeptic` (`opus`) per acceptance criterion of this unit.** Each is told which criterion the
  implementer claims passes, and told to make it fail. It returns `refuted` (it ran something and the
  criterion broke), `stands` (it attacked properly and could not break it), or `unverifiable` (it
  could not check at all) — see `agents/skeptic.md`. Those three are not interchangeable.
- **`pr-review-toolkit:silent-failure-hunter`** on the diff.
- **`pr-review-toolkit:pr-test-analyzer`** on the diff.

Hand every one of them the base SHA, the branch, the unit's criteria verbatim, the binding
constraints, and the run's safety constraints. **Safety constraints go in EVERY brief, including the
judge's.** *(Earned 2026-07-31: every implementer brief carried "use the read-only role"; the judge's
brief omitted it, and the judge then issued an unqualified `UPDATE` against a live production table
while trying to watch a guard fire.)*

**What blocks, by tier.** A finding is not automatically a gate:

| Effort tier | What blocks |
|---|---|
| any tier | a `skeptic` that **actually refuted a criterion** — it ran something and the criterion failed |
| `low`, `medium` | nothing else; lens findings ride to the judge as advisory context |
| `high`, `xhigh`, `max` | lens findings against **correctness** or a **stated acceptance criterion** |

Everything else is advisory in every tier. *(Calibrated from the 2026-08-01 assessment: a reviewer
prompted to find gaps will usually report some even when the work is sound, and the judge already
weighs lens findings. Gating on every finding is the over-gating pattern.)*

Record in the run note, per unit: which criteria were attacked, which survived, which were refuted,
and which nobody could check.

### 4e. A blocking finding goes BACK to the implementer

The verify results are a work queue, not a report.

- **Everything survived** → go to the judge.
- **Anything refuted or blocking** → re-dispatch this unit's implementer, brief = the finding
  verbatim plus the evidence, **escalated one model tier** (`SKILL.md` step 3b). Then re-verify.
  **Cap: 2 remediation rounds per unit.** A third is a finding, not a retry: mark the unit `stuck`,
  record it in the run note, keep draining the rest of the queue, and surface it in `needs_you`.
- **Unverifiable is NOT a pass and NOT a failure** — it means nobody could check. Escalate it to the
  judge explicitly labelled unverified. Never let it silently count as green.

*(MEASURED 2026-08-07: a verify phase returned a genuine defect — a parser turning an absent key into
`""`, indistinguishable from a real empty value and invisible to all 31 tests — and the run completed
successfully anyway, because nothing routed the finding anywhere. A gate that reports a real defect
and then terminates is worse than no gate, because the report reads as diligence.)*

### 4f. Judge the unit

Dispatch `done-judge` with the unit's criteria **and the verify evidence**. Record the verdict in the
run note.

The judge stalls like any other dispatch — check it the same way, and auto-resume it once. A silent
judge taken for a completion ends the run with no verdict while looking judged.

## 5. Integrate

Integration is yours, it is serial, and it happens in a **throwaway worktree** — never by checking
out anything in the main checkout, which another session may be sitting in.

Gate it on 4b having passed for every unit you are about to carry forward. A unit that ended dirty or
with zero commits is resumed, not merged. If a unit genuinely required no change, write that in the
run note and proceed knowingly.

For a single commit, cherry-pick it yourself — one command does not need an agent. For several,
dispatch `integrator` (`sonnet`): hand it the base branch, the source SHAs **in order**, and the
verification command to run after the last pick. It works in its own throwaway worktree, stops on any
conflict rather than resolving it, and never touches `main`.

**Then verify its report yourself.** `git log` the integration branch and confirm each claimed SHA
landed. Never relay an integrator's "picked cleanly" as fact. Check `git branch --show-current`
before and after — another session may share this checkout.

A conflict is real information about how the units were cut. Re-cut and rebuild the affected unit;
do not resolve it by picking a side.

## 6. Whole-ask judgement

When every unit is done, run `done-judge` once more against the **root ask, verbatim** and the full
criteria set — not the per-unit ones. This is what terminates the run.

`incomplete` means work remains: queue what it named in `unmet` and keep going. Do not report until
you have a `satisfied` verdict, or a `stuck` you can name and explain.

## 7. Close

Update the run note with the final verdict, then report the four fields from `SKILL.md`. Nothing
else.

Leave every branch and worktree in place. They are the record, and deleting them is the user's call.

## Failure handling

- **A unit fails repeatedly** — after the 2-round cap, mark it `stuck`, keep draining the rest of the
  queue, and put it in `needs_you`. One failed unit does not end a run.
- **A permission denial** — a parked unit; full rule in `agents/scope-arbiter.md`, Standing rules.
- **A plan that no longer fits what the repo turns out to be** — a discovery like any other. Send it
  to `scope-arbiter` and honour the verdict; it does not end the run.
- **Suite comparison** — compare against a same-session run of the base SHA, by **which tests failed**
  (identity sets), never counts. A remembered baseline number rots within hours.
- **A mid-run message from the user** is steering unless it is plainly a stop. Steering adds,
  reprioritizes, or cancels queued work and the run continues; ambiguous phrasing resolves to *stop*,
  deliberately.
