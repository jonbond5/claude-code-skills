# agent-waits

Two ways to make an agent wait. They differ in what happens when the wait itself fails, which turns
out to be the only question that matters.

| Skill | Invoke | Use when |
|---|---|---|
| `sleep-gate` | `/sleep-gate <duration>` | **One bounded wait.** A rate-limit window, a long external job. Captures durable resume state, runs a pre-sleep checklist, sleeps in the background, resumes from a breadcrumb file. |
| `constantly-monitor` | `/constantly-monitor` | **A repeating check on a fixed cadence.** Poll a log, watch a job, babysit a process. Driven by a recurring cron job. |

## The failure mode that separates them

A chained sleep — sleep, wake, check, sleep again — dies silently if any single wake lands inside a
rate-limit window. The turn is refused, the chain is never re-armed, and the loop stops. Nothing
reports it. You come back hours later to an agent that quietly stopped watching.

`constantly-monitor` uses cron instead, so each fire is independent of the last. A wake lost to a
quota window is simply picked up by the next one. That is the whole reason it exists as a separate
skill rather than a loop inside `sleep-gate`.

The cost is honest and worth stating: reaction latency is bounded by your rate-limit window. A fire
has been observed landing about 2.5 hours late on a busy account. If you need to wake the *instant*
something happens, neither of these is the right tool — watch the event directly.

Cron is minute-granular, so sub-minute cadence is out.

## The breadcrumb

`sleep-gate` writes resume state to disk *before* sleeping, not after waking. The agent that wakes up
may not be the one that went to sleep — context can be summarised across the gap — so anything not
written down is gone. The breadcrumb carries the task, the branch and HEAD at sleep time, and what
was in flight.

On wake it re-checks branch and HEAD and reports drift, because a shared checkout can have moved
underneath it while it slept.

## Pre-sleep checks

`sleep-gate` refuses to sleep with harness-tracked background work in flight — you would lose the
completion notification. It also surfaces uncommitted changes and any existing `sleep` processes
before it commits to the wait.
