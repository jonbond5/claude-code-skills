---
paths:
  - "**/.gitignore"
  - "**/.gitattributes"
  - "**/*.sh"
  - "**/*.md"
---

# Staging hygiene

**Trigger:** editing a `.gitignore` — especially widening an allowlist in a deny-all file — and then
staging with a broad `git add -A`.

**Rule:** a broadened ignore rule newly admits files you have never looked at. **Read whatever it admits
before committing it.** List the new additions (`git status --short`) and open any you did not author.
The same applies to `git add -A` generally: stage explicit paths when the working tree contains anything
you did not put there.

**Tell:** the staged list contains a filename you cannot account for. *(Earned 2026-07-29: widening a
deny-all allowlist to track one design document swept two unrelated plan docs into the same commit,
unread. Separately, a `git add -A` committed three agent worktrees as embedded gitlinks — clean in
`git status`, broken for every clone.)*

## ⛔ NEVER `git add -A` IN A SCRIPT, AND NEVER IN SOMEONE ELSE'S WORKTREE

**Trigger:** writing automation — a cleanup, parking, or "preserve the work" script — that stages and
commits a tree you did not author. **This is why `*.sh` is in `paths:` above.**

**Rule:** `git add -A` stages whatever is there, including scratch data an agent mounted, virtualenvs,
caches, and multi-hundred-megabyte copies of a data directory. In a script you never see the staged
list before the commit lands, and a `push` in the same script puts it on the remote where history
cannot be rewritten without force. **Stage explicit paths, or `git status --short` and stop.**

**Recovering costs more than checking:** the remote branch must be deleted and the clean commit
re-pushed under a new name, because force-push is barred.

**Tell — and it is a nasty one: the blast radius shows up in someone else's report, not yours.**
*(2026-08-08: a parking script ran `git add -A` across a subagent's worktree to "preserve its work",
sweeping in a 553 MB scratch copy of `data/` — 396 files, 1.7 M insertions — and pushed it. The agent
later reported the commit as an unexplained intrusion into its branch and correctly declined to
attribute it. The real work was 8 files, 62 insertions.)*

**Deny-all is the right shape for a config directory** that also holds credentials, transcripts, and
caches: ignore everything, then allow-list the hand-authored files. It means a new release adding a state
directory cannot silently commit secrets — but it also means every allowlist widening is a review point.

## git's auto-merge reports SUCCESS while silently duplicating a restructured document

**Trigger:** merging a markdown file both sides reorganised — a shared backlog, a numbered findings
list, a handoff doc two sessions each renumbered.

**Rule:** git merges these line-wise, so when both sides insert differently-numbered copies of the
same sections it takes BOTH and prints *"Automatic merge went well."* **Count the structure after
every such merge** — section headings, item numbers, duplicates — and diff the result against each
parent. A clean merge message is not evidence about a file whose ordering changed on both sides.

**When an item's body must survive verbatim, prove it** by extracting the section from each parent and
comparing bytes, not by reading it. Check EVERY item, not the one you care about: a reviewed subset
validates items in a list, never the boundary around it.

**Tell:** the merge touched a file where both sides renumbered, and you accepted git's success message
without counting anything.

*(One such merge produced 27 sections where there should have been 22, items 16-20 present twice, and
reported success. Archive.)*
