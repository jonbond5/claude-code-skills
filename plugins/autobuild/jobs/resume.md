# Job: resume an interrupted run

A run outlives a session. Context gets compacted, a session dies, the user walks away and comes back.
**Git is what survives** — recover from it, never from memory.

## 1. Find the run

Two places, in this order:

```
git -C <repo> branch --list 'autobuild/*'
git -C <repo> worktree list
ls -t ~/.claude/autobuild/*.md
```

The branch namespace is authoritative: `autobuild/<slug>/<unit-id>` tells you the slug, the units
that got as far as a branch, and nothing that was merely intended. The run note
`~/.claude/autobuild/<slug>.md` tells you what was *decided*, including the verbatim ask.

**If there are branches under several slugs, they are several runs — possibly several sessions'.**
Do not merge them into one resumed run. Pick the one the user means (ask, if they are present; take
the most recent otherwise), and say in your report which others you found and left alone.

If there is no note and no branch, there is nothing to resume. Say so and stop — do not start a fresh
run on the assumption that one was meant to exist.

## 2. Recover the ask, not your memory of it

The run note's `## The ask — verbatim, immutable` block is authoritative. **Do not restate, refine, or
"clarify" it.** The whole point of the immutable root is that a resumed session works the original
question rather than a summary of a summary of it.

If the note is missing or its ask block is gone, the ask is **unrecoverable** — say that plainly and
ask the user for it verbatim. Do not reconstruct it from commit messages; a reconstructed ask is a
different ask wearing the same clothes, and the judge will verdict against it for the rest of the
run.

Read `## Decisions` for what was already settled — expansions, backlogged items, parked items,
permission denials. That is the record; your recollection is not.

## 3. Reconcile against reality

The note says what was *intended*. Git says what is *true*.

**Dispatch `recon` (sonnet)** with the run note path and the repo path. It reads the note against
`git log`, `git branch`, `git worktree list` and `git status`, and returns the delta — units the note
calls done whose commits do not exist, commits the note does not account for, orphaned worktrees,
parks and denials, and the current tree state. It is read-only and decides nothing.

That is bulk reading with a fixed output shape, which is why it is delegated; **the decisions that
follow are not.** Read its `conflicts` list yourself and spot-check any line you are about to act on.
The task list stays yours — recon does not touch it.

**Where the note and the repository disagree, the repository wins.** Rebuild the task list to match
what git actually contains.

## 4. Re-judge before continuing

Do not trust the last recorded judge verdict. Run `done-judge` against the root ask and the current
state of the code. A verdict from before an interruption describes a tree that may no longer exist —
another session may have committed, merged, or reverted since.

## 5. Continue

Resume at step 4 of `build-feature.md` with whatever units remain. Re-derive the base SHA from the
run note, not from `HEAD`.

## Abandoning a run instead

There is nothing to shut down — no state to clear, no hook to disarm, no lock to release. A run that
is not being worked simply stops being worked.

Report what was left unfinished and **name every branch and worktree that still exists**. Leave them
in place: they hold the only copy of that work, and deleting them is the user's call, not yours.
