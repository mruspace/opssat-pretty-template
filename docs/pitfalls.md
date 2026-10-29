# Pitfalls

Every item here happened to us on exp4051 in October 2026, or nearly did. Each has what happened, why, and what catches it now.

### 1. Hidden macOS files in the archive

**What happened.** ESA's first test found `._run`, `._quorum` and similar entries in our package. **Why.** macOS tar stores extended attributes (here `com.apple.provenance`) as extra `._NAME` entries, and the macOS tar listing hides them, so our own check did not show them. **Now.** `package.sh` sets `COPYFILE_DISABLE=1` and `--no-mac-metadata`; `check-package.py` reads the archive with Python's tarfile, which shows every entry, and fails on them.

### 2. State left from an earlier run

**What happened.** On the FlatSat, our restart test resumed three times instead of once. **Why.** The home folder still held a checkpoint from an earlier run of the same package, and our script did not remove it. Every laptop test had started from a fresh unpack. **Now.** `template/run` removes `toGround/` and any state you name with `remove_state` before it starts, and logs it. `test-local.sh` runs every package twice in the same folder. (We still flew the validated file: the code was right, the setup was not, and the satellite's folder was clean.)

### 3. Emulation is not the SEPP

**What happened.** The SEPP ran our demo about three times slower per tick than the same binary under emulation on a laptop, and about six times slower than ESA's sandbox. **Now.** Put work in counts, give every step a cap, and check that every scheduled event lands inside its cap at a third of your laptop's speed. See [testing.md](testing.md).

### 4. A time limit checked too rarely

**What happened.** Our first package ran about 3 seconds past its 110-second cap, on the FlatSat and in orbit. **Why.** The program checked the time once per tick, and the last tick started a long memory scan just before the limit. **Now.** Check the deadline inside long work, and never sleep past it (`example/workload.c` does both). `template/run` also stops a step at its cap from outside.

### 5. CPU readings from emulation

**What happened.** Our CPU estimates from emulation were wrong in both directions: on the SEPP our demo used more CPU than under emulation, and our F´ package far less. **Now.** Report CPU only as measured on the FlatSat or in orbit, with its scope. Log CPU time by phase (start-up, run, end; user and kernel apart), so a figure you did not expect can be placed. And keep a CPU share by the process's real CPU time, not by how long your work took: system calls and the sleeps themselves cost CPU too. The first version of this template's example kept the share by work time and read 7.5% for a 5% setting on an emulated CI runner; by CPU time it reads 5.00%.

### 6. A background entry point

**What happened.** Our first launcher started the program in the background and returned, which suits a service and not ESA's runner, which waits for `./run`. **Now.** `template/run` stays in the foreground until every step is done.

### 7. bash or Python on the target

The SEPP image has busybox only. A `#!/bin/bash` script or a Python helper fails there and works on your laptop. **Now.** `check-package.py` fails on bash, zsh and Python shebangs; `test-local.sh` runs under busybox.

### 8. Timeouts tuned on a fast host

**What happened.** In our F´ deployment, a manager that fell behind (a slow write, a busy processor) closed cycles before the answers arrived, and healthy replicas looked dead. CI caught it under starvation before it flew. On the FlatSat the fixed rule fired once, as designed. **Now.** Test under CPU starvation (for example, run the package while the host is loaded), and design timeouts for a host several times slower.

### 9. An unoptimized build

**What happened.** F´ builds unoptimized by default. Our first build spent 84% of its time in one hash function and used 8% of the CPU at a 20 ms cycle. **Now.** Build with optimization, and measure the CPU share before you choose the cycle rate.

### 10. The laptop went to sleep

**What happened.** A five-minute local test took 478 seconds: the Mac slept for 327 of them. **Now.** On macOS, run long tests under `caffeinate -i`.

### 11. Links that expire

ESA's download links for the development environment and the results were valid for three days. Download and store everything the day it arrives.

### 12. Messages that look like errors

A planned `SIGKILL` shows as "Killed" in the journal. A framework that cannot set thread priorities as user `exp` prints a note about it. Links between processes print warnings when the other end is killed on purpose. Name all of these in your operator note before the run, so operators do not stop to ask.

### 13. Proving which build ran

Record the checksum of every file of the package at the start of the run (`template/run` does) and compare it with what you sent. Tag the release you build the package from, and build the package from the release, not from your working tree.
