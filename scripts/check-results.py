#!/usr/bin/env python3
"""check-results.py: check what came down against the prediction you wrote before the run.

    scripts/check-results.py PREDICTION.toml RESULTS

RESULTS is what ESA sends back (a pack-*.tar.gz with the SEPP journal and
chg/toGround/), a toGround/ folder, or a run folder from scripts/test-local.sh.
The prediction is a TOML file (see prediction.example.toml):

    [run]                       the last line of run-info.txt
    status = 0
    seconds = { max = 270 }

    [steps.baseline]            the "baseline: exit=..." line of run-info.txt
    exit = 0

    [files."summary-baseline.txt"]   key=value pairs in that file
    ticks = 20000
    stopped = "done"
    run_share = { max = 5.0 }        a range: min, max or both

A number is compared as a number (units such as s, % and KiB are dropped);
anything else must match exactly. Exit 1 if any check fails. Needs Python 3.11+.
"""
import os
import re
import sys
import tarfile
import tomllib

PAIR = re.compile(r"([A-Za-z_][\w.-]*)=(\S+)")


def pairs(text):
    out = {}
    for k, v in PAIR.findall(text):
        out.setdefault(k, v)
    return out


def load(path):
    """Return ({file name: text}, journal text or None) from a pack, folder or run folder."""
    files, journal = {}, None
    if os.path.isfile(path):
        with tarfile.open(path, "r:*") as t:
            for m in t.getmembers():
                if not m.isfile():
                    continue
                parts = m.name.split("/")
                data = t.extractfile(m).read().decode(errors="replace")
                if "toGround" in parts:
                    files["/".join(parts[parts.index("toGround") + 1:])] = data
                elif parts[-1] in ("log", "journal.log"):
                    journal = data
        return files, journal
    base = path
    if not os.path.exists(os.path.join(base, "run-info.txt")) and os.path.isdir(os.path.join(base, "toGround")):
        base = os.path.join(base, "toGround")
    for dirpath, _, names in os.walk(base):
        for n in names:
            p = os.path.join(dirpath, n)
            with open(p, encoding="utf-8", errors="replace") as f:
                files[os.path.relpath(p, base)] = f.read()
    for n in ("journal.log", "log"):
        p = os.path.join(path, n)
        if os.path.isfile(p):
            with open(p, encoding="utf-8", errors="replace") as f:
                journal = f.read()
    return files, journal


def number(v):
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)(?:s|%|KiB|MB|kB|B)?", v)
    return float(m.group(1)) if m else None


def compare(expected, observed):
    """Return (ok, how) for one expected value against one observed string."""
    if observed is None:
        return False, "missing"
    if isinstance(expected, dict):
        x = number(observed)
        if x is None:
            return False, "not a number"
        lo, hi = expected.get("min"), expected.get("max")
        ok = (lo is None or x >= lo) and (hi is None or x <= hi)
        rng = f"{'' if lo is None else lo}..{'' if hi is None else hi}"
        return ok, f"in {rng}"
    if isinstance(expected, bool):
        return observed.lower() == str(expected).lower(), "equal"
    if isinstance(expected, (int, float)):
        x = number(observed)
        return x is not None and x == expected, "equal"
    return observed == str(expected), "equal"


def main():
    if len(sys.argv) != 3:
        print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
        return 2
    with open(sys.argv[1], "rb") as f:
        pred = tomllib.load(f)
    files, journal = load(sys.argv[2])
    if "run-info.txt" not in files:
        print(f"error: no run-info.txt found in {sys.argv[2]}")
        return 1

    info = files["run-info.txt"]
    run_line = next((l for l in reversed(info.splitlines()) if l.startswith("end_utc=")), "")
    steps = {}
    for line in info.splitlines():
        m = re.match(r"([\w.-]+): (.*)$", line)
        if m and ("exit=" in m.group(2)):
            steps.setdefault(m.group(1), {}).update(pairs(m.group(2)))

    rows, failed = [], 0

    def check(where, key, expected, observed):
        nonlocal failed
        ok, how = compare(expected, observed)
        failed += not ok
        rows.append((ok, where, key, expected, observed if observed is not None else "-", how))

    for k, v in pred.get("run", {}).items():
        check("run", k, v, pairs(run_line).get(k))
    for name, keys in pred.get("steps", {}).items():
        for k, v in keys.items():
            check(f"step {name}", k, v, steps.get(name, {}).get(k))
    for fname, keys in pred.get("files", {}).items():
        text = files.get(fname)
        got = pairs(text) if text is not None else {}
        for k, v in keys.items():
            check(fname, k, v, got.get(k) if text is not None else None)

    if journal:
        print("journal:")
        for line in journal.strip().splitlines():
            print(f"  {line}")
        print()
    print("files: " + ", ".join(sorted(files)))
    print()
    w = max(len(r[1]) for r in rows) if rows else 10
    for ok, where, key, expected, observed, how in rows:
        exp = expected if not isinstance(expected, dict) else {k: v for k, v in expected.items()}
        print(f"{'ok  ' if ok else 'FAIL'} {where:<{w}} {key} = {observed}  (expected {exp}, {how})")
    print()
    if failed:
        print(f"FAIL: {failed} of {len(rows)} checks differ from the prediction")
        return 1
    print(f"ok: all {len(rows)} checks match the prediction")
    return 0


if __name__ == "__main__":
    sys.exit(main())
