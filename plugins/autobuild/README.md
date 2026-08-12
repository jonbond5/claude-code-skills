# autobuild

Build a feature end to end without intermediate approvals. You give the ask and the design anchors;
autobuild decides *how* it gets built, expands scope when a discovery blocks the ask, and stops only
when an independent judge says the original ask is satisfied.

**Built from the harness's own primitives and nothing else** — subagents, worktree isolation, the
task list, and git. No CLI, no state file, no hooks, no lock directory. See *Rule zero* below; that
constraint is the design, not an aesthetic.

## The workstream: discuss → design → build

**Discuss** is a conversation, deliberately not a skill — wrapping a procedure around it adds
ceremony to the one phase where it hurts. Reach for `autobuild:requirements-challenger` when you want
an independent attack on something *Claude* proposed. (Measured 2026-07-31: saying "challenge this"
does **not** auto-invoke it — Claude challenges inline, and does it well. The agent's product is
independence, not criticism, so it earns its keep when the author is the one judging.)

**Design** (`autobuild:design`) turns the discussion into a `HANDOFF-*.md`. Non-interactive: it
measures load-bearing facts with real commands first, runs parallel diverse-lens challengers to
convergence, and parks a scope-narrowing rather than stopping on it.

**Build** is this skill. If a handoff exists, it takes `jobs/from-design.md` — which reads the
handoff's ANCHORS as the user's decisions and treats everything else as its own.

### The seam

The handoff format was **mined from 20 hand-written `HANDOFF-*.md` docs** in the author's repos, not
invented. Contract sections: `The question — verbatim, immutable`, `Acceptance criteria`, `ANCHORS`,
`OPEN`, `Anti-scope`, `Where the evidence lives` (with `[MEASURED]`/`[RESEARCH]`/`[REASONED]` tags),
`THE DECISION QUESTION FOR THE NEXT SESSION`, `STILL OWED`.

**Anything not in ANCHORS is Claude's to change.** That default is the whole point — the document can
be as opinionated as it likes about approach without freezing the builder's hands. `ANCHORS` is the
one section that did not already exist in the mined format; everything else was already convention.

## Rule zero — runs cannot see each other

> **Two autobuild runs in one repository must not be able to observe each other, block each other, or
> wait on each other — and a run must never touch a session that is not doing a build at all.**

A run owns a **branch namespace** (`autobuild/<slug>/…`), not the repository. Each unit gets its own
**worktree** via `isolation: "worktree"` — the harness already gives it a private HEAD, and that *is*
the concurrency control. Units are cut so their file lists are disjoint; if a lock ever seems
necessary, the units were mis-cut.

**This is a rewrite, not a preference.** MEASURED 2026-08-09 against the previous implementation, by
driving the real code:

- With a run live in project P, a second session's `start` was **REFUSED, exit 2** — "session B
  cannot run autobuild", the failure this rewrite exists to kill.
- Worse: the Stop hook **blocked any unrelated session in P from ending its turn**, ordering it to
  run autobuild's done-judge, up to five times. A build in one session hijacked every co-tenant
  session in the repository.
- And the guards were **unremovable without a restart**: hook registration is cached at session
  start, so deleting `hooks.json` does not disarm a running session — while a hook whose script is
  *missing* **hard-blocks** the tool rather than failing open, contrary to what this README used to
  claim. Removing the machinery mid-session locked the removing session out of `Write`, `Edit` and
  `Bash`, including from its own subagents.

Roughly 2,600 lines of Python, JavaScript and JSON were deleted to get here. Everything they enforced
is now either a git command the orchestrator runs itself, or a contract inside the one agent that can
end the run.

## Use it

Just ask. The skill is model-invocable, so any build-shaped request routes here:

```
build me a feature that does X
implement X and make sure it actually works
add X — take as long as you need
```

**One gate, once.** A fresh run asks whether to proceed, because a full run is long. Accept the cost
in the ask itself — *"take as long as you need"*, *"don't stop until it's done"*, *"I know this will
take a while"* — and it skips the question and starts.

**Steer without stopping it.** A mid-run message is steering unless it is plainly a stop. Steering
adds, reprioritizes, or cancels queued work and the run continues; ambiguous phrasing resolves to
*stop*, deliberately.

**Stopping it:** say so plainly, or interrupt the turn. There is no sentinel file to touch any more,
because there is no daemon holding the turn open.

## What you get back

Four fields, nothing else:

```
status:    done | stuck | partial
headline:  one sentence
open:      <still queued>
needs_you: <parked items, permission denials, decisions>
```

`status` comes from the done-judge, not from the thing that did the work. That separation is what
makes a terse report trustworthy rather than a blindfold.

Decisions, detours and per-criterion evidence go in the run note for a resumed session and the judge.
They are deliberately not in the reply.

## Authority model

**You own what the question is. autobuild owns everything that serves it.**

| Discovery | What happens |
|---|---|
| blocks the ask, or is cheap | built, logged, no question asked |
| serves the ask but expensive | probed if one command settles it, else backlogged |
| would *change* the ask | parked, run continues on your literal ask, surfaced loudly at the end |

The third is the only class handed back. Expansion and substitution look alike in a transcript and
are completely different risks; telling them apart is the `scope-arbiter`'s whole job.

## How verification works now

Per unit, in **one message**: one `skeptic` per acceptance criterion, plus the two `pr-review-toolkit`
lenses on the diff. Each skeptic is told to make its criterion **fail**, and must run a command to
say anything at all. It returns one of three words — `refuted`, `stands`, `unverifiable` — and they
are not interchangeable.

- `refuted` blocks the unit at every effort tier and goes back to the implementer, escalated one
  model tier, capped at 2 remediation rounds.
- Lens findings are advisory at `low`/`medium`; at `high` and above they block only when they hit
  correctness or a stated criterion. *(Calibrated from the 2026-08-01 assessment: a reviewer prompted
  to find gaps will usually report some even when the work is sound.)*
- `unverifiable` is neither a pass nor a failure. It rides to the judge labelled unverified.

## Who does what, and on which model

**No global default — every dispatch is an explicit call**, and a tier you name always wins. The line
is: anything that can END or BLOCK the run on its own inherits the session model; anything bounded by
a written rubric with a checkable output runs on Sonnet.

Opus keeps the judge, the skeptics, and the challengers. Sonnet gets the building, the searching, the
probing, the writing, the merging, and the reconciling. The orchestrator escalates a unit to Opus
when it is a new subsystem, touches data correctness, or is the second attempt after a failed check —
named in the run note, never silent. Full table: `skills/autobuild/SKILL.md` step 3b.

**Not everything menial is worth an agent.** A dispatch costs ~38k tokens of context setup, so single
git commands, unit cutting, subagent-claim checking and the final report stay inline.

## Parts

| Path | What it is |
|---|---|
| `skills/autobuild/SKILL.md` | build policy + router (thin by design) |
| `skills/design/SKILL.md` | discussion → hardened handoff document |
| `jobs/*.md` | the procedures, loaded on demand |
| `agents/done-judge.md` | independent arbiter of "is the ask satisfied" (opus) |
| `agents/skeptic.md` | attacks ONE claimed-passing criterion until it breaks (opus) |
| `agents/requirements-challenger.md` | independent attack on an idea or claim (opus) |
| `agents/implementer.md` | builds one unit in its own worktree (sonnet) |
| `agents/scope-arbiter.md` | build / backlog / park (sonnet) |
| `agents/prober.md` | batch-verifies factual claims by running commands (sonnet) |
| `agents/scribe.md` | writes a document from content it is handed (sonnet) |
| `agents/integrator.md` | serial cherry-pick forward in a throwaway worktree (sonnet) |
| `agents/recon.md` | reconciles an interrupted run's note against git (sonnet) |

Standing verify lenses come from `pr-review-toolkit@claude-plugins-official`:
`silent-failure-hunter` and `pr-test-analyzer`.

## Run record

The **task list** is the queue. **Git is authoritative** for what exists. One plain markdown **run
note** at `~/.claude/autobuild/<run-slug>.md` holds the verbatim ask, the criteria, the units, the
decisions, the escalations, the verify results and the judge verdicts.

Nothing else ever reads that note — no hook, no other session, no tool. Where it and git disagree,
git wins. That ordering is what keeps it a file instead of a state machine.

## What was traded away, honestly

The old machinery enforced three things in code that are now contracts in prose. This is a real
trade, not a free win:

| Was enforced by | Now |
|---|---|
| a Stop hook that refused to end an unjudged turn | the judge's contract: **a criterion with no skeptic verdict and no command output is UNVERIFIED, and unverified is not satisfied.** If the orchestrator stops early, no verdict exists and the report has nothing to render. |
| a PreToolUse hook refusing an out-of-scope write | `git diff --name-only` after the unit, compared against the declared file list. Same drift, caught one step later, one command. |
| a SubagentStop hook refusing a dirty exit | `git status --porcelain` + `git log <base>..<branch>`, run by the orchestrator against each worktree. |

The two write-time guards are genuinely weaker: they detect rather than prevent. That was the correct
trade, because **they were also the mechanism that broke every co-tenant session in the repository**,
and a guard whose blast radius exceeds its own run is not a guard.

The Stop gate is the one worth watching. It never actually solved the underlying behaviour — the
first thing it did on every measured stall was block, and every recovery still came from a nudge —
and it bounded runs at 5 blocks anyway.

## Known gaps

- **No automated test suite.** The deleted `tests/` exercised the deleted machinery; there is nothing
  left in this skill that is unit-testable, because there is no longer any code. The things that can
  go wrong now are prose defects and agent behaviour, and the check for those is running it.
- **`allowed-tools:` in a plugin skill's frontmatter makes the Skill tool fail** with an opaque
  `Execute skill: autobuild`. Bisected 2026-07-31: the skill executes with the field removed and
  fails with it present, in both space- and comma-separated form. **Do not add it back.**
- A plugin skill must live in `skills/<name>/SKILL.md`. A root `SKILL.md` with `"skills": ["./"]`
  (what `claude plugin init` scaffolds) registers as `Skills (0)` — it appears in the skill listing
  but does not execute.
- **Plugin hook registration is cached at session start.** Nothing here registers hooks any more, but
  if one is ever added: adding or removing it takes effect only in *new* sessions, and a hook whose
  script is missing hard-blocks the matched tool rather than failing open.
- **`claude plugin eval` is early access and unavailable on this account** (`claude plugin eval init`
  exits 1). When access lands, `--ablation with-without` gives a no-plugin baseline arm.
