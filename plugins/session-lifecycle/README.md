# session-lifecycle

Three skills for the end of a working session. None of them run automatically — that is deliberate.
A session-end pass that fires on its own gets ignored, and an ignored gate is worse than no gate,
because the transcript shows diligence that had no effect.

| Skill | Invoke | What it does |
|---|---|---|
| `distill` | `/distill` | Scans the current transcript for corrections, stated-rationale decisions, repeated workflows and self-critique. Routes each finding to the right durable surface — a path-scoped rule, the always-loaded working agreement, or memory — and enforces a hard budget on every always-loaded file so it cannot grow without something else shrinking. |
| `docker-sweep` | `/docker-sweep` | Finds Docker assets this session created and will never reuse: images orphaned by a retag, one-off benchmark images, stopped throwaway containers, BuildKit cache from a single build. Reports them with the exact narrow reclaim command. |
| `close-session` | `/close-session` | Discloses anything still running, writes the closing summary, and renames the session so the agent list shows the thread is finished. Reversible. |

All three are `disable-model-invocation: true` — they only fire when you type the command.

## Why `docker-sweep` reports instead of deleting

It runs against whatever Docker daemon you have, and on a developer machine that daemon is usually
shared with everything else you are working on. A pattern-matched `docker rm` reaches other
projects; named volumes hold live databases.

So the default is a report and a suggested command, and deletion needs an explicit opt-in for that
run. It will never run `docker system prune`, `docker image prune -a`, or `docker volume prune` —
each reaches every project on the daemon. Dangling-only and builder-cache pruning are safe and it
will offer those.

The rule it works to: **do not delete what you cannot prove is disposable.** The proof is a content
hash plus a diff against the canonical copy, timestamps for which is fresher, and a grep through
configs and scripts for anything still referencing it. Not provably redundant means keep and surface.

## Why `distill` runs inline

It reads the live transcript, which a subagent cannot see. Delegating it produces a confident summary
of nothing.

## The budget

`distill`'s job is as much deletion as capture. Every always-loaded surface has a line budget, and
adding to one requires removing from it. Without that, an instruction file grows until it stops being
read — which looks identical to not having written the rule at all.

Related, in [`../../rules/`](../../rules/): `skill-authoring.md` covers the frontmatter footgun that
silently breaks model invocation.
