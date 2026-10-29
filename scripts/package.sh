#!/bin/sh
# package.sh: build an experiment package for OPS-SAT PRETTY.
#
#   scripts/package.sh -n NAME FILE...
#
# Writes dist/NAME.tar.gz with FILE... at the top level, all paths relative,
# every entry owned by user and group exp (uid and gid 1024), no hidden
# entries, and the checksums of the package files appended to README.txt.
# The files must include an executable "run". Then it checks the archive
# with scripts/check-package.py, which fails on anything ESA's runner or the
# SEPP would not accept.
#
# Example, the package of this repository:
#   scripts/package.sh -n exp0000-example template/run build/workload template/README.txt LICENSE
set -eu

# macOS tar stores extended attributes as extra "._NAME" entries, and the
# macOS tar listing hides them. This and --no-mac-metadata below stop them.
export COPYFILE_DISABLE=1

root=$(cd "$(dirname "$0")/.." && pwd)
name=
while getopts n: opt; do
    case $opt in
    n) name=$OPTARG ;;
    *) echo "usage: $0 -n NAME FILE..." >&2; exit 2 ;;
    esac
done
shift $((OPTIND - 1))
[ -n "$name" ] && [ $# -gt 0 ] || { echo "usage: $0 -n NAME FILE..." >&2; exit 2; }

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
for f in "$@"; do
    [ -f "$f" ] || { echo "error: $f is not a file" >&2; exit 1; }
    cp "$f" "$stage/$(basename "$f")"
done
[ -f "$stage/run" ] || { echo "error: the package needs a file named run" >&2; exit 1; }
chmod 755 "$stage/run"
for f in "$stage"/*; do
    # executables keep their bit; everything else is read-only data
    if [ -x "$f" ]; then chmod 755 "$f"; else chmod 644 "$f"; fi
done

sha() { (sha256sum "$1" 2>/dev/null || shasum -a 256 "$1") | cut -d' ' -f1; }
if [ -f "$stage/README.txt" ]; then
    {
        echo
        echo "Package $name, built $(date -u '+%Y-%m-%d %H:%M UTC'). Checksums (sha256):"
        for f in "$stage"/*; do
            b=$(basename "$f")
            [ "$b" = README.txt ] || echo "  $b $(sha "$f")"
        done
    } >>"$stage/README.txt"
fi

mkdir -p "$root/dist"
out="$root/dist/$name.tar.gz"
files=$(cd "$stage" && ls)
# shellcheck disable=SC2086 # file names are plain words, split on purpose
if tar --version 2>/dev/null | grep -q bsdtar; then
    tar -C "$stage" --no-mac-metadata --uname exp --gname exp --uid 1024 --gid 1024 -czf "$out" $files
else
    tar -C "$stage" --owner=exp:1024 --group=exp:1024 -czf "$out" $files
fi
echo "wrote dist/$name.tar.gz"
python3 -I "$root/scripts/check-package.py" "$out"
