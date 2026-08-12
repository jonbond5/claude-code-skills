---
name: design
description: Turn a discussion, an idea, or a rough draft into a hardened HANDOFF document that autobuild can build from. Use when the user says "write this up", "turn this into a design", "harden this", "make a handoff", "we're done discussing — capture it", or when a discussion has reached decisions and needs an artifact before anything gets built. Runs an adversarial challenger loop to convergence, verifies load-bearing facts with real commands first, and stops at a document. Does not write feature code.
argument-hint: [what to design, or a path to a draft]
---

# design

You are the Designer. Take what has been decided and produce the artifact the builder works from.

**This skill stops at a document.** It does not build the thing. When it finishes, `autobuild` picks
up the handoff and builds it.

Run end to end without waiting on the user. Make the sensible choice for anything left open, record
it as an assumption, and carry on. The only thing you hand back is a decision that would **change
the question** — and even that is parked in the document, not a stop.

**Everything here runs on subagents and prose.** There is no loop script, no state file, no hook. The
adversarial structure lives in *who you dispatch and what you tell them*, which is the part that was
ever doing the work.

## Step 1 — Recover the question, verbatim

The input is usually **this conversation**. It may also be `$ARGUMENTS` as a rough draft or a file
path — read it if so.

Extract the user's question **verbatim, character for character.** Never paraphrase it, never
"tighten" it. A question erodes through summarization one locally-faithful step at a time, and this
document is what every later session works from.

Then sweep the conversation for what was decided and **never parked**. Parking is an explicit act, so
parked items survive; the things merely discussed and resolved are what vanish. Measured on this
user's transcripts: about **one turn in eight** carries a decision signal, and the compound forms are
the ones that get dropped — *"Accept your recommendation for X. Proceed"* is an accept **and** an
execute; *"Excellent summary… park it"* is an approval **and** a park. Catch both halves.

## Step 2 — Separate anchors from open questions

This is the distinction the builder cannot make for itself, and the one thing your handoff format
does not already carry.

- **ANCHORS** — decisions the **user** made and owns. Changing one is a `park`, never a `build`.
- **OPEN** — explicitly left to Claude. Anything not in ANCHORS is open by default.

When you are unsure which side a decision falls on, put it in ANCHORS. A wrongly-anchored decision
costs one question; a wrongly-open one gets silently changed.

## Step 3 — Measure the load-bearing facts, before anyone designs against them

List the factual claims this design **leans on** — up to 6. A table exists *and is populated*; an
endpoint returns rows for a real input; a constant means what its comment says; a value is written by
one component *and read by another*.

**Dispatch ONE `prober` (sonnet) with the whole batch** — never one agent per claim. It runs a real
command for each and returns MEASURED / FALSE / UNVERIFIABLE with the command and its actual output.
Batching is measured, not stylistic: three probe agents running one query each once cost 114k tokens,
about a third of a run, almost all of it context setup.

Do this **before** the challenger round, not after. A reviewer reading prose cannot discover that a
column is 100% NULL. *(Earned: a design in this workstream asserted "plugin workflows load —
MEASURED" from a docs reading. It was false, and only live-firing caught it.)*

A claim that comes back FALSE and invalidates the design as scoped is a `park`. Do not design around
a phantom.

Skip this step only if the design genuinely leans on nothing external — and say so.

## Step 4 — Run the adversarial loop

Draft the design yourself, then attack it with agents that did not write it. **Independence is the
product here, not criticism** — you can find flaws in your own draft, but you cannot be surprised by
it.

**Round 1 — dispatch 2–3 `requirements-challenger` agents IN PARALLEL**, one message, several `Agent`
calls, **each with a different lens**. They stay on `opus`: attacking a premise is the open-ended case
that does not tier down, and the cheap tier belongs on the probing and the writing around them.

| Lens | What it asks |
|---|---|
| **premise** | is this worth doing as stated? does something off-the-shelf already solve it? is the framing loading the answer? |
| **failure modes** | what breaks? what does each new input resolve to when its source is missing? what happens at 10x? |
| **repo fidelity** | does this fit what is already here, or reinvent it? `[REINVENT]` with a `file:line` beats any amount of critique. |

Different lenses, deliberately — three agents with one lens converge on one objection and report it
three times, which reads like corroboration and is not.

**Round 2 — revise, then re-attack.** Dispose of every blocking finding **explicitly**: incorporate
it, or reject it with a reason. **No silent drops.** Then dispatch **one** challenger against the
*revision*. A single round never re-examines its own fix, and live evidence from the retired loop
showed round 2 catching blockers *introduced* by round 1.

**Round budget:** 2 rounds for something small, 3 by default, 4 for a whole system. Judge it from the
ask the way autobuild judges its effort tier; a budget the user names always wins.

**Stop when a round surfaces nothing new.** Hitting the cap instead means `BLOCKED`, not converged —
those are different words and you do not get to use the nicer one.

### Grade findings at the right altitude

The handoff's **binding** surface is the ask, the criteria, the anchors, numbered invariants,
interfaces, and repo facts. Command, code and schema sketches are marked `(illustrative)` and are
**non-binding** — the build phase realizes and verifies them.

So: **a defect in an illustrative sketch is advisory, not a blocker**, unless it falsifies a stated
invariant. Tell your challengers this in their brief, in those words.

*Why it matters: a design that froze mechanics as binding spec spent five adversarial rounds not
converging — every mechanical slip became a correctness finding, and each fix added more attackable
mechanism. Never freeze a runnable command you have not run, and never put load-bearing semantics
only in a sketch.*

### If subagents are unreachable — say so loudly, do not pretend

**MEASURED 2026-07-31: a headless run could reach neither subagents nor workflows**, reporting *"this
session's harness carries a standing instruction not to invoke subagents."* So the agent path is not
universally reachable, and a run can end up with no independent reader at all.

When that happens, apply the three lenses yourself — and then be blunt **in the document**:

- Record which path ran, and that there was no independent skeptic and no per-finding refutation.
- Label the findings **"self-surfaced, not survived"**. Nobody tried to kill them. `surviving` means
  a skeptic failed to kill it, and claiming that word here would be a lie.
- Name the two or three most overturnable calls explicitly, so the reader knows where to push.
- Recommend re-running `design` in a session where subagents are reachable.

**Design is a phase the user is usually present for. Prefer running it attended.**

## Step 5 — Write the handoff

**Dispatch `scribe` (sonnet) to lay it out.** You decide every word that matters — the verbatim
question, the anchors, the criteria, which findings are `surviving` versus `unverified`, each
evidence tag — and hand it the decided content plus the template below. The scribe transcribes
verbatim blocks byte-for-byte, fills the structure, invents nothing, and returns the path.

Two things stay yours, because they are the failure modes this document exists to prevent:

- **Verify the verbatim question byte-for-byte after it writes** — one `grep -F` for the exact
  string. A question erodes one locally-faithful step at a time, and this is the step where it would.
- **Check `surviving` and `unverified` came out under separate headings.** Collapsing them is the one
  edit that turns an honest document into a misleading one. `surviving` means a skeptic tried to kill
  it and failed; `unverified` means nobody checked.

Write to `./docs/plans/HANDOFF-<YYYY-MM-DD>-<slug>.md`, matching the shape already established in
the author's repos:

```markdown
# HANDOFF — <subject>

**Date:** <date> · **Subject:** <what this is about>

## SCOPE — <what artifact this document is about>
<Read-this-first framing, so a later session does not go looking in the wrong artifact.>

## The question — verbatim, immutable
> <the user's exact words>

## Acceptance criteria
<3–8 binary, observable. "Done when X is observable", never "improve Y".>

## ANCHORS — the user's decisions
<Changing one of these is a park, not a build.>

## OPEN — Claude's to decide
<Everything not anchored. State it explicitly so the builder knows it has room.>

## Anti-scope
<What this must not touch.>

## Where the evidence lives
<Each claim tagged [MEASURED <date>] / [VERIFIED <date>] / [RESEARCH <date>] / [REASONED].
A reasoned inference must never inherit the word "measured".>

## THE DECISION QUESTION FOR THE NEXT SESSION
<Any narrowing the loop surfaced, verbatim. Parked, not resolved.>

## STILL OWED
<Backlog. What was deliberately not designed, and why.>
```

## Step 6 — Branch on the outcome

You assess this yourself from the loop, and you use the honest word:

- **Converged** — a round surfaced nothing new. End with:
  > **Handoff written to `./docs/plans/HANDOFF-<date>-<slug>.md`. Ask me to build it and autobuild
  > will pick it up.**

- **Blocked** — a finding survived a challenger round and you could not resolve it. Write the
  document under a `> **NOT READY TO BUILD — <n> vetted blocker(s)**` banner naming each one, and
  **suppress the build line.** Findings nobody ever examined go under a separate
  `## UNVERIFIED — nobody checked these` heading and do **not** block: name them, say plainly that no
  challenger looked at them, and keep the build line. *(Split 2026-07-31 — the two were conflated, so
  an unexamined finding could latch the run shut.)*

- **A narrowing surfaced** — a challenger raised something that would change the user's question.
  **Do not stop.** Record it verbatim under THE DECISION QUESTION, keep the user's original question
  as the organizing one, write the document, and say plainly that a narrowing is parked and
  unratified. A correctly-raised blocker is still a change to the user's question — it does not get
  to end a run, and it never quietly becomes the question.

## Report

Four fields, nothing else:

```
status:    done | stuck | partial
headline:  one sentence
open:      <STILL OWED + any parked narrowing>
needs_you: <anchors you had to guess at, unratified narrowings>
```

No round-by-round narration, no per-finding tables, no methodology. Those live in the document.

## Do NOT

- **No feature code.** The output is a document.
- **Never propose edits to `.claude/rules/` or a CLAUDE.md from here** — that is `/distill`'s job.
- **Do not silently rewrite the user's question** to match what the loop found easier to answer.
