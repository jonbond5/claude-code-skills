---
name: distill
description: Session-end capture and pruning pass. Scans the current transcript for corrections, stated-rationale decisions, repeated workflows, and self-critique observations; routes load-bearing findings to the right surface (path-scoped rules, always-loaded CLAUDE.md, or auto-memory); reconciles stale status claims in memories and working docs; and enforces a hard budget on every always-loaded surface so it cannot grow without something else shrinking. Runs inline against the active transcript — never delegate to a subagent.
disable-model-invocation: true
allowed-tools: Read Write Edit Glob Grep Bash
---

# /distill

A self-learning pass on the current session. Two jobs, and the second is the one that was missing:

1. **Capture** what this session learned into the surface that will actually load when it's needed.
2. **Enforce the budget.** Every always-loaded surface has a hard cap. `/distill` may not leave one
   larger than it found it without an explicit, reported trade.

> **Why job 2 exists.** This skill previously had a one-way ratchet: it could promote into
> `~/.claude/CLAUDE.md` but was forbidden from pruning it. That file reached **961 lines / ~15,700
> tokens loaded into every session in every project** — 4.8× Anthropic's 200-line target, and 49
> entries against a stated ≤30 aim, with no mechanism able to correct it. Growth was structural, not
> drift. A capture pass that cannot prune is a context leak with good intentions.

## Routing: two tests, in this order

**Test 1 — SCOPE. "Would this rule hold, unchanged, in an unrelated project?"**
Yes → user-level. References this project's names, paths, agents, infra, or magic numbers →
project-level. When a generic principle is entangled with a project-specific example, **split it** and
cross-link. Genuinely unsure → project-level (a wrongly-global rule pollutes every project; a
wrongly-local one is merely under-shared).

**Test 2 — TRIGGER. "Is this rule triggered by a FILE TYPE, or by a SITUATION?"**

| | File type triggers it | A situation triggers it |
|---|---|---|
| **User-level** | `~/.claude/rules/<topic>.md` **with `paths:`** | `~/.claude/CLAUDE.md` |
| **Project-level** | `<project>/.claude/rules/<topic>.md` **with `paths:`** | `<project>/.claude/CLAUDE.md` |

A rules file **without** `paths:` loads unconditionally and saves nothing — it is just CLAUDE.md with
extra steps. Only write one when the `paths:` globs are real.

**Standard tier** (neither critical nor path-scoped): the auto-memory directory, indexed by its
`MEMORY.md`. Use for durable facts that don't shape behavior on every touch.

**Legacy:** `.claude/CRITICAL.md` is superseded by `.claude/rules/`. When a project still has one,
migrate the entries you touch this run and note the rest in the summary. Don't bulk-migrate a file
this session didn't engage with.

## Setup (every invocation; no-op when already set up)

```bash
project_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
project_hash=$(echo "$project_root" | sed 's:[/_.]:-:g')
memory_dir="$HOME/.claude/projects/$project_hash/memory"     # harness auto-memory dir
project_rules="$project_root/.claude/rules"                   # git-tracked
project_claude="$project_root/.claude/CLAUDE.md"              # git-tracked
user_rules="$HOME/.claude/rules"                              # not tracked in any repo
user_claude="$HOME/.claude/CLAUDE.md"
legacy_critical="$project_root/.claude/CRITICAL.md"            # migrate on touch
```

Create `$project_rules` if a project-level promotion needs it. Tell the user project-level surfaces
are git-tracked and want committing.

**Do NOT hand-manage `$memory_dir/MEMORY.md`'s length.** The harness measures it against its own
200-line / 25KB read limits after every write and errors if it's over. That logic was removed from
this skill; don't reintroduce it.

## Phase 1 — Scan the transcript

Walk the conversation already in your context. Four signal classes:

1. **Corrections.** User said "no", "don't", "stop", "actually X", "wrong", or visibly redirected you.
2. **Stated-rationale decisions.** A "because Y" reason for a choice. *The rationale is the
   load-bearing part; the choice is usually re-derivable from code.*
3. **Repeated workflows.** Same procedure 3+ times this session, or the user said "every time"/"always".
4. **Confirmed non-obvious approaches.** An unusual choice accepted without pushback, especially where
   an obvious alternative existed. Quiet signal, captures validated judgment.

Track raw candidates. Defer filtering to Phase 2.

## Phase 2 — Critique, including self-critique

Two filters per candidate:
- **3-session test.** Will this matter in 3 future sessions here? No → drop.
- **Root cause, not symptom.** For mistakes, capture *why* the wrong choice was made (violated memory
  X; assumed Y without checking), not the surface output.

Then the highest-value step — explicit self-critique:
- **Memory violations.** For each existing entry in `$memory_dir/`, the rules files, and the CLAUDE.md
  files: did your behavior this session contradict it? Every violation is top-priority. Don't write a
  new entry — **sharpen the existing one** with a `**Why this matters:**` line citing the violation,
  and promote it if it isn't already at the right tier.
- **Wasted detours.** Debugging the user had to redirect. Root-cause it.
- **Missed obvious.** Anything the user pointed out twice.

## Phase 3 — Consolidate

Diff each survivor against what exists before writing:
- **Exact overlap** → no-op.
- **Partial overlap** → update in place, keep the slug, sharpen the wording.
- **Reinforcement** (existing rule violated this session) → sharpen + promote.
- **Genuinely new** → new entry at the tier the two routing tests select.

Write entries in **trigger → rule → tell** shape. The *tell* is how the failure gets noticed in
flight; an entry without one is advice, not a rule.

Link related memories with `[[slug]]`. Never write duplicates. **One rule, one home** — cross-link
rather than restating a rule in two files.

**Full incident narrative goes to a separate incident log, not into the rule.** The rule carries
trigger, rule, and a one-clause tell; dates, exact numbers, wrong root-causes, and recovery
procedures go to the archive. Append; never delete an archive entry.

## Phase 3.5 — Reconcile stale status claims

Capture adds what was learned; this reconciles what was *already written* against what is now true. A
memory saying "not started" about work that shipped this session actively misleads the next agent —
worse than no memory.

**3.5a — Status-bearing memories.** Scan the memory index (open the file when a line is ambiguous) for
work-status assertions: "TODO", "pending", "planned", "in progress", "blocked", "not started",
"SHIPPED", "plan only", dated state claims, "verify before relying". For each whose subject this
session **advanced, completed, unblocked, abandoned, or contradicted**:
- **State changed** → update body AND description/index line, with an absolute date. Preserve durable
  rationale; only the status wording changes.
- **Finished, nothing durable left** → fold surviving rationale elsewhere, delete the tracker.
- **Status now unknown** → mark it "unverified as of <date> — <what changed>". An honest question mark
  beats a stale claim.

**3.5b — Working documents.** Repo-resident docs the session created, edited, or executed from (plan
docs, handoffs, phase checklists, `.sf/` files). Add or refresh a dated status banner at the top and
tick/strike completed items. **Do not delete working documents here** — banner-and-annotate. Note git-tracked ones in the
summary.

**Guardrails.** Ground truth only: verify "done/shipped/passing" against evidence from this session
(git log, actual test output, observed state) — never a subagent's unverified claim. If you can't
verify cheaply, write "unverified as of <date>". Only touch status-bearing entries and documents
actually referenced this session. Don't rewrite what you didn't observe.

## Phase 4 — Re-rank, and ENFORCE THE BUDGET

### Budgets (hard, not aspirational)

| Surface | Cap | On overflow |
|---|---|---|
| `$user_claude` | **200 lines** | Mandatory trade — see below |
| `$project_claude` | **200 lines** | Mandatory trade |
| any single rules file | **~150 lines** | Split by sub-topic |
| `$memory_dir/MEMORY.md` | harness-enforced | Move detail to topic files |

### The prune mandate

**Adding to an always-loaded surface obligates you to find the offsetting reduction in the same run.**
Options, in preference order:

1. **Relocate, don't delete.** The entry is path-scopable → move it to a rules file with `paths:`. This
   is the cheapest trade and usually available: most footguns are triggered by a file type.
2. **Compress in place.** Cut narrative to the archive, keep trigger + rule + tell.
3. **Demote.** Constraint lifted, footgun fixed in code (**grep to verify first**), or a procedural
   default replaced by tooling (a pre-commit hook now runs the step).
4. **Merge.** Two entries describing one mechanism become one with two tells.
5. **Refuse the promotion.** Leave the candidate at standard tier and **say so in the summary** with
   what it lost to. This is a legitimate outcome, not a failure.

**If a surface is over its cap at the START of a run, reduce it whether or not you are adding.** Report
the delta. A run that leaves an over-cap surface unchanged has not done job 2.

`$user_claude` and `$user_rules` aggregate rules from *all* projects, and this session sees one.
Age-based auto-pruning does not apply to user-level surfaces.

**RELOCATION IS NOT DELETION, and on an over-cap user surface it is MANDATORY.** Moving an un-earned entry from `$user_claude` to `$user_rules` with real `paths:`
globs loses nothing — the rule still loads, just when it is relevant — so it is always permitted, and
when `$user_claude` is over cap it is **required whether or not you are adding anything.**

*Why this is spelled out: on 2026-07-29 this skill compressed the entries it reinforced, correctly, and
still left `$user_claude` at 457 lines against a 200 cap — up from 442. It read the protection as
forbidding it from touching un-earned entries at all, so an over-cap file could only grow. That is the
one-way ratchet this phase exists to break, wearing a different hat. If nothing is left to relocate and
the file is still over cap, say so explicitly in the summary as an unresolved budget breach — do not let
it pass silently.*

### Pruning the standard tier (autonomous)

Delete from `$memory_dir/` when ALL hold: older than 90 days, AND not user-identity, AND not surfaced
or reinforced this session, AND the subject is no longer active (deadline passed, feature shipped,
system removed) OR it is a post-consolidation duplicate.

### Rebuild

Rebuild project-level surfaces from current state — this session sees the whole project. Touch
user-level surfaces **surgically**: insert or sharpen what this run earned, apply relocations and
compressions, leave every untouched entry byte-for-byte intact.

## Final output

One summary, then stop. Deltas only — do not narrate the scan or the critique.

```
/distill summary
  Added:      N  (one line each, with destination surface)
  Updated:    M  (one line each)
  Relocated:  R  (CLAUDE.md -> rules/<file>.md, with the paths: globs)
  Compressed: C  (entry, lines before -> after)
  Demoted:    D  (with why; grep evidence for any "fixed in code")
  Refused:    F  (candidate, and what it lost the budget trade to)
  Tidied:     T  (status reconciliations, old -> new; flag git-tracked docs)
  Pruned:     Q  (standard tier only, one-line reason each)

  BUDGET
    ~/.claude/CLAUDE.md        <before> -> <after> lines   / 200 cap
    <project>/.claude/CLAUDE.md <before> -> <after> lines   / 200 cap
    rules files touched         <name>: <lines> / 150
    legacy CRITICAL.md          <migrated N entries | none present | N left, not touched>

  Reminder: project-level surfaces are git-tracked — commit when ready.
```

**Every always-loaded surface reports before → after.** A run whose caps all read unchanged while
entries were added has violated the prune mandate — say so explicitly rather than hiding it.

## Taxonomy — the seven categories

Each answers "what fails if I forget this?"

1. **Architectural constraints with non-obvious rationale.** If I forget, I will re-propose violating it.
2. **Hard requirements / non-negotiables.** Absolute language, or violations produce wrong answers.
3. **Procedural defaults.** A named trigger + a default action. Both halves required.
4. **User-identity context framing interaction register.** Usually one entry total.
5. **Safety rules for destructive or shared-state actions.** Hard or impossible to reverse.
6. **Cross-cutting domain invariants.** Not visible from any one file; forgetting them produces code
   that compiles but breaks the system.
7. **Silent-failure footguns.** The wrong code looks correct and tests can pass while it's broken.

**Promotion mechanic.** Any standard-tier memory contradicted in **two observable sessions**
auto-promotes to its routed tier with a sharpened `**Why this matters:**` note citing both violations.
This is how `/distill` learns from its own failures, not only from user corrections. **The promotion
still pays the budget trade** — it is not exempt.

## What NOT to capture

Reject at Phase 1: ephemeral task state; anything `git log`/`git blame` already tells you; code
patterns, conventions, and file paths derivable from reading the project; summaries of what just
happened; "useful to know" trivia that doesn't shape behavior.

## Notes

- **Runs inline.** The transcript lives in your context; a subagent would not have it. Do not use
  `context: fork`.
- **`disable-model-invocation: true`** is deliberate — this skill rewrites global config and prunes
  memories. It fires when the user asks, not when Claude judges the moment right.
- Session-transient **Docker** assets are no longer swept here. That was an unrelated concern costing
  tokens on every invocation — it now lives in `/docker-sweep`. Suggest it in the summary when this
  session built images or ran throwaway containers.
- Cross-session pattern detection is future work; the 3-in-session repetition threshold is the v1 rule.
