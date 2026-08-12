# feature-experiment

One loop for two kinds of question, run to a peer-reviewed verdict rather than a promising number.

| Track | Question shape | Noise unit |
|---|---|---|
| **TRAINING A/B** | "Would feature X help the model?" — something fits or trains as part of the experiment | Training seeds, in paired multi-seed arms |
| **MEASUREMENT STUDY** | "How good is X really? Can I trust Y for this decision? Is this threshold justified?" — measured on frozen artifacts, nothing trained | Sampling, bootstrapped over the data's natural cluster unit |

The spine is the same either way: audit → design → independent design review → frozen
pre-registration → build+smoke → run → one-read verdict → adversarial peer review → bounded
refine-and-re-run. Bars freeze before outcomes exist. A re-run needs a named instrument defect,
never a disliked outcome, and the whole program is capped at two re-runs.

## Why peer review is a phase, not a nicety

The skill's first validation run produced a clean-looking across-the-board null. An adversarial
audit overturned it — not because of a bug, but because the instrument was underpowered and not
production-faithful. The second run went further: it found nine mechanisms reporting green while
structurally incapable of failing, including the positive control for the very metric under study,
and a blocking gate that passed on the exact null it existed to reject.

Hence the skill's central claim: trust requires auditing the instrument, not just the numbers —
and auditing the audit, not just the instrument. The reviewers who attack the design are not the
reviewers who attack the results, and neither is the agent that built the runner.

## The one rule that pays for the rest

**Every guard is demonstrated in both directions before it is trusted.** It fires on a constructed
violation, and it stays quiet on known-good input, with the false-alarm rate measured. One
direction is not verification — a guard that is switched off entirely passes the quiet half, and a
guard that fires on everything passes the loud half. A guard that cannot be made to fire is a
blocking finding, not a passed test.

## What it protects that pre-registration alone does not

Pre-registration protects against outcome-driven choices; it does not protect the user's
*question*. A substitution can be fully pre-registered, fully auditable, and still answer
something other than what was asked. The skill carries the verbatim ask in an immutable block
through every document and agent brief, states the estimand next to it so any swap is visible in
the transcript, and requires re-ratification when a mid-chain decision rule narrows the question.

## Integration points

The skill names two contracts and deliberately not the tools behind them:

- **An experiment record** — something that can OPEN an entry when the pre-registration freezes,
  LOG arms as they complete, and CLOSE / ABANDON / CLAIM at the end. The point is that *starting*
  an experiment leaves a trace, so an abandoned program is visible. Any ledger that hashes the
  frozen contract will do.
- **A GPU arbiter** — only on the training track, and only if your GPU is shared between projects.
  Acquire a lease before training rather than racing for VRAM; the measurement track skips the GPU
  ceremony entirely and says so in its deviations.

Neither is required to use the skill; both are named so a project that has them knows where they
plug in.
