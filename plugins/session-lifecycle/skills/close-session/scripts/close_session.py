#!/usr/bin/env python3
"""Mark the current Claude Code session closed and rename it CLOSED_*.

The session name lives in up to two places, and both are read-modify-written by
the live session process:

  ~/.claude/jobs/<jobId>/state.json     name + nameSource   (background sessions)
  ~/.claude/sessions/<pid>.json         name                (any session with a
                                                             registry entry)

MEASURED 2026-08-01 on a live, busy background session: an atomic write to both
files renamed the session, `claude agents --json` reflected it immediately, and
the name SURVIVED two subsequent rewrites of state.json by the session process
(updatedAt advanced twice, name held). The process merges rather than
overwriting from memory, so an external rename sticks.

`nameSource` is set to "user" on close. Every session you have renamed by
hand carries that value, and auto-naming only targets nameSource=auto — so
pinning it is what stops the harness renaming a closed session back.

Exit codes:  0 closed   2 already closed (no-op)   3 nothing renamed / unverified
             4 usage error
A non-zero exit means the session is NOT closed. Never report otherwise.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
CLOSE_DIR = os.path.join(HOME, ".claude", "session-closes")
PREFIX = "CLOSED_"
OPEN_PREFIX = "OPEN_"


# --- surfaces ---------------------------------------------------------------

def job_state_path():
    d = os.environ.get("CLAUDE_JOB_DIR")
    if not d:
        return None
    p = os.path.join(d, "state.json")
    return p if os.path.exists(p) else None


def session_reg_path():
    pid = os.environ.get("CLAUDE_PID")
    if not pid:
        return None
    p = os.path.join(HOME, ".claude", "sessions", f"{pid}.json")
    return p if os.path.exists(p) else None


def session_id():
    return os.environ.get("CLAUDE_CODE_SESSION_ID")


def load(path):
    with open(path) as f:
        return json.load(f)


def atomic_write(path, obj):
    """Write whole-object, preserving mode. The session process does the same,
    so the loser of a race is simply overwritten — which is why every caller
    below verifies by re-reading instead of trusting the write."""
    mode = os.stat(path).st_mode & 0o777
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".close-tmp-")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f, indent=2)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# --- naming -----------------------------------------------------------------

def closed_name(current, literal=False):
    """CLOSED_ + the current name.

    Default swaps a leading OPEN_ for CLOSED_ rather than stacking them, which
    is the filing convention this skill assumes (OPEN_x and CLOSED_x name the same
    thread in two states, never CLOSED_OPEN_x). --literal does exactly what the
    name says instead: prefix, whatever is already there.
    """
    if not literal and current.startswith(OPEN_PREFIX):
        return PREFIX + current[len(OPEN_PREFIX):]
    return PREFIX + current


def is_closed(name):
    return name.startswith(PREFIX)


# --- read current state -----------------------------------------------------

def current_name():
    """Returns (name, source_path). The two surfaces agree in normal operation;
    if they disagree the job state wins, and the caller is told."""
    names = {}
    for p in (job_state_path(), session_reg_path()):
        if p:
            try:
                names[p] = load(p).get("name")
            except Exception as e:
                names[p] = f"<unreadable: {e}>"
    return names


def close_record_path():
    sid = session_id()
    if not sid:
        return None
    return os.path.join(CLOSE_DIR, f"{sid}.json")


def existing_close():
    p = close_record_path()
    if p and os.path.exists(p):
        try:
            return load(p)
        except Exception:
            return {"note": "<close record unreadable>"}
    return None


# --- verification -----------------------------------------------------------

def cli_reported_name():
    """Best effort cross-check against what the CLI actually lists. Absence of
    an answer is reported as unknown, never as agreement."""
    sid = session_id()
    if not sid:
        return None, "no CLAUDE_CODE_SESSION_ID"
    try:
        out = subprocess.run(
            ["claude", "agents", "--json", "--all"],
            capture_output=True, text=True, timeout=30,
        )
        if out.returncode != 0:
            return None, f"claude agents exited {out.returncode}"
        for a in json.loads(out.stdout):
            if a.get("sessionId") == sid:
                return a.get("name"), None
        return None, "session not listed by claude agents"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


# --- commands ---------------------------------------------------------------

def cmd_status(args):
    names = current_name()
    prior = existing_close()
    cli, cli_err = cli_reported_name()
    payload = {
        "sessionId": session_id(),
        "pid": os.environ.get("CLAUDE_PID"),
        "jobDir": os.environ.get("CLAUDE_JOB_DIR"),
        "surfaces": names,
        "cliName": cli,
        "cliError": cli_err,
        "alreadyClosed": bool(prior),
        "closeRecord": prior,
    }
    print(json.dumps(payload, indent=2))
    return 0


def cmd_close(args):
    surfaces = [p for p in (job_state_path(), session_reg_path()) if p]
    if not surfaces:
        print(
            "ERROR: found neither a job state file nor a session registry entry.\n"
            "  CLAUDE_JOB_DIR=%r CLAUDE_PID=%r\n"
            "  Nothing was renamed. This session cannot be closed by this script."
            % (os.environ.get("CLAUDE_JOB_DIR"), os.environ.get("CLAUDE_PID")),
            file=sys.stderr,
        )
        return 3

    names = current_name()
    live = [n for n in names.values() if isinstance(n, str)]
    if not live:
        print("ERROR: no readable current name on any surface: %r" % names, file=sys.stderr)
        return 3

    base = live[0]
    if len(set(live)) > 1:
        print("WARNING: surfaces disagree on the current name: %r" % names, file=sys.stderr)
        print("         using %r (job state wins)" % base, file=sys.stderr)

    prior = existing_close()
    if is_closed(base) and not args.force:
        print(
            "Already closed: name is %r%s\n"
            "Nothing changed. Use --force to re-close, or reopen first."
            % (base, "" if not prior else " (closed at %s)" % prior.get("closedAt")),
            file=sys.stderr,
        )
        return 2

    new = closed_name(base, literal=args.literal)

    # Write, then verify by re-reading. The session process rewrites these files
    # on its own schedule, so a write that "succeeded" is not a rename that held.
    written, failed = [], []
    for p in surfaces:
        ok = False
        for _ in range(3):
            try:
                o = load(p)
                o["name"] = new
                o["nameSource"] = "user"      # pin: auto-naming only targets "auto"
                atomic_write(p, o)
                if load(p).get("name") == new:
                    ok = True
                    break
            except Exception as e:
                print("  retry on %s: %s" % (p, e), file=sys.stderr)
        (written if ok else failed).append(p)

    if not written:
        print("ERROR: no surface accepted the rename. Session NOT closed.", file=sys.stderr)
        for p in failed:
            print("  failed: %s" % p, file=sys.stderr)
        return 3

    cli, cli_err = cli_reported_name()

    rec = {
        "sessionId": session_id(),
        "pid": os.environ.get("CLAUDE_PID"),
        "closedAt": datetime.now(timezone.utc).isoformat(),
        "previousName": base,
        "name": new,
        "note": args.note or "",
        "renamed": written,
        "renameFailed": failed,
        "cliVerifiedName": cli,
        "cliVerifyError": cli_err,
        "literal": bool(args.literal),
        "forced": bool(args.force),
    }
    rp = close_record_path()
    if rp:
        os.makedirs(CLOSE_DIR, exist_ok=True)
        with open(rp, "w") as f:
            json.dump(rec, f, indent=2)
        rec["recordPath"] = rp
    else:
        rec["recordPath"] = None
        print("WARNING: no CLAUDE_CODE_SESSION_ID — close record not written.", file=sys.stderr)

    print(json.dumps(rec, indent=2))

    if failed:
        print("\nPARTIAL: %d surface(s) renamed, %d failed — say so in the report."
              % (len(written), len(failed)), file=sys.stderr)
    if cli is not None and cli != new:
        print("\nPARTIAL: files say %r but `claude agents` still reports %r."
              % (new, cli), file=sys.stderr)
        return 3
    if cli is None:
        print("\nNOTE: could not cross-check with `claude agents` (%s). "
              "The files were verified by re-read; the CLI was not consulted."
              % cli_err, file=sys.stderr)
    return 0


def cmd_reopen(args):
    """Undo a close. Closing is meant to be cheap to reverse."""
    surfaces = [p for p in (job_state_path(), session_reg_path()) if p]
    if not surfaces:
        print("ERROR: no writable surface found.", file=sys.stderr)
        return 3
    names = current_name()
    live = [n for n in names.values() if isinstance(n, str)]
    if not live:
        print("ERROR: no readable current name.", file=sys.stderr)
        return 3
    base = live[0]
    if not is_closed(base):
        print("Not closed (name is %r). Nothing to do." % base, file=sys.stderr)
        return 2
    new = base[len(PREFIX):]
    if args.open_prefix:
        new = OPEN_PREFIX + new
    ok_any = False
    for p in surfaces:
        try:
            o = load(p)
            o["name"] = new
            o["nameSource"] = "user"
            atomic_write(p, o)
            ok_any = ok_any or load(p).get("name") == new
        except Exception as e:
            print("  failed %s: %s" % (p, e), file=sys.stderr)
    rp = close_record_path()
    if rp and os.path.exists(rp):
        os.unlink(rp)
    print(json.dumps({"name": new, "reopened": ok_any}, indent=2))
    return 0 if ok_any else 3


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="report session identity, current name, prior close")

    c = sub.add_parser("close", help="rename to CLOSED_* and write the close record")
    c.add_argument("--note", default="", help="one line recorded with the close")
    c.add_argument("--literal", action="store_true",
                   help='prefix CLOSED_ verbatim, even onto an existing OPEN_ prefix')
    c.add_argument("--force", action="store_true", help="re-close an already-closed session")

    r = sub.add_parser("reopen", help="strip CLOSED_ and delete the close record")
    r.add_argument("--open-prefix", action="store_true", help="restore as OPEN_<name>")

    args = ap.parse_args()
    return {"status": cmd_status, "close": cmd_close, "reopen": cmd_reopen}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
