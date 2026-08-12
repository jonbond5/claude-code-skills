# The architect ↔ reviewer loop (shared engine)

The single definition of the adversarial design loop. `harden-plan` and `project-to-plan` Stage B
run it; the autobuild plugin's `design` skill drives a mechanized twin. Not a skill — a reference
document those skills read.

**The mechanics live in code where they can:** `plugins/autobuild/workflows/review-loop.mjs`. Round
counting, the convergence predicate, dedup, the refutation cap, and the ceiling are JavaScript there,
not prose an orchestrator interprets. **When the autobuild plugin is installed, prefer the script.**
Without it, run the loop by hand with general-purpose subagents — the prompts live beside this file
(`architect-agent.md`, `researcher-agent.md`) — holding yourself to the contract below. Edit loop
mechanics in the script; edit this document to explain them.

> **Why the mechanics moved into code.** As prose, the loop depended on an orchestrator faithfully
> executing 111 lines of round-counting and guard-flag logic across many turns while also holding a
> conversation. One planning run finalized a plan carrying **eleven live blockers** because
> `N == MAX_ROUNDS` — five of which meant a core component could not be built at all (observed on one
> project). The loop worked; the control flow was negotiable. `while (dry < DRY_ROUNDS)` is not.

## Parameters

The same knobs whichever way the loop runs — as `args` to the script, or as the contract you hold a
hand-run loop to.

| Parameter | Required | Meaning |
|---|---|---|
| `frozenContext` | **yes** | Passed **verbatim** to every agent in every round. The ask + acceptance criteria + binding constraints. |
| `seed` | **yes** | Round 1's input: a brief, a contract + repo findings, or an existing plan. |
| `maxRounds` | no | **Hard** ceiling on draft rounds. Default 3. |
| `dryRounds` | no | Consecutive clean rounds required to converge. Default 1; use 2 when correctness matters more than cost. |
| `lenses` | no | Review lenses, `[{key, prompt}]`. Default: reinvention, failure-modes, repo-fidelity. |
| `refuteCap` | no | Max findings refuted per round. Default 3. Anything over the cap is returned in `unverified` — **never** in `surviving` — and logged. |
| `probeFacts` | no | Load-bearing claims to verify with real commands **before** round 1. Up to 6. |

The loop **returns** the design; it does not write it. Writing the output file and emitting the
question-first header are caller responsibilities.

## What each round does

1. **Draft** — the architect (prompt: `architect-agent.md`) produces or revises. On a revision it
   must dispose of every surviving finding explicitly: incorporate, reject with a reason, or mark an
   open question, in a `§0 Change log`. No silent drops.
2. **Review** — every lens attacks the design **in parallel**, each a reviewer (prompt:
   `researcher-agent.md` plus the lens instruction) returning schema-validated findings with tags and
   cited evidence. Different lenses, so they don't converge on one objection.
3. **Refute** — one skeptic per blocking finding, **in parallel**, prompted to *kill* it. Survivors reach
   the architect as vetted; findings that die are reported but never acted on; findings over `refuteCap`
   reach the architect explicitly labelled as unchecked.
4. **Converge or continue** — `dryRounds` consecutive rounds with zero *new* blocking findings ends it.

A final **question check** agent verifies the design still answers the original ask.

## The four design decisions worth understanding

**Loop-until-dry, not a fixed cap.** Convergence is "K consecutive rounds surfaced nothing new,"
deduplicated against everything seen so far. A fixed counter misses the tail — which is exactly what
the eleven-blocker incident was. `maxRounds` remains as a hard ceiling, and hitting it sets
`status: 'BLOCKED'` and `readyToImplement: false`. **A blocked finalize must not emit a
"run `/implement-plan`" line.**

**Dedup against `seen`, never against `surviving`.** Deduping against surviving findings makes
refuted ones reappear every round and the loop never converges. This is the classic bug in this shape.

**Per-finding refutation, because a reviewer's claim is a claim.** Reviewers here have cited
`file:line` references and spec items that do not exist. Previously the architect received raw critique
and had to dispose of every item, fabrications included. Now each blocking finding faces a skeptic
that checks whether the evidence exists, whether the failure reproduces, and whether the design
already handled it. Refuters default to `refuted=true` when they cannot substantiate.

**Refutation is unconditional HERE and conditional in
`plugins/autobuild/workflows/implement-verify.mjs` — deliberately.** A finding in this loop is a
claim about a *design document*, which cannot be executed; nothing settles it but a second reader, so
every blocking finding earns a skeptic. A criterion in `implement-verify` can be settled by *running
the thing*, so that workflow refutes only a PASS whose evidence is a citation or a config assertion —
and it re-checks the evidence text rather than trusting the reviewer's self-classification.

> **Measured non-result, and it is load-bearing.** Three escalating live traps failed to provoke a
> single refutation in `implement-verify`: (1) an unread `VALIDATE_LIMITS` flag; (2) a green test
> named `test_max_limit_enforced` asserting only `MAX_LIMIT == 100`; (3) a correct `None`-excluding
> ranker made a no-op by a `COALESCE` upstream in SQL, so the guard passed in isolation while the
> endpoint shipped ten fabricated zeros. **Every time, the reviewer caught it at the review stage and
> the refuter had nothing to overturn.** On trap 2 it seeded a 500-row fixture because the real 40-row
> table could not exceed the bound under test; on trap 3 it proved from the DB that no legitimate
> zero existed.
>
> Two honest conclusions. **Keep the refuter** — three trials on a toy repo is not evidence of absence
> on real work with harder criteria, and conditional refutation makes it cheap insurance. **But do not
> claim it is proven**: its wiring is verified deterministically, its live judgment is not. If a
> session provokes one, record it here.
>
> What *did* the catching was the instruction to verify on the exercised path rather than in isolation.
> That was a per-run constraint at first; it is now standing text in the reviewer prompt, because the
> thing that works should not be optional.

**Narrowing exits to the user.** When a reviewer sets `narrows_scope`, the loop **stops** and
returns `status: 'NEEDS_USER_RATIFICATION'` rather than letting the architect absorb it. A correctly
raised blocker is still a change to the user's question. *(Earned: a methodologically-correct confound
blocker was absorbed silently and became the organizing question across two handoffs, displacing the
user's actual decision question.)* Re-enter the loop after ratification with the decision folded into
the frozen context.

## State minimization

Each agent gets `frozenContext` + the current design + the current findings. Never accumulated
history, never earlier rounds' critiques, never the conversation. In the script this is a property of
what gets passed; in a hand-run loop it is a rule you must hold yourself to.

## Handling the result

```
{ design, rounds, status, readyToImplement, narrowing, surviving, resolvedByRevision,
  unverified, refuted, advisory, questionCheck, ceilingHit, stoppedOnBudget, agentsProjected }
```

A hand-run loop reports the same fields. `resolvedByRevision` holds survivors that a later revision
fixed and a subsequent clean review round affirmed — they no longer block.

**`surviving` and `unverified` are NOT the same thing, and the difference is the point.**
`surviving` = a skeptic tried to kill it and failed. `unverified` = it was over `refuteCap` and
**nobody checked it.** Report them as separate lists; never merge them into a blocker count. *(Measured:
`refuteCap: 1` against 10 blocking findings put 9 unchecked items into `surviving`, where any reader
would assume they had been vetted — refutation's own confusion, reintroduced by its budget.)* If
`unverified` is routinely large, raise `refuteCap` or cut a lens; do not let the list grow silently.

Report to the user:

1. **Plan path** — where you wrote `design`.
2. **What changed, per round** — 2–4 sentences from the architect's `§0 Change log`.
3. **Surviving findings** — vetted live blockers. If any, say plainly the plan is **not ready to implement**.
3b. **Unverified findings** — over the refutation budget, nobody checked them. List separately; do not
    fold them into the blocker count either way.
4. **Refuted findings** — what a skeptic killed, and why. The user may disagree with a refutation.
5. **Question check** — any `drifted` items or a `became_the_question` value, verbatim.
6. **Ceiling** — if `ceilingHit`, say so loudly. Blockers can be generated indefinitely; a reviewer
   still finding them at the ceiling means the design needs re-scoping *with the user*, not another round.

**Preserve friction. Do not smooth over disagreements** — a loop that reports consensus it didn't
reach is worse than no loop.

## Cost

`1 probe agent + maxRounds × (1 architect + lenses + refuteCap) + 1`. At defaults that is up to 23 agents
at the ceiling; a typical 2-round convergent run is ~15.

**Measured, one round with 2 lenses and 3 probe claims on one small repo:** ~306k tokens, ~12 min. The
lenses are the bulk (~111k) and that is where the value is — they do the real code reading. Probes are
~38k for any number of claims up to 6, since they batch into one agent. Batching cut probe cost 66% and
cost ~9% wall-clock, because three parallel probes became one serial agent. The script `log()`s the
projection on entry and logs every finding it passed through unrefuted — **no silent caps.** If a run
needs to be cheaper, cut `refuteCap` or drop a lens; don't cut `maxRounds` to zero-out the tail, which
reintroduces the original defect.

**Budget-aware termination is implemented in the script, not aspirational.** When the session carries
a token budget, the script reserves roughly one round's worth of output and **stops at a round
boundary** when it can no longer afford another, setting `stoppedOnBudget: true` and logging what
remained live. A design stopped this way is `BLOCKED`, not converged — report it as such. A hand-run
loop has no such instrumentation: when the session is running out of room, stop at a round boundary
yourself and report the same way.

Model tiers are per-stage judgment calls — the tiering note at the top of `review-loop.mjs` records
the reasoning. The lenses and refuters run at high effort because adversarial verification is where
effort pays; the pre-flight probes run at low effort because they just execute a command and report
output.

## Why it's bounded at all

- Multi-agent debate research (Peacemaker/Troublemaker, arXiv 2509.23055) shows sycophancy intensifies
  with rounds. The explicit sycophancy warning on every round ≥2 and the hard ceiling are the
  countermeasures.
- Anthropic's multi-agent writeup documents ~15× token cost vs single-agent. State minimization is the
  countermeasure.
- Self-declared convergence alone is a known false-convergence trigger — hence a termination
  *predicate* (no new blocking findings) rather than an agent's opinion that it's done.
- Live evidence for a ≥2-round floor: round 1 caught 10 issues and round 2 caught 3 **new** blockers
  introduced by the round-1 revision. A single round never re-examines its own fix.
