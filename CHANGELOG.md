# Changelog

Versions follow the marketplace manifest. Each release records the private source commit it was
built from, so any published file can be traced back to the revision that produced it.

## 0.1.0 — 2026-08-12

First public release.

### Added
- **autobuild** — autonomous build pipeline: unit scoping, worktree-isolated implementers, standing
  verify lenses, one adversarial skeptic per acceptance criterion, and an independent judge that
  terminates the run against the original ask. Bundles `design` for turning a discussion into a
  build-ready handoff. Built from Claude Code's own primitives — subagents, worktree isolation, the
  task list and git — with no state file, no lock directory and no session hooks, so two runs in one
  repository cannot observe or block each other.
- **session-lifecycle** — `distill`, `docker-sweep`, `close-session`.
- **agent-waits** — `sleep-gate`, `constantly-monitor`.
- **rules/** — five path-scoped rule files loaded automatically on matching file types.
- **docs/working-rules.md** — the always-loaded working agreement the plugins were written against.

### Notes
- Numbered 0.1.0, not 1.0.0. An earlier `v1.0.0` tag existed locally and was never published
  anywhere; this is the first release to leave the repository, and 0.1.0 states its maturity
  honestly.
- `rules/` was cut back to the harness core before publication. Six stack-specific files
  (`python.md`, `database.md`, `ml-modeling.md`, `gpu-torch.md`, `frontend.md`,
  `docker-containers.md`) and three `testing.md` entries were removed as lore inherited from the
  private origin repo rather than anything about the Claude Code harness; two entries were kept by
  relocating them — the harness-timeout `docker exec` orphan into `testing.md`, and the
  fabricating-fallback-fixture rule into `writing-code.md`. Git history is the archive.
- `autobuild`'s two optional verify lenses come from `pr-review-toolkit@claude-plugins-official`.
  It runs without that plugin installed; those two lenses are skipped.
- Four planning skills that `autobuild` superseded (`feature-to-plan`, `harden-plan`,
  `implement-plan`, `project-to-plan`) are not published. Two of them covered plan-only work that
  `autobuild` deliberately does not do — attacking a plan without building it, and interactive
  whole-project requirements hardening. If that is what you want, `design` is the closest thing here.
