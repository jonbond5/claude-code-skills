---
paths:
  - "**/workflows/*.mjs"
  - "**/workflows/*.js"
  - "**/.claude/workflows/**"
---

# Editing a dynamic-workflow script

Each entry is **trigger → rule → tell**. Narratives: a separate incident log.
These were all earned on 2026-07-29 building `review-loop.mjs` and `implement-verify.mjs`.

## A bare `node --check` FALSE-FAILS on a workflow script

**Trigger:** validating a workflow script's syntax before or after editing it.

**Rule:** the harness wraps the script body in an async function, so **top-level `return` and top-level
`await` are legal there and illegal in a bare ESM module.** `node --check script.mjs` reports
`SyntaxError: Illegal return statement` on a perfectly valid script. Check it in the **harness shape**:
strip `export` from the `meta` declaration, wrap the remainder in `(async () => { … })()`, then check
that. If your host has no `node` on PATH, `node:20-alpine` runs it in a container.

**Tell:** the reported error points at a `return` that has always been there and that you did not touch.
**A runner that manufactures a false failure is the instrument, not your change** — see
`~/.claude/rules/testing.md`.

## Backticks inside a template literal terminate it

**Trigger:** writing prose into an agent prompt inside a workflow script — the prompts are template
literals, and technical prose wants markdown backticks.

**Rule:** never put a backtick in prompt text. Use plain words or single quotes. Grep for an **odd**
backtick count per file as a cheap smoke test.

**Tell:** `SyntaxError: missing ) after argument list` pointing at a line far below your edit — the
string closed early and everything after it parsed as code.

## `args` may arrive as an object OR a JSON string

**Trigger:** reading `args` fields at the top of a script.

**Rule:** parse defensively — if `typeof args === 'string'`, `JSON.parse` it before field access. A
stringified payload otherwise dies at the first required-field check with a message blaming a field the
caller *did* supply. Make the error name the received keys and `typeof args`.

**Tell:** the workflow fails at agent 0 with "X is required" on a call whose args plainly contain X.

## `Date.now()`, `Math.random()`, and argless `new Date()` throw

They would break resume. Pass timestamps in via `args`; vary agent prompts by index rather than
randomly. Stamp results after the workflow returns.

## The script has no filesystem access — agents do

The script cannot read or write files. Return the artifact and let the **caller** write it, or have an
agent write it. Do not design a script around persisting its own output.

## Count EVERY agent in the projection, and log what you drop

**Trigger:** logging a projected agent count, or capping a fan-out.

**Rule:** the projection is an honest ceiling only if it includes every stage — probe agents, verify
agents, the final synthesis. Anything a cap excludes gets `log()`-ed as dropped, and **anything that
skipped verification is returned in its own field, never merged with the verified set.**

**Tell:** a projection of "up to 5 agents" beside a run that used 7; or a `surviving` list whose members
were never actually checked. *(Both happened; the second put 9 unchecked findings where a reader would
assume they had been vetted.)*

## Batch trivially-parallel agents into one

**Trigger:** fanning out N agents that each run one cheap command.

**Rule:** an agent pays ~38k tokens of fixed context setup before it does anything. Three probe agents
running one SQL query each cost 114k — 34% of a run — to do about a minute of work. Batch them into one
agent unless each genuinely needs a clean context or the latency matters. **The trade is real in both
directions:** batching cut probe tokens 66% and raised wall-clock ~9%, because three parallel agents
became one serial one.

## Model selection is the workflow's judgment call — no global default
Trust each stage to get the model and effort it needs. Omit `model` to inherit unless a stage warrants a
different tier; use `effort` too — `low` for mechanical stages, `high`/`xhigh` for verify and judge
stages. There is **no** "always use model X" rule. *(A prior blanket Sonnet-only rule was deprecated
2026-07-29; see the archive before reinstating it.)*

**Mechanical fact:** a subagent killed by a model limit does **not** resume on a different model —
`SendMessage` reuses the dead one. Relaunch with a fresh `Agent` call carrying an explicit `model:`.

## No silent caps; budget, don't ration

**No silent caps.** If a fan-out bounds coverage — top-N, sampling, no-retry — `log()` what was dropped.
Silent truncation reads as "covered everything" when it didn't. **Budget, don't ration:** rate limits are
real, and the countermeasure is budget-aware termination inside the script, not pre-emptively shrinking
the work.

## A serial phase loop MUST gate on each phase's outcome

**Trigger:** a `for` loop in a workflow script that runs phases in sequence, each depending on the last.

**Rule:** inspect every phase result before starting the next — `agent()` returns **null** when the
agent dies, and a phase that reports failures still returns a string. Halt or retry once, and `log()`
the decision. Also capture a **same-session baseline** before phase 1 and compare **identity sets**
(which test names failed), never counts — counts rot within hours.

**Tell:** the run reports success and the failure is only visible in a final gate, or in a phase report
nobody read. *(Earned 2026-07-30: a 15-agent build shipped 8 serial phases with no gate. It passed only
because every phase happened to succeed.)*

## Never let the agent that GATES a harness also REPAIR it

**Trigger:** a workflow stage allowed to fix the tests or checks it is simultaneously validating.

**Rule:** split the roles. A repair stage may edit; a gate stage may only judge and must not write.
Otherwise nothing verifies that the repaired artifact still encodes the acceptance criteria — **a gate
that can edit what it gates is a guard grading itself**, the failure class this project has already
catalogued elsewhere.

## Re-assert an earlier phase's guarantee after any phase that could erode it

**Trigger:** a later phase adds code, stubs or fixtures under a harness whose value is a *property*
(e.g. "every red fails on an assertion, never an import error").

**Rule:** the property is established once and silently degradable thereafter. Re-check it after every
phase that adds a module. *(Earned 2026-07-30: Phase 1's `NotImplementedError` stubs converted 11 of
Phase 0's clean assertion-failures into raised exceptions — exactly as the plan instructed — and nothing
re-verified the property. The implementer disclosed it unprompted; nothing in the workflow would have.)*

## Give every writing agent an explicit staging rule

**Trigger:** any workflow whose agents commit, in a repo other sessions also work in.

**Rule:** state verbatim — *never `git add -A` or `git add .`; stage only the exact paths you created or
edited, by name; never switch branches.* Observed: 15 concurrent agents, zero scope violations in a tree
carrying another session's uncommitted work. **Causally untested** — no arm ran without the rule — but
it is cheap and the failure it prevents is expensive.
