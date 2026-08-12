---
name: implement-plan
description: Build a plan that already exists. Takes ANY implementation plan (from /harden-plan, /project-to-plan, the autobuild plugin's design skill, or an ad-hoc one) and deploys implementers — in parallel worktrees when the work is disjoint — plus a verification pass that checks every acceptance criterion and then tries to refute each claimed pass. Use when you have a plan and want it BUILT with you in the loop. Does not design — if the plan needs challenging first, run /harden-plan. For unattended build-to-verdict runs, use the autobuild plugin instead.
argument-hint: [plan-path]
disable-model-invocation: true
---

# Implement Plan

Build a plan that already exists. This skill does **not** design.

## This skill or the autobuild plugin?

The `autobuild` plugin in this repo covers the same ground autonomously: it plans, builds in
worktree-isolated units, verifies adversarially, and stops only when an independent judge says the
original ask is satisfied — it does not come back for approval, and it arbitrates mid-run
discoveries itself. This skill is the **attended** alternative. Same worktree isolation, same
refute-the-pass verification, but the human stays in the loop: a plan that turns out to be wrong is
a stop-and-surface here, never a silent rewrite or an arbitrated scope change, and nothing lands on
your branch unless you ask. Use `autobuild` to hand off an ask and come back to a verdict. Use this
when you hold a plan you have already reviewed and want it executed exactly as written, with every
deviation surfaced.

The frontmatter sets `disable-model-invocation: true` deliberately — you type this skill, plan in
hand. A build-shaped request in free conversation should route to `autobuild` if it is installed.

## Input

`$ARGUMENTS` is a path to a plan — **Read it**. If empty, look for the plan produced earlier in this
conversation, or the most recent file under `./docs/plans/`. **Name the plan you are about to build
before spawning anything. Never guess silently.**

**A plan carrying a `NOT READY TO IMPLEMENT` banner still has surviving findings — surface them**
before proceeding.

## Pre-flight — refuse to build an unbuildable plan

1. **Acceptance criteria.** Must be present and **binary/observable**. If absent or vague, derive them.
   *A build with no success definition cannot be reviewed, only rationalized.*
2. **Changes list.** The plan must name the files/modules to touch. If it does not, spawn **one**
   `Explore` subagent (thoroughness `"medium"`) to map the plan onto concrete files, then show the user
   the file list before proceeding.
3. **Constraints.** Read the project's rules surfaces — its `CLAUDE.md` and `.claude/rules/*.md`, or
   whatever equivalent the project keeps; carry entries touching this area into the Scope Contract.

Assemble the **Scope Contract**. Every subagent gets it **verbatim**.

```
VERBATIM ASK:         <the plan's stated goal>
ACCEPTANCE CRITERIA:  <binary, observable>
ANTI-SCOPE:           <what NOT to touch>
BINDING CONSTRAINTS:  <entries from the project's rules surfaces touching this area>
```

## Execution — parallelize by default, isolate by worktree

Partition the CHANGES list into **file groups**, then classify each:

- **Disjoint group** — touches only its own files, no shared convergence file. → **Parallel implementer
  with `isolation: "worktree"`.** Launch all of them in one message.
- **Convergence group** — touches the core module everything wires into. → **One sequential owner**,
  after the disjoint groups merge, one gated commit per sub-phase.

**The constraint is physical, not cautionary: a working tree has one HEAD.** Two branch-owning agents in
one checkout will sweep each other's staged files into unrelated commits **even when their file sets are
disjoint**. Worktree isolation is what makes parallelism safe here — it is the default mechanism, not an
exception. Worktrees cost setup and disk per agent, so for a single small feature one inline implementer
is still right; the fan-out earns its cost from three groups up.

Each implementer's brief opens with the **frozen Scope Contract verbatim** + its CHANGES bullets + this:

> Your done-criterion is: every acceptance criterion observably passes, every binding constraint is
> respected, and no files outside the CHANGES list are modified. Adjacent improvements are not in scope.
> Poll long commands in the FOREGROUND. Do not end your turn parked waiting on a background job.

**Before the first fan-out, gitignore `.claude/worktrees/`.** The harness creates agent worktrees
*inside* the repo, so a `git add -A` in the convergence step stages each one as an embedded gitlink —
a commit that reads clean in `git status` and is broken for every clone. In the convergence step,
**stage explicit paths, never `-A`.** *(Observed live: three embedded repos committed alongside a
one-file change.)*

**Merging is orchestrator work, and it is serial.** Do it yourself, one worktree at a time, in a
**throwaway worktree** — never `git merge` in the shared checkout. The exception is when the target
branch IS the one checked out there; then merging in place is correct, but diff the incoming file list
against any other session's dirty files first. Check `git branch --show-current` before each merge.
If a container wrote root-owned files inside a worktree, `docker exec <container> rm -rf` them
**before** removing the container, then remove the worktree.

**Budget one resume-nudge per long-running implementer.** An agent whose completion notification says
it is "standing by" has usually stalled with no live background children — the wake it waits for will
never fire. Resume it with: *collect your background results now, poll in the foreground, do not end
your turn until the task list is complete or a named gate fails.*

## Verification — the part usually skipped, and the part that matters

**First, the suite.** Run it, and compare against a **SAME-SESSION run of the base branch**, comparing
**which tests failed (identity sets)**, not counts. **Never gate on a recorded or remembered baseline
number** — those rot within hours.

**Then one reviewer per criterion.** Fan out one general-purpose subagent per acceptance criterion —
all in one message, in parallel. Each gets the frozen Scope Contract verbatim, its single criterion,
the diff to read (`git diff $(git merge-base HEAD <base>)...HEAD`), and the prompt template in
[`verify-criterion.md`](verify-criterion.md). Each returns `PASS` / `FAIL` / `UNVERIFIABLE` with its
evidence, and must classify that evidence honestly:

- `MEASURED_OUTPUT` — it ran a command and quotes the real output.
- `CITATION` — it points at code that appears to do the thing, without running anything.
- `CONFIG_ASSERTION` — it leans on a flag, a constant, a test's name, or a green suite.

**Then a skeptic per unmeasured PASS.** A PASS backed by a command and its real output has already
been measured — a skeptic re-running the same command adds cost and no information. A PASS backed by
a citation or a config assertion has **not** been measured, and that is exactly the shape that ships
false passes. So refute selectively: every PASS whose evidence kind is not `MEASURED_OUTPUT` — plus
any that claims `MEASURED_OUTPUT` but quotes no command and no output, since self-classification is
itself a claim — goes to a fresh general-purpose subagent with the prompt template in
[`refute-pass.md`](refute-pass.md), all in parallel. This stage exists because implementers
over-report success and rationalize failures as benign, and because a reviewer's evidence is itself a
claim — reviewers in loops like this have cited file:line references and spec items that do not
exist. The skeptic re-runs the command, probes the edge cases, and checks what every new input
resolves to when its source is missing.

**Then constraints over the whole diff.** One subagent with the prompt template in
[`check-constraints.md`](check-constraints.md): binding-constraint violations, files modified outside
the CHANGES list, and at most 3 advisory observations.

**Then verify the verifier.** Read the actual diff yourself and spot-check one `verified` criterion's
evidence. Never relay an agent's "it's green" as fact, including a skeptic's.

## Finalize

Report:

- What was built.
- Criteria: **verified / overturned / failed / unverifiable**, with evidence. An `overturned` criterion
  is a FAILURE that a reviewer initially called a pass — say so plainly, it is the highest-signal
  output of the whole run.
- The **suite delta, itemized** by test identity.
- Constraint violations, and any out-of-scope files touched.
- The ≤3 advisory observations.
- Anything you could **NOT** verify.

If a criterion failed, **say so plainly with the output — do not hedge.**

## Do NOT

- **Do not redesign the plan mid-build.** A plan that turns out to be wrong is a **STOP-and-surface**,
  not a silent rewrite. (This is the deliberate difference from `autobuild`, which arbitrates and
  continues.)
- **Do not expand beyond the CHANGES list.**
- **Do not commit to the user's branch or push unless the user asks.** Implementer commits inside
  their own worktree branches are execution mechanics, not an exception to this.
- **Do not run two branch-owning agents in one checkout.** Ever.
