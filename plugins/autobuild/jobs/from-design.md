# Job: build from a handoff document

The seam. `design` wrote a handoff; you build it. Assumes the gate in `SKILL.md` step 2 is cleared.

## 1. Read the handoff, and take the question from it

Read the file. The contract lives in these sections — everything else is context you may read but are
not bound by:

| Section | What it means to you |
|---|---|
| `## The question — verbatim, immutable` | the root ask. Copy into the run note **verbatim**. |
| `## Acceptance criteria` | what `done-judge` verdicts against |
| `## ANCHORS` | the user's decisions. Changing one is a `park`, never a `build`. |
| `## OPEN` | explicitly yours. Decide and log; do not ask. |
| `## Anti-scope` | never touch, regardless of what a discovery argues |
| `## Where the evidence lives` | claims and their evidence class |
| `## THE DECISION QUESTION` | a parked narrowing — carry it forward, do not resolve it |
| `## STILL OWED` | backlog. Do NOT build these. |

**Refuse to build a handoff carrying `NOT READY TO BUILD`.** Surface its surviving findings and stop.

**Anything not in ANCHORS is yours to change.** That default is the point of the format — the
document can be as opinionated as it likes about approach without freezing your hands.

## 2. Re-verify what the design leaned on

**Dispatch ONE `prober` (sonnet) with every claim you need re-checked** — not one agent per claim. It
runs a real command for each and returns MEASURED / FALSE / UNVERIFIABLE with the command and its
actual output. Batching is measured, not stylistic: three probe agents running one query each once
cost 114k tokens, about a third of a run, almost all of it context setup.

The handoff's evidence tags tell you how much to trust each claim, and which ones go in that batch:

- `[MEASURED <date>]` / `[VERIFIED <date>]` — measured *then*. **Re-check anything you will build on.**
  A measurement is a point-in-time observation, not live state.
- `[RESEARCH <date>]` — external, may have moved.
- `[REASONED]` — **never** treat as measured. If the plan leans on it, measure it now.

A claim that comes back FALSE is a finding: if it invalidates the design as scoped, that is a `park`
and it goes in `needs_you`. Do not design around a phantom. *(A design in this very workstream
asserted "plugin workflows load — MEASURED" from a docs reading. It was false.)*

## 3. Then join the normal path

Everything from here is `build-feature.md` step 3 onward — cut units so their file lists are disjoint,
build them in parallel worktrees, attack every claimed pass, judge, integrate.

Two differences that persist for the whole run:

- **ANCHORS raise the bar for `scope-arbiter`.** A discovery that would change an anchored decision is
  `park`, even when it looks like it merely serves the ask. The user already decided that one.
- **`STILL OWED` is not a backlog you may promote.** It was deliberately deferred. A discovery that
  happens to match a STILL OWED item stays deferred unless it now *blocks* an acceptance criterion.

## 4. Close

Update the run note with the final verdict, then report the four fields. Carry any parked narrowing
from THE DECISION QUESTION into `needs_you` — it was unratified when the design was written and it is
still unratified now.
