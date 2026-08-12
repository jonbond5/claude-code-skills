# claude-code-skills

_Note_: **This repo is human-designed, 100% AI developed**. 
For my thoughts on the methodology and why this project matters, please review the Github page associated with this repo. This repo will be actively maintained (sentiment CAO August 2026).

Three Claude Code plugins built around one idea: **an agent that checks its own work has to be
able to watch the check fail.**

Every guard in here ships with a negative test. Every gate is wired so its exit status is what the
next step depends on — not a line of output somebody reads. That constraint shaped all three
plugins, and it is most of what makes them different from a prompt in a markdown file.

| Plugin | What it does |
|---|---|
| **[autobuild](plugins/autobuild/)** | Takes a feature ask and drives it to committed, verified code without intermediate approvals. Scopes the work into units, builds each in an isolated git worktree, runs standing verify lenses, and stops only when an independent judge says the *original* ask is satisfied. Includes `design`, which hardens a discussion into a build-ready handoff. |
| **[session-lifecycle](plugins/session-lifecycle/)** | Closing a session properly: capture what was learned (`distill`), reclaim what was created (`docker-sweep`), and file the thread as finished (`close-session`). |
| **[agent-waits](plugins/agent-waits/)** | Making an agent wait without burning tokens. `sleep-gate` bridges a bounded wait such as a rate-limit window; `constantly-monitor` sets up a recurring, self-healing wake loop that survives the window it is waiting out. |

Also here: **[`rules/`](rules/)** — five path-scoped rule files that load automatically when Claude
touches a matching file (skill authoring, workflow scripts, git staging, writing code, testing), and
**[`docs/working-rules.md`](docs/working-rules.md)**, the always-loaded working agreement the plugins
were written against.

## Install

```bash
/plugin marketplace add jonbond5/claude-code-skills
/plugin install autobuild
```

Full instructions, including the manual copy route and how to install `rules/`, are in
[docs/installing.md](docs/installing.md).

## The idea, in one example

When an `autobuild` implementer reports that an acceptance criterion passes, that claim is not taken
at face value. Each criterion gets its own skeptic whose job is to **make it fail** on the real code,
and the verdict it returns has three values, not two: `refuted` (it ran something and the criterion
broke), `stands` (it attacked properly and could not break it), or `unverifiable` (it could not check
at all).

The third value is the point. A criterion nobody could check is not a pass, and collapsing it into
one would turn the whole verify phase into a rubber stamp. `unverifiable` reaches the judge
explicitly labelled unverified; `refuted` goes back to the implementer as work, with the evidence
attached, rather than being written down as a finding and forgotten.

The same discipline shapes the concurrency design. `autobuild` is built from Claude Code's own
primitives — subagents, worktree isolation, the task list, git — and deliberately ships no state
file, no lock directory and no session hooks, because an earlier version that had them refused to
start a second run in the same project and blocked unrelated sessions from ending a turn. Units are
cut so they share no files; that disjointness *is* the concurrency control, and there is nothing left
to lock.

The same discipline runs through the rest. `docker-sweep` reports by default and deletes only on an
explicit opt-in, because it runs against a shared daemon where a pattern-matched `docker rm` can take
out another project's database. `sleep-gate` writes a durable breadcrumb before it sleeps, because
the whole point is surviving a context the agent will not remember.

## What these assume

Written for Claude Code on Linux with `git`, `python3` (3.11+) and `bash`. `autobuild` additionally
needs `git worktree` support — that is what isolates each implementer, so it is a hard requirement
rather than a nicety. Nothing here calls a paid API beyond Claude Code itself.

`autobuild` uses two agents from `pr-review-toolkit@claude-plugins-official` as standing verify
lenses. It runs without them; you lose those two lenses.

## Status and honesty about it

These came out of one person's daily use, not a product plan. Consequences worth knowing:

- **Opinionated by design.** `autobuild` deliberately does not stop for approval mid-run. If you want
  a plan to review before code is written, use `design` first and read its handoff.
- **The rules encode specific incidents.** Each entry in `rules/` and `docs/working-rules.md` exists
  because something broke. They read as strong claims because they were expensive. Yours will differ;
  fork them.
- **`autobuild`'s container test needs Docker** and exits 77 when it cannot run — never a pass.

Issues and PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT. See [LICENSE](LICENSE).
