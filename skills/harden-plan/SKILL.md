---
name: harden-plan
description: Take an implementation plan or design idea that ALREADY EXISTS (usually one Claude just wrote, or a doc/file) and run an adversarial architect-reviewer workflow to attack its assumptions, surface blockers, and iterate it into a hardened plan. Use when you are HOLDING a plan and want it challenged. If you only have a feature idea, use the autobuild plugin's design skill; for a whole project or major refactor, use /project-to-plan.
argument-hint: [plan-text-or-file-path]
disable-model-invocation: true
disallowed-tools: Edit NotebookEdit
---

# Harden Plan

You are holding a plan. This skill attacks it. It does **not** re-plan from scratch — the plan is the
seed, and an adversarial loop tries to break it.

`disallowed-tools: Edit` is deliberate: the output is a plan, and the harness enforces that rather than
trusting a prose instruction.

## Files this skill reads

Repo-relative paths below refer to this repository's `skills/_shared/` directory: `review-loop.md`
(the loop contract), `architect-agent.md` and `researcher-agent.md` (subagent prompts). Install them
somewhere this skill can Read them — alongside the skill is fine — and adjust paths to match.

## Input

The plan is in `$ARGUMENTS`.

- An existing file path → **Read it**, use the contents as the plan.
- Otherwise → treat `$ARGUMENTS` as the plan text directly.
- **Empty** → the plan is most likely the one you just produced earlier in THIS conversation. **Say
  which plan you are about to harden before launching anything.** Never guess silently.

## Pre-loop

Deliberately thin. This skill does not re-plan. All of it is inline — the interactive parts cannot go
into the loop, which runs in the background and cannot ask the user anything.

1. **Verbatim ask.** Capture the USER'S ask **verbatim** — the question this plan exists to answer,
   distinct from the plan text being hardened. If it isn't stated anywhere, ask for it before starting.
2. **Acceptance criteria.** If the plan states them, lift them **verbatim**. If not, derive **1–5
   binary, observable** criteria. **A review loop with no success definition just produces opinions.**
3. **Binding constraints.** If cwd is a relevant repo, read the project's rules surface — `CLAUDE.md`,
   `.claude/rules/*.md`, or whatever the project uses — and carry the entries touching this plan's
   area. If none apply, say so explicitly.
4. **Load-bearing facts.** Skim the plan for factual claims it *depends* on — a table has rows, a
   column is populated, an endpoint exists, a constant means what a comment says. Collect up to 6 as
   `probeFacts`. **These get verified with real commands before the architect designs against them** — a
   reviewer reading prose cannot discover that a column is 100% NULL.

## Loop

`mkdir -p ./docs/plans`. `<slug>` = lowercased hyphenated 3–6 word name from the plan's subject, no
articles. **If the input was a file under `./docs/plans/`, overwrite that same file.**

Run the shared architect ↔ reviewer loop with these parameters:

- `frozenContext`: verbatim ask + acceptance criteria + binding constraints
- `seed`: the plan, VERBATIM
- `maxRounds`: 3
- `probeFacts`: the load-bearing facts from pre-loop step 4

The loop contract — round structure, convergence predicate, dedup, refutation cap, exit statuses — is
defined once in `skills/_shared/review-loop.md`. Read it and follow it. Do not reimplement round logic
here.

Bare skills cannot register agents, so spawn each role as a **general-purpose subagent**: the
architect gets the body of `skills/_shared/architect-agent.md` as its prompt, and each review lens
gets `skills/_shared/researcher-agent.md` plus its lens instruction — always followed by the frozen
context and the current design. If the **autobuild plugin** is installed, its `design` skill drives a
mechanized implementation of the same loop (`plugins/autobuild/workflows/review-loop.mjs`); prefer
that when it is reachable, because there the control flow is code, not prose you interpret.

## Finalize

Write the loop's returned `design` to `./docs/plans/<slug>.md`, with the **verbatim ask and decision
question at the top, above methodology** — successors spec work against the question, not the plan's
most-emphasized section.

Then branch on `status`:

- **`CONVERGED`** → report per the shared contract's "Report to the user" section, then end with:
  > **Plan written to `./docs/plans/<slug>.md`. Run `/implement-plan ./docs/plans/<slug>.md` to build it.**

- **`BLOCKED`** → write the plan with a `> **NOT READY TO IMPLEMENT**` banner naming every surviving
  finding. **Do NOT emit the `/implement-plan` line.** Say plainly that the loop hit its ceiling with
  live blockers and the design needs re-scoping with the user.

- **`NEEDS_USER_RATIFICATION`** → do not write a final plan. Surface the narrowing findings verbatim and
  ask whether to accept the narrowed question, reject it, or defer. On an answer, re-enter the loop
  with the ratified decision folded into the frozen context.

Pay particular attention to **refuted** findings — the user brought this plan in, so they have a stake
in what a skeptic killed and why.

## Do NOT

- Do **not** silently rewrite the user's plan without running the loop.
- Do **not** expand scope beyond the plan's subject.
- Do **not** raise `maxRounds` past 5. If blockers still live there, the answer is re-scoping with the
  user, not another round.
