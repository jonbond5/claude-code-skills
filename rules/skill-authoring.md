---
paths:
  - "**/skills/**/SKILL.md"
  - "**/.claude/skills/**"
---

# Authoring a skill

Relocated 2026-07-31 out of the author's own always-on `~/.claude/CLAUDE.md` (the equivalent surface
in this repo is `docs/working-rules.md`) — the trigger is *editing a skill definition*, which
is a file type, so it does not belong on a surface that loads in every session of every project.

## `allowed-tools:` silently breaks MODEL invocation

**Trigger:** adding or keeping an `allowed-tools:` line in a skill's frontmatter.

**Rule:** it breaks invocation **via the Skill tool** — the call returns an opaque
`Execute skill: <name>` and the skill never loads. Both syntaxes fail. **User-typed `/slash`
invocation is unaffected**, which is exactly why it survives casual testing.

So it is **fatal for a model-invocable skill** (one you expect Claude to reach for on its own) and
**harmless on a `disable-model-invocation: true` skill** like `/distill`, which only ever fires when
the user types it.

**Tell:** the skill works perfectly when you type `/name` and does nothing when the model tries to
use it — so the bug looks like the model "choosing not to" rather than a config defect.

MEASURED 2026-07-31 by isolating the line in a throwaway skill and exercising both invocation paths.
