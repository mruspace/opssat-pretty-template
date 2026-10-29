#!/bin/sh
# test-local.sh: run a package the way ESA's runner does, before you send it.
#
#   scripts/test-local.sh PACKAGE.tar.gz [IMAGE]
#
# Unpacks the package as user exp (uid 1024) into an empty $HOME in a 32-bit
# ARM Linux container, runs ./run in the foreground, then runs it a second
# time in the same folder: the FlatSat and the satellite can reuse $HOME, so
# a second run must not start from the first one's state. It times both runs,
# checks the exit codes and the five-minute limit, and copies each run's
# toGround/ to test-results/.
#
# IMAGE defaults to alpine:3.21 (armhf), the same Linux and C library as the
# SEPP's experiment environment. Registered experimenters get ESA's own
# environment as a root filesystem tarball; import it once and pass its name:
#
#   docker import --platform linux/arm/v7 exp_env.tar.gz opssat-pretty-env
#   scripts/test-local.sh dist/exp0000-example.tar.gz opssat-pretty-env
#
# Timing under emulation is not the SEPP's: see docs/testing.md. On a laptop,
# keep it awake for long tests (macOS: caffeinate -i scripts/test-local.sh ...).
set -eu

[ $# -ge 1 ] || { echo "usage: $0 PACKAGE.tar.gz [IMAGE]" >&2; exit 2; }
pkg=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
image=${2:-alpine:3.21}
root=$(cd "$(dirname "$0")/.." && pwd)
stamp=$(date -u '+%Y%m%dT%H%M%SZ')
out="$root/test-results/$stamp"
mkdir -p "$out"

docker run --rm --platform linux/arm/v7 \
    -v "$pkg:/pkg/package.tar.gz:ro" -v "$out:/out" "$image" /bin/sh -c '
set -u
id exp >/dev/null 2>&1 || adduser -D -u 1024 exp >/dev/null 2>&1 || {
    echo "exp:x:1024:1024::/home/exp:/bin/sh" >>/etc/passwd
    echo "exp:x:1024:" >>/etc/group
}
mkdir -p /home/exp && chown 1024:1024 /home/exp
cd /home/exp
su exp -s /bin/sh -c "tar -xzf /pkg/package.tar.gz" || { echo "unpack failed"; exit 1; }
for n in 1 2; do
    t0=$(date +%s)
    su exp -s /bin/sh -c "cd /home/exp && HOME=/home/exp ./run"
    rc=$?
    t1=$(date +%s)
    echo "run $n: exit=$rc seconds=$((t1 - t0))" | tee -a /out/summary.txt
    mkdir -p /out/run-$n && cp -R /home/exp/toGround/. /out/run-$n/ 2>/dev/null
    left=$(ps -o user,pid,comm 2>/dev/null | grep -c "^exp ")
    echo "run $n: processes of exp left after the run: $left" | tee -a /out/summary.txt
done
chmod -R a+rwX /out
'

echo
fail=0
while read -r line; do
    case $line in
    *exit=0*) ;;
    *exit=*) fail=1 ;;
    esac
    case $line in
    *seconds=*)
        s=${line##*seconds=}
        [ "$s" -le 300 ] || { echo "error: a run took $s s, over the five-minute limit"; fail=1; }
        ;;
    esac
    case $line in
    *"left after the run: 0") ;;
    *"left after the run"*) echo "error: processes left after the run"; fail=1 ;;
    esac
done <"$out/summary.txt"
echo "results: test-results/$stamp (run-1/ and run-2/ hold each run's toGround/)"
if [ "$fail" -ne 0 ]; then
    echo "FAIL"
    exit 1
fi
echo "ok: both runs exit 0, under five minutes, no process left"
