#!/bin/sh
# harness.sh: test template/run itself on the host, with a native build of
# the example workload: a step stopped at its cap, a planned kill, a step
# skipped because it would break the budget, state removed from an earlier
# run, and no process left behind. Runs under every shell given, default sh;
# CI also runs it under busybox sh, the SEPP's shell.
#
#   tests/harness.sh [SHELL...]
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
${CC:-cc} -std=c11 -O2 -o "$work/workload" "$root/example/workload.c"

fail=0
expect() { # FILE TEXT
    if grep -qF -- "$2" "$1"; then echo "  ok   $2"; else echo "  FAIL missing: $2"; fail=1; fi
}

for shell in "${@:-sh}"; do
    echo "== $shell"
    pkg=$work/pkg-$(echo "$shell" | tr ' /' '__')
    mkdir -p "$pkg"
    cp "$work/workload" "$pkg/"
    # The template with its experiment section replaced by the test steps.
    awk '
        /^# ---- Your experiment/ { print; skip = 1; while ((getline line < "/dev/stdin") > 0) print line; next }
        /^# ---- to here/ { skip = 0 }
        !skip { print }
    ' "$root/template/run" >"$pkg/run" <<'STEPS'
echo old >"$here/state.dat"
remove_state "$here/state.dat"
step capped 2 ./workload --ticks 1000000000 --max-seconds 60 --cpu-percent 50 \
    --summary "$OUT_DIR/summary-capped.txt"
step_kill killed 10 2 ./workload --ticks 1000000000 --max-seconds 60 --cpu-percent 50 \
    --summary "$OUT_DIR/summary-killed.txt"
step quick 5 ./workload --ticks 100 --summary "$OUT_DIR/summary-quick.txt"
step too-long 1000 ./workload --ticks 1
STEPS
    chmod 755 "$pkg/run"
    mkdir -p "$pkg/toGround" && echo stale >"$pkg/toGround/old.txt"

    rc=0
    (cd "$pkg" && BUDGET_SECONDS=60 $shell ./run) || rc=$?
    info=$pkg/toGround/run-info.txt
    if [ "$rc" -eq 1 ]; then echo "  ok   exit 1 (a step was skipped)"; else echo "  FAIL exit $rc, expected 1"; fail=1; fi
    expect "$info" "removed 1 files left in toGround/ by an earlier run"
    expect "$info" "removed state left by an earlier run: $pkg/state.dat"
    expect "$info" "capped: reached its cap of 2 s"
    expect "$info" "capped: exit=0"
    expect "$pkg/toGround/summary-capped.txt" "stopped=signal"
    expect "$info" "killed: killed (SIGKILL)"
    expect "$info" "killed: exit=137"
    expect "$info" "quick: exit=0"
    expect "$pkg/toGround/summary-quick.txt" "ticks=100 planned=100 stopped=done"
    expect "$info" "too-long: skipped"
    expect "$info" "status=1"
    if [ ! -e "$pkg/state.dat" ]; then echo "  ok   state file removed"; else echo "  FAIL state file still there"; fail=1; fi
    if [ ! -e "$pkg/toGround/old.txt" ]; then echo "  ok   old output removed"; else echo "  FAIL old output still there"; fail=1; fi
    sleep 1
    if pgrep -f "$pkg" >/dev/null 2>&1; then
        echo "  FAIL a process of the run is still alive"
        fail=1
    else
        echo "  ok   no process left"
    fi
done
if [ "$fail" -ne 0 ]; then echo "FAIL"; exit 1; fi
echo "ok: harness behaves as documented"
