---
name: project-to-plan
description: Take a whole-project idea or major refactor and drive it to a hardened implementation plan. Stage A hardens your REQUIREMENTS interactively — reviewer agents challenge the idea and its assumptions, you refine, up to 3 rounds. Stage B turns the hardened requirements into a plan via a non-interactive architect-reviewer loop. Use for a fresh repo, a new system/service, or a major refactor. For a single feature, use the autobuild plugin's design skill; to attack a plan you already hold, use /harden-plan.
argument-hint: [project-idea-or-brief-path]
disable-model-invocation: true
---

# Project → Plan

Two stages, and **the distinction between them is the whole point**:

- **Stage A — requirements hardening. INTERACTIVE.** The user is the decision-maker being challenged.
- **Stage B — plan. NOT interactive.** The agents argue with each other.

Never blur them.

## What this skill needs

Standalone skills cannot register named agents — only plugins can — so this skill spawns
**general-purpose subagents primed with prompt files** shipped alongside it:

- `skills/_shared/researcher-agent.md` — the adversarial reviewer (Stage A challengers, Stage B lenses).
- `skills/_shared/architect-agent.md` — the architect (Stage B, hand-run path).
- `skills/_shared/review-loop.md` — the loop's full contract and reporting rules.

Install `skills/_shared/` next to this skill's folder and read the prompt files from there. "Prime"
means: read the file and paste its full contents at the top of the subagent's prompt, then append the
task-specific input below it.

Optionally, install the [autobuild plugin](../../plugins/autobuild/): its
`workflows/review-loop.mjs` runs Stage B's loop deterministically. Without it, run the loop by hand
(described in Stage B).

Downstream: the plan this skill writes is what `/implement-plan` (`skills/implement-plan/`) builds
and `/harden-plan` (`skills/harden-plan/`) re-attacks.

## Input

`$ARGUMENTS` is the project idea, or a path to a brief — **Read it** if it is a path. If empty, ask what the project is.

If this is a **refactor of an existing repo** rather than a fresh build, additionally read the
project's rules surfaces — its `CLAUDE.md` and any `.claude/rules/*.md` — and note the existing
stack and conventions. A refactor's requirements are constrained by what already exists, and
**those constraints belong in `frozenContext`**.

---

## Stage A — Requirements hardening (INTERACTIVE, max 3 rounds, early exit)

Attack the **idea** and its **assumptions** before any design exists. Most bad projects are bad at the requirements layer, and no amount of architect-reviewer looping downstream can fix a requirement that should never have existed.

### Each round

**1. Write the current requirements statement.**
Round 1: derive it from the user's idea. Later rounds: it is the version the user refined at the end of the prior round. Keep it short — what the project does, for whom, the hard constraints, and the assumptions it rests on. **State the ASSUMPTIONS explicitly and separately.** They are the primary attack surface.

**2. Spawn 2 general-purpose subagents IN PARALLEL** — a single message with 2 `Agent` calls — each
primed with the reviewer prompt from `skills/_shared/researcher-agent.md`, and with **DIFFERENT
lenses**, so they do not converge on the same objection:

- **Lens 1 — Premise.** Is this project worth doing as stated? Attack the problem framing, the assumptions, unstated dependencies, whether an off-the-shelf product or library already solves it, and whether the stated users actually want this.
- **Lens 2 — Feasibility.** Attack scope, hidden complexity, the riskiest technical bet, the requirement most likely to be underestimated, and what would make this fail at 10x the stated scale.

Both use the reviewer prompt's tag system (`[BLOCKER]` / `[REINVENT]` / `[PATTERN]` / `[NITPICK]`) and end with a Verdict line. **Tell them explicitly they are critiquing REQUIREMENTS, not a design doc** — there is no architecture yet, and demanding one is out of scope.

**3. Present the challenges to the USER** — deduplicated, grouped by lens, blocking tags first. **Be blunt. Do not soften a `[BLOCKER]` into a suggestion.** Then ask the user to respond to each blocking item: **accept** it and change the requirement, **reject** it with a reason, or **defer** it as an open question.

**4. Fold the user's responses into a revised requirements statement.**

### Early exit

Advance to Stage B immediately if **either**:

- a round returns **zero blocking-tag items** (`[BLOCKER]` / `[REINVENT]` / `[PATTERN]`) across both lenses, **or**
- the user says to move on.

**Do not run rounds the user has not earned.** After round 3, advance regardless, carrying any unresolved items forward as **explicit open questions** in `frozenContext`.

### Exit gate

Present the final hardened requirements and get **one explicit confirmation** before Stage B. Derive **3–8 binary, observable acceptance criteria** from them — Stage B's loop and any downstream `/implement-plan` run are worthless without them.

---

## Stage B — Plan (NON-INTERACTIVE)

Say plainly that **the user is now hands-off**: the agents argue with each other, not with the user.
That sentence is the workflow boundary — Stage A cannot go into a scripted workflow (it stops for the
user every round); Stage B is exactly what one is for.

`mkdir -p ./docs/plans` first. `<slug>` = lowercased hyphenated 3–6 word project name, no articles.

Before launching, collect **`probeFacts`** — the load-bearing factual claims the requirements assume
about the existing world (a service exists, a schema has these columns and rows, an API returns what
the brief says). Up to 6. For a fresh repo there may be none; say so. For a refactor there are always
some, and they are where the expensive surprises live.

### With the autobuild plugin installed

Invoke its loop script (in this repo: `plugins/autobuild/workflows/review-loop.mjs`) by path:

```
Workflow({
  scriptPath: "<autobuild plugin root>/workflows/review-loop.mjs",
  args: {
    frozenContext: <hardened requirements + acceptance criteria + binding constraints
                    + unresolved Stage-A open questions>,
    seed:          <the hardened requirements>,
    maxRounds:     4,
    dryRounds:     2,
    probeFacts:    [...]
  }
})
```

Invoke by **`scriptPath`, never by name** — named workflow resolution does not reach plugin
workflows in current CLI versions.

`dryRounds: 2` is deliberate here — a whole project earns a stricter convergence bar than a single
feature. Full contract, including how to report `surviving` vs `unverified` findings:
`skills/_shared/review-loop.md`.

### Without it — run the loop by hand, keeping independence

Do **not** design alone; that trades away the one thing this stage exists for.

1. **Probe first.** Dispatch one subagent with the whole `probeFacts` batch — never one per claim —
   to verify each with a real command and return MEASURED / FALSE / UNVERIFIABLE with the actual output.
2. **Draft.** One general-purpose subagent primed with `skills/_shared/architect-agent.md`, given
   `frozenContext`, the probe results, and the hardened requirements as the brief.
3. **Review.** 2–3 subagents primed with `skills/_shared/researcher-agent.md`, IN PARALLEL, each with
   a different lens (reinvention / failure modes / repo fidelity). Each gets `frozenContext` + the
   current design — never earlier rounds' critiques, never the conversation.
4. **Revise.** The architect disposes of **every** blocking finding explicitly — incorporate, reject
   with a reason, or mark an open question, in a §0 Change log. No silent drops.
5. **Repeat review on the revision.** A single round never re-examines its own fix — round 2 is where
   blockers *introduced by* round 1's changes get caught. Stop after **2 consecutive rounds that
   surface zero new blocking findings**, or at 4 rounds. Hitting the cap means **BLOCKED**, not
   converged.

## Finalize

Report per the shared engine's standard finalize output (`skills/_shared/review-loop.md`, "Handling
the result"), **plus** a short **Requirements hardening** section: how many Stage-A rounds ran, what
the user changed in response to challenges, and what was deferred.

Then branch on `status`:

- **`CONVERGED`** → end with exactly:
  > **Plan written to `./docs/plans/<slug>.md`. Run `/implement-plan ./docs/plans/<slug>.md` to build it.**
- **`BLOCKED`** → write it under a `> **NOT READY TO IMPLEMENT**` banner listing every surviving
  finding, and **suppress the `/implement-plan` line.**
- **`NEEDS_USER_RATIFICATION`** → surface the narrowing findings. On a project this usually means a
  Stage-A requirement was wrong; consider one more Stage-A round rather than forcing Stage B through.

(On the hand-run path there is no `NEEDS_USER_RATIFICATION` machinery — treat any reviewer finding
that would **narrow the user's question** the same way: surface it to the user rather than letting
the architect absorb it.)

## Hard rules

1. **Stage A is interactive and Stage B is not.** Never blur them.
2. **Never skip Stage A because the idea "seems clear."** That is exactly when unexamined assumptions survive.
3. **Stage B never revisits a requirement the user settled in Stage A.** That is drift — it belongs in the open-questions list, not the plan.
4. **No code in this skill.** The output is a plan.
