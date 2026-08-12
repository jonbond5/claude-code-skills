---
name: feature-experiment
description: Run a pre-registered experiment to a peer-reviewed verdict. Two tracks. (A) TRAINING A/B — a feature/metric whose model value is unknown ("would X help the model?"): design, review, run, verdict. (B) MEASUREMENT STUDY — the true value or trustworthiness of something that already exists ("how good is X really?", "can I trust Y for this decision?", "is this threshold justified?"), measured on frozen artifacts with nothing trained. Both get independent design review, bars frozen before outcomes, and adversarial peer review of the instrument as well as the numbers. Use for "test this feature", "does feature X improve the model", "how much can I trust the model at Z", or auditing an inherited constant. Do NOT use for wiring an already-proven feature (normal implementation) or pure research with no verdict wanted.
---

# Feature Experiment — hypothesis → verified verdict

Runs one loop for two kinds of question: audit → design → independent design review → frozen
pre-registration → build+smoke → run → one-read verdict → **adversarial peer review** → bounded
refine-and-re-run. Pick the track in Phase 0; the spine never changes.

Validated twice on one project, and each run bought a different lesson. **2026-07-17** (a
candidate-feature slate, TRAINING A/B) earned the peer-review stage: the first run produced a
clean-looking across-the-board null that an adversarial audit overturned — no bugs, but the
instrument was underpowered and not production-faithful. **2026-07-18** (a per-tier trust table,
MEASUREMENT) earned the universal instrument rules: it found **nine** mechanisms reporting green
while structurally incapable of failing, including the positive control for the very metric under
study, and a blocking gate that passed on the exact null it existed to reject.

Trust requires auditing the instrument, not just the numbers — and auditing the AUDIT, not just
the instrument.

**Prime directives** (violating any of these invalidates the run):
- The user's ask is carried VERBATIM in an immutable block at the top of every document and agent
  brief. Reviewer concerns become gates inside the question, never the question.
- Bars freeze BEFORE outcomes exist, in `docs/experiments/<date-slug>/preregistration*.md`,
  committed. One read per registration. Deviations are NAMED.
- **Every guard is demonstrated in BOTH directions before it is trusted** — it FIRES on a
  constructed violation, AND it stays QUIET on known-good input, with a measured false-alarm rate.
  One direction is not verification. See "Universal instrument rules" below; this is the single
  highest-yield rule in the file.
- The verdict of record is the thing the question actually asks about, never a proxy for it.
  TRAINING A/B: an in-model A/B (or Stage-2 joint search), never a standalone correlation.
  MEASUREMENT: the measurement with its interval, and only once the instrument gates have passed.
- A re-run must be justified by a NAMED instrument defect — never by disliking the outcome. Each
  re-registration updates the sequential-testing ledger. Hard cap: 2 re-runs per program.

## Phase 0 — Intake + TRACK ROUTING

Capture: the verbatim ask; which models/segments are in scope; data-source appetite; how many
candidates. Check the do-not-retry ledger (memory + `docs/experiments/*/result_*.md`): a candidate
family with a prior NO-GO needs new evidence to re-enter. Check the sequential-testing ledger for
how many times the intended test origins have been read. AskUserQuestion only for genuine scope
choices; otherwise proceed.

**ESTIMAND — state it, then proceed.** Emit the two-line block so the substitution is visible in
the transcript, and carry on without waiting:

```
USER ASKED (verbatim):  <the ask, character-for-character>
WE WILL MEASURE:        <the specific estimand, in plain language — the exact quantity,
                         on which population, at which layer>
```

Pre-registration protects against outcome-driven choices; **it does NOT protect the user's
question.** A substitution can be fully pre-registered, fully auditable, and still answer a
different question than the one asked. Earned 2026-07-20: a user hypothesis about the DIRECTION of
an effect — *does a regime change whose incoming replacement leans a particular way benefit
segment S?* — reached a model A/B as a deliberately direction-AGNOSTIC change flag interacted with
a trend term. Every step was registered and reviewable. The user was never asked to ratify the
swap.
*(2026-08-02: the hard-STOP ratification gate was DELETED. It stranded unattended runs waiting for
approval nobody was present to give, and the record-opening tooling's copy of the same gate
already self-ratifies under a standing grant. The block stays; only the wait is gone.)*

**GATE 2 — RE-RATIFICATION ON NARROWING (MULTI-ARTIFACT CHAINS ONLY).** This gate fires only when
an experiment chain spans MORE THAN ONE artifact — a successor pre-registration, an addendum, a
follow-up experiment. Single-artifact experiments skip it. When a decision rule, an addendum
mapping row, or a reviewer blocker NARROWS or redirects the question mid-chain, return to the user
for approval BEFORE writing the successor artifact. **A correctly-fired pre-registered decision
rule is still a change to the user's question.** Earned 2026-07-20, same chain as Gate 1: an
addendum's decision row fired *"close the original thread; open a narrower successor thread"* —
correct by its own frozen rule, never ratified by the user, and it silently replaced the user's
estimand for everything downstream.

**Then classify the track by ONE question: does anything FIT or TRAIN as part of this experiment?**

- **YES → TRAINING A/B.** Noise unit = training seeds. Everything below applies as written.
- **NO → MEASUREMENT STUDY.** The study reads frozen artifacts (stored predictions, out-of-fold
  frames, logged outcomes) and characterises something that already exists. Noise unit = SAMPLING,
  over the data's natural cluster.

State the track in the pre-registration. The spine is identical — freeze bars, verify the
instrument, adversarial peer review, named deviations, ledgers. Only these four definitions swap:

| | TRAINING A/B | MEASUREMENT STUDY |
|---|---|---|
| **Power** | ≥5 paired seeds/arm; `DB = max(floor, 2×SD_pair/√n_seeds)` from control-vs-control seed noise | Bootstrap over the natural CLUSTER unit, not rows (rows inside a cluster are correlated; row-resampling gives a spuriously tight interval). State the unit and the realized resolution. |
| **Positive control** | A deliberately leaky candidate must fire at ≥3×DB | A SYNTHETIC INJECTED EFFECT must bend the measured curve in the injected direction, AND a zero-effect null must be REJECTED. Publish the detection floor per arm. |
| **Verdict of record** | In-model A/B; Stage-2 joint search before wiring | The measurement + its interval, valid only if the instrument gates passed |
| **Compute** | GPU lease from your project's GPU arbiter (if the GPU is shared), CUDA verified before and during | Usually CPU-only — say so explicitly rather than inheriting the GPU ceremony |

Requirements that are TRAINING-ONLY and must be named as deliberate deviations (never silently
omitted) on the measurement track: multi-seed paired arms, seed-noise dead-bands, the GPU lease,
the leaky-candidate control, and "isolated signal ≠ in-model lift". Force-fitting them is theatre;
dropping them without naming them is dishonest.

**GATE 3 — OPEN THE RECORD BEFORE YOU RUN ANYTHING (added 2026-07-29).** The moment the estimand
is ratified and the pre-registration is frozen on disk, create the experiment's entry in your
project's experiment record. **This happens BEFORE Phase 1, not at Phase 8.**

The row is what makes an abandoned experiment visible. Until this gate existed, nothing anywhere
recorded that an experiment had STARTED — the only in-progress state lived in a process-local dict
that a restart erased — so a program begun and quietly dropped left no trace, and the directories
under `docs/experiments/` existed only because somebody wrote a document afterwards. A record
created after the fact can only describe work that finished.

**This skill does not hand-write the record.** It owns the METHODOLOGY — estimand ratification,
bar freezing, instrument rules, peer review — and delegates the RECORDING to whatever
experiment-ledger tooling your project has. This is an integration point: the original used a
ledger CLI with five verbs; reproduce the *contract*, with whatever tool you have:

| when | record |
|---|---|
| estimand ratified + prereg frozen | OPEN the record — track, prereg path, estimand |
| each arm / seed / measurement completes | LOG its metrics, dead-band **and its derivation**, and the both-directions instrument check |
| Phase 5 verdict lands | CLOSE with the verdict and a one-line summary |
| the program is dropped before a verdict | ABANDON with what blocked it |
| Phase 8, per promoted finding | CLAIM with its evidence class: MEASURED \| OBSERVED \| REASONED |

The evidence — prereg, result docs, CSVs — still lives in the experiment directory exactly as
before. The record stores the pointer plus a hash of the frozen contract, so an edit to a frozen
bar after outcomes are known becomes detectable rather than silent. Nothing in the record
duplicates the prose; a copy free to disagree with the original is the failure mode being removed.

**Two refusals are worth building into the tooling, and neither should be worked around.** The
close step should refuse an assertive verdict when no run carries a complete instrument check —
close `UNVALIDATED` instead, which is an honest outcome and stays fully reachable. And it should
refuse to close at all if the frozen pre-registration no longer hashes to what was recorded;
restore it byte-for-byte or open a successor study.

## Universal instrument rules (BOTH tracks, EVERY phase)

Earned 2026-07-18 by a single measurement study that found **nine** mechanisms in one project
reporting green while being structurally incapable of failing. A guard's correctness is the one
property nothing else in a system exercises — everything else gets tested by being used. Apply
these to the experiment's own machinery, not only to the system under test.

1. **Both directions, always.** A guard must be watched FIRING on a constructed violation and
   staying QUIET on known-good input, with the false-alarm rate MEASURED. Quote both in the
   results. Failures that earned this: a "positive control" that compared a function call to
   itself, so it was `True` by construction on any input including a broken one — it had been
   green for months and the work it certified was never actually validated; a stratified
   informativeness gate that returned PASS on synthetic data engineered to carry ZERO signal, i.e.
   on the exact null it existed to reject; and firewall guards whose fixed thresholds false-fired
   on CORRECT input 14–87% of the time by segment (measured on one project), which would have
   driven an operator to re-roll the seed until it went quiet — choosing a seed inside the
   mechanism built to prevent choosing. Calibrate a statistical guard's bar against its own null
   at the realized sample size; never against a constant someone liked.
2. **A guard that cannot be made to fire is a BLOCKING finding**, not a passed test. If a
   perturbation can't turn it red, the perturbation may be measure-zero (flipping `<` to `<=` is
   undetectable on continuous data — plant exact-boundary cases) or the guard is inert.
3. **Inherited constants get forensics before they become load-bearing.** Read the calibration
   ARTIFACT, not the comment describing it. Earned: a canonical threshold used repo-wide turned
   out to be a fallback preset hardcoded before its calibration run; all three decision rules
   failed at every value tested; the code comment and a handoff both called it "calibrated." If
   you cannot find the derivation, the constant is a convention — say so in the prereg.
4. **Every number carries its BASIS; comparing across bases is a defect.** Earned three times in
   one study: raw vs conformally-shaped bands (would have calibrated detection floors for an
   instrument nobody uses), two different scoring conventions for the same quantity, and
   within-cluster exact enumeration vs across-cluster sampling (the study's numbers do NOT average
   to the published pooled figure). Label every table and say plainly which figures are not
   comparable.
5. **Grep WRITERS and READERS separately.** A value written, stamped available, and read by
   nothing is a bug, not dead code. No assertion on a producer's output can see this.
6. **Verify you are measuring CURRENT code and CURRENT artifacts.** Earned: an agent quoted
   constants five days stale from a committed file while the live DB held different ones; a
   sandbox served a DIFFERENT CHECKOUT on another branch with reload off, so a merged fix never
   reached it; and a test run reported "15 passed" against a copy baked into a container image
   because `tests/` wasn't bind-mounted. Check the mount, the branch, and the process, not the file
   on disk.
7. **Suspicious UNIFORMITY is an alarm, like suspicious accuracy.** If N supposedly independent
   measurements agree to three decimals, ask what they SHARE — it is usually one construction
   restated N times.
8. **GATE 3 — NULL PRE-FLIGHT (ALWAYS).** Before any feature or instrument ships, and before any
   verdict is written: enumerate EVERY new input and state what it resolves to when its sources are
   MISSING. Classify each default as **HONEST** (a real neutral, distinguishable from a
   measurement) or a **SILENT LIE** (a default indistinguishable from a measured value). Silent
   lies are blocking. Defaults that fire in PRODUCTION are reported as FINDINGS, never as normal
   operation — count them, name the affected rows, put them in the report. Earned in production: a live write
   path emitted rows with a key categorical input `None` and a related indicator defaulted to `0.0`
   for every row, pinning ~14 enabled features to zero. Nothing errored, nothing
   logged, nothing reported it. This is the SERVE-TIME TWIN of rule 5 (grep WRITERS and READERS
   separately): rule 5 catches a value nobody reads, this catches a reader silently substituting a
   value nobody wrote.

## The two-stage freeze (use whenever a threshold must be data-informed)

A bar set after seeing outcomes is not a bar. But some thresholds genuinely need data to set. Split
it, and enforce the split MECHANICALLY:

- **Stage A** computes ONLY design quantities — populations, counts, composition, cluster coverage.
  Never accuracy, concordance, or any outcome-ordering statistic. Enforce by DROPPING the outcome
  column at load, so a forbidden path dies with `KeyError` instead of quietly succeeding. Ship a
  negative test that watches it raise. Where a transform of the outcome must cross the firewall
  (e.g. an equality key for tie counting), prove the ORDERING cannot survive it, and calibrate that
  proof's guards per the both-directions rule.
- **Freeze** the threshold, record it, commit.
- **Stage B** reads outcomes.
- **Dispatch these as SEPARATE agent runs.** One agent that sees the census, sets the bars, and
  measures has effectively chosen its bars with the answer in view, whatever its instructions said.

## Phase 1 — Ground (parallel read-only agents)

Explore agents (parallel): (a) current feature inventory for the affected models + which raw
columns exist unused; (b) data availability for each candidate — verify source columns are
POPULATED (one project's feature registry had entries pointing at 100%-NULL columns), verify any
loader exists, verify serve-time availability (train/serve parity kills any feature not
reproducible at serve time — an entire candidate family has died here). External research agent
only if the idea needs grounding in what other projects do; availability claims get verified, not
assumed.

## Phase 2 — Design + independent design review (3-round bound)

An **architect agent** drafts the pre-registration; **independent reviewer agents** attack it;
architect revises; max 3 rounds, then freeze. Reviewers get the draft + the verbatim ask and must
check AT MINIMUM (each earned by a real failure). Items 3, 4, 6 and 7 are TRAINING-A/B forms —
on the measurement track substitute the Phase-0 table's equivalents and say so. Items 9–10 and the
universal instrument rules apply to BOTH tracks:

1. **Leakage paths** — every candidate strictly as-of; fit-on-all transforms identical across
   arms; split assertions present.
2. **Production fidelity** — estimator must load the SAME per-segment tuned params production
   training loads (one v1 slate silently tested default params: 13/33 cells measured a model that
   doesn't exist in production). Record resolved params per segment in outputs.
3. **Power** — paired multi-seed arms (≥5 seeds both arms, paired deltas); dead-band from measured
   control-vs-control seed noise on the AVERAGED statistic: `DB = max(floor, 2×SD_pair/√n_seeds)`;
   state the detection floor and expected false-positive count for the slate size. Single-seed
   treatments against a 2σ band have ~50% power AT the band — not acceptable.
4. **Positive control** — a deliberately leaky candidate (e.g. a column derived from the target
   period's own outcome), script-internal, run per segment. Must fire at ≥3×DB or that segment's
   verdicts are INCONCLUSIVE-INSTRUMENT. An instrument never shown to detect anything proves
   nothing.
5. **Metric fit** — a pairwise-concordance metric with a fixed ε is calibrated for one magnitude
   scale; low-magnitude subsets need rank-based metrics. A secondary error-improvement lane must
   exist so error-style wins are reportable (one v1 run discarded a −1.45% MAE win with no lane
   for it).
6. **Low-power honesty** — any segment whose realized DB exceeds a ceiling stated in the prereg
   reports non-earning cells as LOW-POWER, not NO-KEEP (on one project, one segment's seed noise
   measured ~3× the others').
7. **Adoption-path honesty** — a marginal single-column A/B is weaker than the production
   joint-search adoption path; pre-register the Stage-2 qualification rule (which results earn a
   joint auto-tune with the candidates in the pool).
8. **Sequential testing** — origins reuse counted and mitigations stated.
9. **Can every gate FIRE?** For each gate, construct the failure case and ask whether the stated
   test would detect it. Reviewers must hunt specifically for gates that are true by construction,
   tautological self-comparisons, and bars never checked against their own null. This check has
   caught a blocking defect in EVERY round it has been run.
10. **Selector semantics.** A selector (a threshold, a calibrated constant) cannot "return TRUE" —
   state its bar as "recovers a known correct value within a pre-stated tolerance," and check the
   prereg's tolerances are mutually satisfiable (two frozen numbers have contradicted each other).

Freeze + commit the pre-registration on an `experiment/*` branch off the development branch BEFORE
any fitting. Frozen means byte-untouched: later corrections go in `preregistration_v<N>.md` beside
it, with a SUPERSEDED banner on what they replace — never edited into the original.

## Phase 3 — Build + smoke (implementer agent)

Mirror the project's prior A/B runner and candidate-feature module if they exist; either way these
properties are load-bearing: in-memory candidate injection, feature registry untouched, nothing
written to production run-tracking, shared controls across arms, raw-deltas-only output (the
runner NEVER computes verdicts). Deterministic tests: as-of invariance (delete/alter target-period
data ⇒ identical values), hand-computed fixtures, missing-stays-NaN. Smoke run must show the
positive control firing before the full run is allowed. Container facts (when training runs in
one): check what the container actually mounts before assuming your docs directory is visible —
write to a mounted data path and copy host-side (container writes are root-owned; never let them
into git directly). Run per-directory tests only, never the full suite.

## Phase 4 — Execute (orchestrator, not an agent)

**MEASUREMENT TRACK: skip the GPU ceremony entirely** — no lease, no CUDA checks — and say so in
the prereg's deviations. Instead verify the container actually mounts what you think it does
(`docker inspect`), that the code under test is the code on disk, and that writes land only in a
gitignored, container-owned path. A root-running container's files inside the working tree BLOCK
later `git checkout`/`merge`.

TRAINING TRACK: if the GPU is shared between projects, acquire a lease from your project's GPU
arbiter first — never start/stop the GPU container directly. The lease contract worth having:
submit → lease → heartbeat honoring cancel-requested → done. GPU verified before AND during:
`nvidia-smi -L` + a fresh-exec torch CUDA check (a cached health endpoint lies after cgroup loss),
then a compute-apps check mid-run. From inside a training container, a host-side arbiter is
reachable at the Docker bridge gateway, not the compose service name. After the run: orphan
-process check.

## Phase 5 — One-read verdict

Mechanical read against the frozen bars; verdict doc in the experiment dir (verdict, realized
dead-bands, full cell table, skips, named deviations, ledger entry, reproduction command). Commit.

Run the Gate 3 null pre-flight before writing the verdict — a cell fed by a silent-lie default is
not a measurement.

**GATE 4 — EVIDENCE TAGS + RESULT BACKLINK (MULTI-ARTIFACT CHAINS ONLY).** Fires only when the
chain spans MORE THAN ONE artifact — a successor prereg, an addendum, a follow-up experiment, or
any handoff/memory write a later session will read. Single-artifact experiments skip it.

- **(a) Every claim leaving the experiment carries an evidence class: MEASURED / REASONED /
  OBSERVED.** Tag it in the report, the handoff, and the memory entry. **A reasoned inference must
  never inherit the word "measured."** Earned: *"8 of 12 candidate features did not earn tuner
  lift"* (OBSERVED) was written into project memory as *"the family is redundant with existing
  signal (measured)"* — and then relayed to the user as a measured precedent for a design
  decision.
- **(b) On verdict, REWRITE the pre-registration pointer** in every code comment, registry seed,
  handoff, and memory entry to point at the RESULT document (keep the prereg pointer alongside it).
  A pointer that still says "see the pre-registration" reads as "never ran." Earned: a registry
  seed comment naming only its prereg caused a later session to conclude the A/B had never run —
  it had run four days earlier and returned NO-KEEP.

## Phase 6 — PEER REVIEW (mandatory, regardless of outcome)

Independent reviewer agents — fresh context, NOT the design reviewers, NOT the implementer — get:
the prereg(s), the verdict doc, the raw results, and read access to the code. Two mandates:

- **Audit the experiment**: hunt false-null and false-positive mechanisms. Hypotheses to confirm
  or refute with file:line + empirical evidence: control leakage (subtle paths: fit-on-all
  transforms, calibration/eval overlap, seeds double-dipping); treatment columns actually consumed
  (join dtypes, NaN dominance, feature-weight/colsample/monotone misalignment); hastened runs
  (tree counts, params vs production); metric dilution (pair population vs production convention);
  power actually realized. **Re-run the gates' own negative controls rather than trusting the
  run's report of them** — a gate reported green may never have been capable of red. FORBIDDEN:
  fabricating problems. Every claim needs evidence.
- **Audit the results**: too-good = leakage alarm; too-uniform = tautology alarm; sign-skew across
  cells (many small positives under an underpowered gate); secondary-lane wins the primary gate
  had no lane for; verdicts stated beyond what cells support (unmeasurable ≠ null).

Each verdict cell gets classified: **CONFIRMED** (trustworthy as stated) or **UNCONFIRMED** with
the named defect. Cross-check reviewer citations against sources before acting (agents have
fabricated spec references here).

## Phase 7 — Refine + re-run (the 3-bound loop)

If any cells are UNCONFIRMED: reviewers + a fresh architect agent run up to **3 rounds** of
amendment-drafting ↔ critique to produce `preregistration_v<N>.md`: names every defect, states
what each fix changes and why it's a fidelity/power correction (not a re-roll), re-classes the
superseded verdicts (unmeasurable → INCONCLUSIVE, superseded → SUPERSEDED banner cross-linked,
never silently reversed), updates the ledger. Freeze + commit, then re-run ONLY the unconfirmed
scope (Phase 3 delta → 4 → 5), then Phase 6 again on the new results. Cap: 2 re-runs total; if
verdicts still can't be confirmed, report that honestly as the finding.

**Amendment legitimacy — state it explicitly, every time.** An amendment made while NO outcome has
been observed is a pre-outcome CORRECTION, not a re-roll, and does not spend the sequential-testing
budget. Record precisely what has and has not been seen at the moment of amending. This is what
lets a broken gate be replaced mid-experiment without laundering a result: on 2026-07-18 a blocking
gate was rewritten between Stage A and Stage B, legitimately, because only census quantities
existed. An amendment made AFTER outcomes are visible needs a NAMED instrument defect and costs a
ledger entry.

Stage-2 (joint search) runs when the frozen qualification rule fires, with the production
auto-tune guardrails intact; only Stage-2 evidence can justify wiring. MEASUREMENT track has no
Stage-2 — its adoption path is a RECOMMENDATION with evidence, and **wiring is a separate change
gated on its own evidence, not on a signature**: a measurement result never justifies wiring by
itself; an in-model A/B (or Stage-2) does. Where that evidence already exists, wire it registered
**DISABLED**, log it through the config audit trail, and disclose it in the report. Where it does
not, the recommendation IS the deliverable and the A/B is the next experiment.
*(2026-07-31: this read "wiring is a separate, user-approved change". No incident was ever recorded
for that gate, it sat beside a Phase 8 step that merges autonomously, and the real protections —
DISABLED-on-registration plus the audit trigger — are mechanical, not procedural.)*

## Phase 8 — Report + memory

User-facing report: impact-led, plain language, NO code identifiers, layman stats with small worked
examples, effect sizes not just verdicts, confidence labels from peer review, what's deferred vs
rejected and why. Update memory: program status, durable measurement facts (e.g. per-segment seed
noise), do-not-retry entries, ledger state. **Every memory write carries its Gate 4a evidence tag —
MEASURED / REASONED / OBSERVED — inline with the claim.** Memory is where an OBSERVED claim
silently promotes itself to MEASURED and comes back years later as precedent. Apply Gate 4b at the
same time: any pointer written here names the RESULT doc, not just the prereg. Merge the
experiment branch per the project's git policy once per-directory gates pass.

**Close the record here, and promote each finding as a claim** — close with the verdict and one
line, then one claim entry per promoted finding carrying the same evidence tag. A verdict that
lives only in prose is one nothing can aggregate: when one project backfilled its record
(2026-07-29), 28 of 35 historical evidence directories contained a verdict *sentence* and only 2
held a token any machine could classify. That is what the claims register fixes going forward.

**Do NOT copy claim identifiers into memory.** The record is solely authoritative; memory stays
prose. There is no memory↔record sync to maintain — a memory line is checked by reading the
record, never by matching identifiers.
