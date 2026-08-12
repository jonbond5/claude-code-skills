# Contributing

Issues and pull requests are welcome. One thing to know before you open a PR.

## This repo is generated

The plugin sources live in a private working tree and are exported here through a redaction
pipeline. **Edits made directly to files in this repository will be overwritten by the next
release.**

That is a real constraint and it is not your problem to work around — send the PR anyway. Changes
are applied upstream and land here on the next release, with attribution in the changelog. Nothing
gets lost; it just does not appear as your commit on this branch, because the branch is a build
output.

Files that are safe to expect round-tripping: anything under `plugins/`, `rules/`, `docs/`, plus the
top-level `README.md` and this file. Which is all of them — the whole tree is generated.

## What makes a change likely to land

The bar these skills are held to, in rough order of how often it comes up:

**A guard ships with a negative test.** If you add a check, a validation, a hook, or a gate, add a
test that constructs the violation and watches the guard refuse it — and another that confirms it
stays quiet on legitimate input that looks similar. One direction is not verification: a guard that
is always-on and a guard that works pass the same one-directional test.

**Assert on the effect, not on a source token.** A test that greps for a forbidden string is beaten
by rephrasing the violation. Drive the real path and assert on what it produces.

**Exit status is the gate.** If a check's result should stop something, wire it so it does —
`if check; then act; fi`, never a newline chain past it. And confirm the exit status actually tracks
the verdict: a checker that prints FAIL and exits 0 gates nothing while looking rigorous.

**Say what a missing input resolves to.** For any new input, state whether its default is an honest
neutral or indistinguishable from a real measurement. `0.0` for an unmeasured quantity is the second
kind, and it is a blocker.

## Running the tests

Most of what ships here is prose — skill and agent definitions that instruct an agent rather than
execute. There is no repo-wide suite to run, and `autobuild` in particular ships no executable code
at all: it once had a hook-based runtime with two conformance suites, and both were deleted when the
runtime was, because the runtime's own state file made two concurrent runs impossible.

So the bar depends on what you are changing:

- **Changing a script** (anything under a skill's `scripts/`): add the negative test described above
  and wire the exit status so it gates. A script that ships without one will be asked for one.
- **Changing prose**: the test is whether an agent following the words does the right thing. Say in
  the PR what you ran it against and what it did — a transcript excerpt is worth more than an
  assertion that it reads better.

If you are proposing that `autobuild` grow executable code again, expect that to be the main topic
of review rather than a detail: the release pipeline refuses to publish executable code in that
plugin unless a passing suite ships with it.

## Style

Match the surrounding prose. The skill files are written as instructions to an agent, in the
trigger → rule → tell shape: what situation fires this, what to do, and how you notice in flight
that it is going wrong. Keep the "tell" — it is the part that makes a rule usable rather than
merely true.

Claims carry their provenance. If a number or threshold is measured, say so and say how; if it is
reasoned, do not let it inherit the word "measured".

## Reporting a leak

If you find anything in this repository that looks like a private hostname, an internal path, a
credential, or a project name that should not be public: please open an issue without quoting the
value, or email the address on the owner's GitHub profile. The export pipeline has a leak gate, but
a gate only catches the categories someone thought to write down.
