# Testing on the ground

Three places to test before orbit, and what each one can tell you.

| Where | Who | What it proves | What it cannot |
|---|---|---|---|
| Alpine armhf container (`scripts/test-local.sh PACKAGE`) | You, any time | The package unpacks, `run` works under busybox as user `exp`, binaries run on 32-bit ARM with musl, the run finishes and leaves nothing behind, a second run in the same folder works | Speed, CPU share, anything specific to ESA's image |
| ESA's environment image (`scripts/test-local.sh PACKAGE opssat-pretty-env`) | You, once registered | The same, in the exact root filesystem of the SEPP | Speed and CPU share: it runs under emulation |
| TU Graz FlatSat | ESA and TU Graz, after you send | Everything on the flight processor, on the bench: real timing, real CPU share, real memory | The space environment |

## ESA's image

ESA's README suggests entering the root filesystem with `chroot` under `qemu-user-static` on Debian. With Docker it imports as an image:

```sh
docker import --platform linux/arm/v7 exp_env.tar.gz opssat-pretty-env
scripts/test-local.sh dist/expNNNN-name.tar.gz opssat-pretty-env
```

Do not publish ESA's image or README; they are ESA's.

## What emulation gets wrong

On a laptop, the 32-bit ARM binary runs under emulation. That changes speed and CPU readings, and not always in the same direction. Measured in our runs, scope as stated:

| Measure | Laptop, ESA's image under emulation (Apple silicon) | SEPP (FlatSat or orbit) |
|---|---|---|
| Demo ticks per second at a 5% CPU share (run 1, October 15 and 16, 2026) | about 130 | about 45 (ESA's sandbox VM: about 270) |
| Demo voter CPU, share of wall time (run 2, October 20 to 22, 2026) | 4.3% to 4.6% | 4.6% to 5.8% |
| F´ deployment, four processes, share of wall time (run 3, October 22 to 28, 2026) | 2.6% to 3.7% | 0.75% to 0.99% |
| Run 3 total wall time | 148 s | 148 s (every step ran to its cap) |

So:

- **Put work in counts, not seconds.** Then the result is the same everywhere, and only the time it takes changes.
- **Plan for a SEPP about three times slower than your emulated laptop** for compute-bound work, and check every scheduled event lands inside its cap at that speed.
- **Do not predict a CPU share from emulation.** Emulation read our demo low and our F´ processes high (the emulator's own start-up cost lands in the processes it runs). Report CPU only as measured on the FlatSat or in orbit, and log it by phase (start-up, run, end) so a surprise can be placed.
- **Time-capped steps take the same wall time everywhere.** Only the work done inside them changes.

## Long tests on a laptop

A laptop that sleeps in the middle of a test gives a wrong wall time and can break timeouts. One of our five-minute tests took 478 seconds because the Mac slept for 327 of them. On macOS run long tests under `caffeinate -i`.
