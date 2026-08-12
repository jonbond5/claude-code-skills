# Installing

## As plugins (recommended)

```
/plugin marketplace add jonbond5/claude-code-skills
/plugin install autobuild
/plugin install session-lifecycle
/plugin install agent-waits
```

Install only what you want — the three plugins are independent.

Verify with `/plugin` (the plugin should be listed and enabled) and by typing `/sleep-gate` or
`/distill` and seeing the skill load rather than an opaque `Execute skill:` line.

## Manually

Clone, then copy the skill directories into your own skills folder:

```bash
git clone https://github.com/jonbond5/claude-code-skills.git
cd claude-code-skills

# autobuild is plugin-shaped; copy the whole tree
cp -r plugins/autobuild ~/.claude/skills/autobuild

# the other two are plain skill directories
cp -r plugins/session-lifecycle/skills/* ~/.claude/skills/
cp -r plugins/agent-waits/skills/*       ~/.claude/skills/
```

`autobuild` is prose and agent definitions — there are no hooks to register and no runtime to
install, so the manual copy is a complete install rather than a degraded one. The plugin route is
still easier to update.

Its subagents (`implementer`, `skeptic`, `done-judge` and the rest) live in `agents/`. If you copy
the tree manually, keep that directory: the recipes dispatch those agents by name, and a missing one
fails at the point of use rather than at install time.

## Installing the rules

`rules/` holds path-scoped rule files. Claude Code loads one automatically when it touches a file
matching the `paths:` glob in that file's frontmatter, so they cost nothing until they are relevant.

```bash
cp rules/*.md ~/.claude/rules/
```

Read them before adopting them. Each one encodes a specific incident on a specific stack, and a few
are strong claims that may not hold for you — `workflow-scripts.md` assumes a particular
dynamic-workflow runner shape, and `testing.md`'s traps are written around containerised pytest
suites. Take what applies.

`docs/working-rules.md` is the always-loaded working agreement these were factored out of. It is a
worked example rather than something to install wholesale; copying another person's operating rules
into your own `CLAUDE.md` unread is how that file becomes long enough to stop being read.

## Requirements

- Claude Code, on Linux or macOS
- `git`, with worktree support — `autobuild` isolates every implementer in its own worktree
- `python3` 3.11 or later, for the skills that ship scripts
- `bash`
- Docker, optional — only `docker-sweep` uses it

## Checking it works

`autobuild` ships no executable code, so there is no suite to run against it. Check the install the
way you would use it: ask for something small and watch where it goes.

```
Use the autobuild skill to add a --version flag to this CLI.
```

A healthy run announces the ask it anchored on, scouts the repo once, cuts the work into units, and
creates branches under `autobuild/<slug>/…` — one worktree per unit, under `.claude/worktrees/`. If
you see branches and worktrees appear, the plugin is installed and its agents resolved.

Two things are worth knowing before leaving one unattended:

- **Add `.claude/worktrees/` to your `.gitignore` first.** Agent worktrees are created inside the
  repository, so a later `git add -A` stages each one as an embedded gitlink — a commit that reads
  clean locally and is broken for everyone who clones it.
- **Running it headless** (`claude -p`) needs `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`. Print mode
  otherwise terminates a session after 600 seconds of waiting on background agents, and it exits
  **0 reporting success** — on a run that may have built only part of the ask and never reached its
  final judge.

## Uninstalling

```
/plugin uninstall autobuild
```

`autobuild` writes run state under `~/.claude/autobuild/`, `sleep-gate` under `~/.claude/sleep-gate/`,
and `close-session` under `~/.claude/session-closes/`. Uninstalling leaves those in place; remove
them by hand if you want the state gone.
