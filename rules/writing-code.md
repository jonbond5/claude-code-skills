---
paths:
  - "**/*.py"
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
  - "**/*.go"
  - "**/*.rs"
  - "**/*.java"
  - "**/*.rb"
  - "**/*.sql"
  - "**/*.ipynb"
---

# Writing code — always-on hygiene, relocated from CLAUDE.md

These three were situational-looking but their trigger is **editing source**, so they load here instead of
in every session. Narratives: a separate incident log.

## A value WRITTEN at one line and READ at zero is invisible to every test you'd write
**Grep in THREE steps: who WRITES it, who READS it, and WHO CALLS THE READER** — transitively out to a
call site on the real execution path. Step 3 is the one that gets skipped, and skipping it is how the
*fix* becomes decorative: adding a `get()` beside a `register()` makes the readers grep come back
non-empty while nothing executes. Then write a **provenance test**: take a stored user-facing row and
prove which code produced it, end to end. A second implementation of the same idea feeding nothing gets
**deleted**.

**Tell:** the producer is correct, its tests pass, the value lands on disk, the flag says it's there — and
**nobody calls it.** A conformal correction shipped in all nine artifacts, stamped available, read by
nothing; a stated "80% confidence range" held as little as 65%, for months.

**Violated twice in one session (2026-07-29):** one commit deleted an unread flag; the **next** added an
unread constant read only by a test asserting its literal value. **A convergence step that adds no import
edge outside the convergence file converged nothing.**

**Why this matters — A GUARD IS THE WORST INSTANCE, and I shipped one (2026-08-05).** Ordinary unread
code has a happy path that might expose it. **A guard has no happy-path symptom at all**: unwired, it
is indistinguishable from a guard that simply never had to fire, so nothing will ever surface it.
That session diagnosed a defect where three models passed their gate and could not serve, fixed the
cause, wrote an activation-time servability check — and never called it. `grep` returned the
definition plus two *comments*. Its companion opt-in flag had zero callers too, so the default left
the old behaviour live. **Three defences against one failure, all inert, all "done".**
**Tell:** you finished a guard and the only thing that changed in the diff was the file defining it.
**Rule: a guard is not shipped until you have watched it FIRE from the real entry point** — which is
step 3 of the grep, enforced by [[the never-watched-fire rule]] in the always-on working agreement
(`docs/working-rules.md` in this repo, `~/.claude/CLAUDE.md` once installed).

## The LLM interprets; it must not COMPUTE numbers that matter
Money, stats, metrics: do arithmetic in deterministic code, never via the model.

For a new mathematical function, **derive the expected values INDEPENDENTLY of the implementation** — by
hand, from the published definition, or with a second tool — and use those as the test fixture. Never let
the implementation generate its own expected output; that is a tautology dressed as a test.

**Surface the check, do not block on it.** Put a runnable command plus a 3–5 row worked sample, with the
outputs printed in plain numbers, in the same report; write the test immediately, marked as awaiting the
user's number-check; keep a ledger of what is unverified so they can audit at leisure. A disputed value is
fixed by editing the fixture.

*(SOFTENED 2026-07-31 — this rule previously said "**wait for the user to verify**" before writing the
test. Measured in one repo: 16 new mathematical modules landed in a single month with zero verified
fixtures ever recorded, so the gate delivered no verification while blocking every autonomous run. It also
contradicted this config's own autonomy rules. The honesty half — independent derivation, no
self-generated fixtures — is the part that was doing the work, and it is strengthened above.)*

---

## Safety & shared state

## Mirror existing patterns before introducing new ones
On any "add X" task, scan for analogous patterns (error handling, logging, test structure, route
organization) and mirror the convention. If nothing analogous exists, **choose the pattern, write it, and
name the choice and its rationale in one line of your report** — do not stop for approval.

*(Approval clause CUT 2026-07-31 — no incident was ever recorded for it in the archive, unlike every
neighbouring rule, and a new pattern on a feature branch is diff-visible and one-command reversible. The
merge decision already stays with the user.)*

## A work-queue predicate SATISFIED BY ITS OWN SUCCESS never terminates

**Trigger:** writing the selector for a recovery job, backfill, retry sweep, or any loop of the shape
*"find the broken rows, fix them, repeat until none remain."*

**Rule:** state what a row looks like AFTER you fix it, then check the predicate against that. If a
repaired row still matches, the population refills as fast as it drains and the loop is infinite. The
fix is a monotonic discriminator the repair necessarily moves — a timestamp cutoff, a version stamp, a
processed-marker — never a field the repair leaves unchanged.

**Both failure directions are real, and the second is worse:**
- *Refills* — the loop never exits and burns compute re-doing finished work.
- *Empties early* — the predicate stops matching rows you have merely CLAIMED but not processed. A
  claim step that mutates state (`status='pending' -> 'running'`) moves rows OUT of the population, so
  a termination check reading the population sees zero while the queue is full.

**Never test a pre-mutation read against a post-mutation count.** Re-read, or update the local
variable, after anything that moves rows in or out of scope.

**Tells:** the topped-up/claimed counter exceeds the population size; or the loop reports "drained"
in the same breath as claiming a batch. Assert on *items remaining* — including claimed-but-unfinished
— never on the exit code, which is 0 for both shapes.

*(Both hit one recovery run: a podcast predicate keyed on `status='extracted' AND payload IS NOT NULL`
— exactly what success looks like — burned ~11h re-extracting completed work; and its termination
check compared a pre-top-up queue count against a post-top-up population count and exited 0 leaving
479 documents queued. Archive.)*

## A fallback fixture gated on "empty" instead of "fetch failed" fabricates data on the happy path

**Trigger:** any consumer keeping a mock/sample fixture as a graceful fallback for a failed fetch.

**Rule:** gate the fallback on **the failure itself** (`!resp || resp.ok !== true`, or a caught
exception) — never on the payload being empty. `if (!data || !data.length) return FIXTURE` conflates
*the fetch failed* with *the fetch succeeded and there is genuinely nothing*. **Empty-but-successful
is a first-class state deserving its own visible, labeled rendering.** When auditing, enumerate every
fixture const and classify each reference as dead / failure-only / live-path — the live-path ones are
bugs.

**Tell — wired ≠ live.** Verify a fetch exists, that the endpoint returns rows for real inputs, and
that the render path uses them. Observed live: a strip labeled "LIVE" scrolling five fabricated
status alerts because its endpoint honestly returned zero rows (a blank panel would have been
*better* — it would have been honest); a surface captioned with a live source containing **no fetch
at all**; and a panel wired to a real endpoint returning empty for *every* input due to a key-format
mismatch.
