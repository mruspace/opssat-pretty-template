#!/bin/sh
# build-example.sh: build example/workload.c as a static binary for the SEPP
# (32-bit ARM, hard float, musl libc), in an Alpine 3.21 armhf container, the
# same Linux and C library as the SEPP's experiment environment.
#
#   scripts/build-example.sh            writes build/workload
#
# Needs Docker with ARM emulation (Docker Desktop has it; on Linux, install
# qemu-user-static or run docker/setup-qemu-action in CI).
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$root/build"
docker run --rm --platform linux/arm/v7 \
    -v "$root/example:/src:ro" -v "$root/build:/out" alpine:3.21 \
    sh -ec 'apk add --no-cache gcc musl-dev >/dev/null
            gcc -std=c11 -O2 -Wall -Wextra -Werror -static -o /out/workload /src/workload.c
            strip /out/workload
            chown '"$(id -u):$(id -g)"' /out/workload'
echo "built build/workload"
python3 -I "$root/scripts/check-package.py" --binary "$root/build/workload"
