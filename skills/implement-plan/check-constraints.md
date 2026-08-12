# Constraints reviewer prompt — the whole diff

Prompt template for the constraints stage of `implement-plan`. One general-purpose subagent, run
after the per-criterion reviews. It answers a different question from the criterion reviewers: not
"does the change work" but "did the change stay inside its contract".

---

You are auditing a just-built change for scope and constraint adherence. You are not judging whether
it works — other reviewers own that. Do not fix anything.

=== SCOPE CONTRACT — verbatim, never paraphrased ===
<the frozen Scope Contract>
=== END SCOPE CONTRACT ===

CHANGES LIST (the files the plan authorized):
<the plan's CHANGES list>

THE DIFF: run `<diff command, e.g. git diff $(git merge-base HEAD <base>)...HEAD>` and read all of it.

Check:

1. **Every binding constraint** in the Scope Contract against the whole diff. For each violation,
   name the constraint, how the diff violates it, and the evidence (file:line or command output).
2. **Every file the diff touches** against the CHANGES list. A file modified outside the list is a
   finding even when the modification looks harmless — adjacent improvements were explicitly out of
   scope.
3. **Anything else worth saying** goes into at most 3 advisory observations. Advisory means it does
   not block; pick the 3 that matter and drop the rest rather than padding the list.

Report exactly this, nothing else:

```
VIOLATIONS:
- constraint: <which> | how: <what the diff does> | evidence: <file:line or output>
(or "none")

OUT_OF_SCOPE_FILES:
- <path> — <one line on what changed>
(or "none")

OBSERVATIONS (max 3):
- <advisory note>
```
