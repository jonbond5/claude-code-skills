# Reviewer prompt — one acceptance criterion

Prompt template for the per-criterion review stage of `implement-plan`. Fill every `<...>` slot and
pass the body to one general-purpose subagent per criterion. Launch all of them in parallel, in one
message. Each agent judges exactly one criterion — narrow briefs are what keep the verdicts sharp.

---

You are reviewing ONE acceptance criterion of a change that was just built. Judge only this
criterion. Do not review style, do not fix anything, do not widen into other criteria.

=== SCOPE CONTRACT — verbatim, never paraphrased ===
<the frozen Scope Contract>
=== END SCOPE CONTRACT ===

THE CRITERION:
<one acceptance criterion, verbatim>

THE DIFF: run `<diff command, e.g. git diff $(git merge-base HEAD <base>)...HEAD>` and read it.

How to judge:

- **Prefer running the thing over reading it.** If the criterion can be settled by a command, run
  the command and quote its real output. Reading code that appears correct is a weaker kind of
  evidence, and you must label it as such below.
- **Verify on the EXERCISED path, not in isolation.** A guard that holds in a unit test can be a
  no-op in the pipeline that calls it — check what actually runs end to end.
- **Check the missing-input case.** For any input the change introduces, determine what it resolves
  to when its source is missing, and whether that default is distinguishable from a real value. A
  default indistinguishable from a measurement is a finding, not a pass.
- `UNVERIFIABLE` is a real answer. A criterion you could not exercise is not a PASS.

Report exactly this, nothing else:

```
STATUS: PASS | FAIL | UNVERIFIABLE
EVIDENCE: <the command you ran and its actual output, or the file:line proving it — not a description>
EVIDENCE_KIND: MEASURED_OUTPUT | CITATION | CONFIG_ASSERTION
NOTES: <optional, one or two lines>
```

`EVIDENCE_KIND`, honestly:

- `MEASURED_OUTPUT` — you ran a command and are quoting its real output.
- `CITATION` — you are pointing at code that appears to do it, without having run it.
- `CONFIG_ASSERTION` — you are relying on a flag, a constant, a test's name, or a green suite.

Be honest here. A PASS classified as anything other than `MEASURED_OUTPUT` will be sent to a skeptic
whose job is to break it — misclassifying evidence does not make it stronger, it only delays the
refutation.
