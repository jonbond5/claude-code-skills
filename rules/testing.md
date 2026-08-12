---
paths:
  - "**/tests/**"
  - "**/test_*.py"
  - "**/*_test.py"
  - "**/conftest.py"
  - "**/pytest.ini"
  - "**/tox.ini"
  - "**/*.test.ts"
  - "**/*.test.tsx"
  - "**/*.spec.ts"
---

# Testing footguns

Full incident narratives: a separate incident log. The always-on rules —
**verify the verifier**, **watch every guard fire in both directions** — live in the always-on
working agreement (`docs/working-rules.md` in this repo, `~/.claude/CLAUDE.md` once installed); this
file holds the harness-specific traps.

## A hand-built test runner manufactures FALSE FAILURES

**Trigger:** a bespoke way to run tests — a custom `docker run` with hand-specified mounts/env, a
script wrapping the real harness, a worktree-pointed runner.

**Rule:** before trusting ANY failure it reports, run it against the **known-good baseline** — the
unmodified branch point — and confirm it reproduces the *established* pass set. **A failure the
baseline also shows is the runner, not your change.** Treat the runner as an instrument needing
both-directions proof: it must execute YOUR code (positive control — a worktree-only marker test is
collected) AND reproduce the clean baseline (negative control).

**Why:** the real container/CI replicates more than you will — extra bind mounts, env vars, a warm
DB, service links. A missing piece surfaces as a `FileNotFoundError`, a collection error, or an
assertion failure that looks **exactly** like a regression in your change. One runner omitting two
mounts manufactured 4 "failures" + 3 collection errors that a subagent then reported as the real
baseline.

## Suite gates compare against a SAME-SESSION base-branch run, never a recorded baseline

**Rule:** each gate re-measures the base branch in the same session and environment as the branch
run, and compares **identity sets** (which tests failed/errored), not counts, with every delta
itemized. Reuse a previous gate's post-merge run as the next baseline only when the base branch and
environment are provably unchanged in between.

**Why:** recorded counts rot fast — a service coming up un-skips tests, live-data tests flip on data
drift, other merges add/retire tests. One recorded baseline was wrong within hours and moved through
three different figures in a single day for reasons unrelated to any branch under test. Gating on
stale numbers either blocks a clean merge or waves through a real regression.

## A green test-harness / CI run doesn't prove real-target-environment behavior

**Rule:** before declaring done, verify in the actual target environment (or one faithful to it).
"The pipeline says it passed" is necessary, not sufficient — especially for anything
environment-dependent: GUI/display, window manager, OS libraries, networking, file permissions.

**Tell:** an always-on-top window passed an `xprop` check under bare Xvfb (no window manager) and did
nothing under the real desktop; a container `--self-test` passed in a pipeline that supplied a
display and crashed standalone with no `$DISPLAY`; GUI tests "passed" only because the harness
skipped them on a missing `tkinter`. Each green run measured the harness, not reality.

## Phased TDD — write the RED harness first

For non-trivial features, Phase 0 is the **full test harness, RED** — deterministic, ideally
token-free — encoding the spec as failing tests *before* any implementation. Verify the reds fail for
the **right reason** (assertion failures, not harness/collection errors). Then implement to green,
phase by phase, smallest correct change, one commit per phase with the phase named. Each phase is
gated: its tests pass AND the pre-existing suite still passes.

**Tell:** "tested after" passes just as green as "tested first," so the miss is invisible. Two
non-trivial fixes shipped this way — the tests passed, but the spec was never encoded as failing
tests before the change. **Write the red test first whenever the change has a stateable expected
behaviour — including small patches.** The full Phase-0 harness is for non-trivial features; for a
small patch, one failing test that pins the behaviour is the whole requirement. *(Scoped 2026-07-31:
the old "write the red harness first even for small patches" removed the non-trivial-features scope
this entry opens with, so the rule contradicted itself; the archive's incident was two non-trivial
fixes.)*

## Comparing a branch's suite to a base's — compare the COLLECTED count, not only pass/fail

**Trigger:** reporting a branch as regressed because its pytest tally looks worse than a baseline
figure taken from another branch (or from earlier in the session).

**Rule:** a base that moved ahead makes the branch look like it is failing when it is merely missing
the base's newer tests. Compare **collected** first; only then compare failures. Re-take the baseline
on the current base tip rather than quoting a remembered number.

**Tell:** "3 failed, 327 passed" against a 418 baseline reads as a catastrophe and was 87 uncollected
tests plus 3 real failures. *(Relocated 2026-08-02 out of the author's own always-on
`~/.claude/CLAUDE.md`.)*

## When auditing tests for obsolescence, audit the PASSING ones — the dangerous one is GREEN

**Trigger:** a retirement, deprecation or removal, and you go looking for which tests it invalidated.

**Rule:** the failing tests announce themselves. **A test whose subject was retired can just as easily
start passing UNCONDITIONALLY**, and then it guards nothing while reporting success — strictly worse
than red, because nothing will ever surface it. Sweep the tests that *touch* the retired thing, not
the ones that fail. For each, ask what would make it fail now; if the answer is "nothing", it is
obsolete no matter what colour it is.

**Two shapes, one session (2026-08-08):** a CONTROL pinned to the retired subject — *"this input
serves NOTHING"* passes unconditionally once the subject serves nothing by definition; and a GUARD
whose subject silently left the data — the lookup dropped the retired position and the comparison
**skipped it**, so every assertion stopped executing while staying green.

**Tell:** you are deprecating tests from a FAILURE LIST. Wrong input — start from what the retirement
touched. Sibling of *never watched fire*: there untested, here unreachable.

**Same family — a CACHE landing under a test.** Patching an evaluator proves nothing once the code
short-circuits to stored rows before it runs: both arms go byte-identical and the assertion passes by
tautology. **Revert the fix the test guards and confirm RED**; anything still green has stopped
measuring. *(Three siblings of one acceptance test had quietly stopped discriminating; only the one
with a self-check on its own control noticed.)*

## Before believing a bespoke runner, add the mounts and flags the real one has

**Trigger:** a hand-rolled `docker run … pytest` for a repo whose real harness you have not read.

**Rule:** each missing piece manufactures failures that look exactly like regressions — a missing
source dir surfaces as `ModuleNotFoundError` at collection, and one unimportable file can abort the
entire run before a single test executes. Mount every tree the tests import from (not just `src`
and `tests`), pass each database URL the conftests read, and use
`--continue-on-collection-errors` so one broken module cannot mask the rest. **Prove the instrument
both ways first:** it collects a marker only your branch has (it runs YOUR code), and it reproduces
the base branch's known result (it is not inventing failures).

**Tell:** your "regressions" are all collection errors, or they vanish when you add a mount.

## A control that fails for a HARNESS reason is not a verdict

*(Relocated 2026-08-08 out of the author's own always-on `~/.claude/CLAUDE.md`, merged with the
bespoke-runner rule above — one mechanism, one home.)*

Identical non-zero exits across every arm mean the rig broke, not that the hypothesis died. No bind
mounts runs BAKED-IN code. **A PARTIAL mount set is the nastier shape** — mounting code but not its
ARTIFACTS yields a plausible DOMAIN failure ("these two models are unservable") instead of an obvious
one, and the more plausible the defect sounds, the likelier you are to report it. **A broken probe
fanned out to N agents is replicated N times — its false negatives agree, which looks like
consensus.** Run every probe once yourself first.

## A harness-timeout-killed `docker exec` leaves the in-container process ALIVE

**Trigger:** a long `docker exec <container> <cmd>` killed by the *agent-harness* timeout, then
re-run.

**Rule:** the harness kills the `docker exec` **client** on the host; the process **inside the
container keeps running**, orphaned, still holding its locks and transactions. Before re-running or
trusting a measurement, **sweep in-container orphans**
(`docker exec <c> sh -c 'ps -eo pid,args | grep [p]attern'` → `kill -9`) and confirm the shared
resource is quiet (`pg_stat_activity`, held locks, a lockfile). Give long `docker exec` commands a
**generous timeout** so a slow-but-clean run isn't itself killed into a new orphan.

**Tell:** a *shifting failure identity* across otherwise-identical re-runs is contention, not a code
regression. Five orphaned pytest processes mid-`DROP SCHEMA` deadlocked each new run at a *different*
test each time, while every test passed in isolation — it read exactly like a post-merge regression.
