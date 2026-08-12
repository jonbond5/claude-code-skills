# Skeptic prompt — refute one claimed PASS

Prompt template for the refutation stage of `implement-plan`. Send one fresh general-purpose
subagent per claimed PASS whose evidence kind is not `MEASURED_OUTPUT` — or that claims
`MEASURED_OUTPUT` while quoting no command and no output. Launch the skeptics in parallel, in one
message. Never reuse the reviewer that produced the claim: the point is an agent with no stake in
the verdict.

---

A reviewer claims the acceptance criterion below PASSES. Your job is to BREAK that claim. You are
not confirming it — you succeed by refuting it, and you treat the claimed evidence as unsubstantiated
until you have reproduced it yourself.

=== SCOPE CONTRACT — verbatim, never paraphrased ===
<the frozen Scope Contract>
=== END SCOPE CONTRACT ===

THE CRITERION:
<the acceptance criterion, verbatim>

THE CLAIMED EVIDENCE (from the reviewer, verbatim):
<the reviewer's STATUS / EVIDENCE / EVIDENCE_KIND block>

Do all of these:

1. **Check the evidence exists.** Open every cited file:line and confirm it says what the reviewer
   says it says. Reviewers in loops like this have cited references and spec items that do not
   exist — a citation is a claim, not a fact.
2. **Re-derive the verdict by RUNNING something.** A flag, a constant, or a test's name is not the
   behavior it advertises. Drive the real path and look at what it produces.
3. **Probe the edges.** Boundary values, the empty case, and what every new input resolves to when
   its source is missing. A default that is indistinguishable from a real value refutes a pass that
   depended on it.
4. **Check the exercised path.** A guard correct in isolation can be a no-op in the pipeline that
   calls it. If the criterion was verified only in isolation, verify it where it actually runs.

Report exactly this, nothing else:

```
REFUTED: yes | no
REASON: <one or two sentences>
EVIDENCE: <the command you ran and its actual output>
```

**Default to `REFUTED: yes` when you cannot substantiate the claimed evidence.** A pass whose
evidence cannot be reproduced is not a pass — "I could not confirm it" is a refutation, not an
abstention.
