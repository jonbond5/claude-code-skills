---
paths:
  - "**/.claude/rules/*.md"
---

# `rules/` — path-scoped rules for working inside the harness

Every file here carries a `paths:` glob list in its frontmatter, so the harness loads it **only when
Claude reads a matching file**. That is the point: these were all inline in an always-on working
agreement, which loads in full on every session in every project, where trivia competed for attention
with load-bearing verification discipline.

What survives here is **harness-scoped**, not a general engineering rulebook: authoring skills and
workflow scripts, staging and merging, wiring code so it actually executes, and trusting a test
result. Stack-specific lore that used to live alongside it (Python, Docker, databases, ML, GPU,
frontend) was cut — it belonged to one person's stack, not to Claude Code.

| File | Loads when touching | Holds |
|---|---|---|
| `skill-authoring.md` | `**/skills/**/SKILL.md`, `**/.claude/skills/**` | the `allowed-tools:` frontmatter footgun that breaks model invocation while leaving `/slash` working |
| `workflow-scripts.md` | `**/workflows/*.mjs`, `**/workflows/*.js`, `**/.claude/workflows/**` | the dynamic-workflow runner's shape — `node --check` false-failing on its async wrapper, backticks terminating agent-prompt template literals, no clock/randomness/filesystem, agent projection and batching, per-phase outcome gating, never letting the gating agent also repair |
| `git-staging.md` | `**/.gitignore`, `**/.gitattributes`, `**/*.sh`, `**/*.md` | why `git add -A` is barred (especially in scripts and someone else's worktree), deny-all ignore files as review points, and auto-merge silently duplicating a restructured document |
| `writing-code.md` | `**/*.py`, `**/*.ts`, `**/*.tsx`, `**/*.js`, `**/*.jsx`, `**/*.go`, `**/*.rs`, `**/*.java`, `**/*.rb`, `**/*.sql`, `**/*.ipynb` | written-but-never-read values (and the guard shape of that defect), no LLM arithmetic, mirroring existing patterns, non-terminating work-queue predicates, fixtures that fabricate data on the happy path |
| `testing.md` | `**/tests/**`, `**/test_*.py`, `**/*_test.py`, `**/conftest.py`, `**/pytest.ini`, `**/tox.ini`, `**/*.test.ts`, `**/*.test.tsx`, `**/*.spec.ts` | hand-built runners manufacturing false failures, same-session baselines, collected-vs-pass counts, green-CI-isn't-reality, phased TDD, auditing the PASSING tests, harness-reason controls, orphaned in-container processes |

## What did NOT move here

Rules whose trigger is a **situation** rather than a **file type** stayed in the always-on working
agreement — `docs/working-rules.md` in this repo, `~/.claude/CLAUDE.md` once installed: working
style, the verification core (verify the verifier, both-directions guards, null pre-flight),
destructive-op safety, git/worktree discipline, and host-environment facts. A rule here with no
`paths:` field would load unconditionally and save nothing.

## Conventions

- Keep entries in **trigger → rule → tell** shape. The *tell* is how you notice the failure in flight.
- Full incident narratives live in a separate incident log, not here. Never delete an entry
  from the archive.
- Cross-link with plain relative references (`~/.claude/rules/<file>.md`) rather than duplicating a
  rule in two files. One rule, one home.
- `/distill` promotes here. Its Scope test decides project-level vs user-level; its Trigger test
  decides whether an entry is path-scopable (→ this directory) or situational (→ `CLAUDE.md`).
