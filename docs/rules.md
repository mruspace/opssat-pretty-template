# Rules of the experiment environment

What the package must be and how it runs, as we met it in October 2026. Sources: ESA's README for the OPS-SAT PRETTY experiment development environment (v0.3, dated January 15, 2026), our introduction meeting with ESA (October 14, 2026), and what we saw in three runs. ESA's current documents are the authority; check every line against what ESA sends you.

## The package

| Rule | What to do | Checked by |
|---|---|---|
| One `tar.gz` archive | `scripts/package.sh` | `check-package.py` |
| All paths relative | no leading `/`, no `..` | `check-package.py` |
| Every file owned by user and group `exp` | ESA's README gives `tar --owner=exp --group=exp -zcvf NAME.tar.gz FILES`; `package.sh` also sets uid and gid 1024, the `exp` user we saw on the SEPP | `check-package.py` |
| An executable `run` at the top | `chmod 755 run`; `#!/bin/sh` | `check-package.py` |
| No hidden files | build with `COPYFILE_DISABLE=1` on macOS | `check-package.py` |

## The run

- ESA's runner unpacks the package into the home folder of user `exp` and executes `./run` there, **as user `exp`**. On the SEPP we saw systemd start a unit named "Experiment NNNN" that runs the experiment in a container named `exp-NNNN`.
- `run` must stay in the **foreground** until the experiment is done. Do not start work in the background and exit.
- The home folder is writable. **Anything changed there is collected and sent to ground.** Put outputs in one folder (`toGround/`) and leave nothing else behind.
- **Five minutes or less** per run (ESA, October 14, 2026). Keep a margin: the template's budget is 270 seconds.
- The home folder can still hold files from an earlier run of the same package (we saw this on the FlatSat). Remove state you resume from before you start.

## The target

| | |
|---|---|
| Processor | The SEPP: Altera Cyclone V SoC, two ARM Cortex-A9 cores at 800 MHz (`armv7l`), 1 GB of memory |
| Operating system | Alpine Linux 3.21 (we saw kernel 4.9 on the SEPP) |
| Architecture | 32-bit ARM, hard float (`armhf`), musl libc |
| Shell and tools | busybox; no bash, no Python |
| Libraries in the image | busybox, musl, libiio, libserialport and others (see ESA's README). A static binary needs none of them. |

## Limits we kept

ESA did not hand us a list of resource limits. We stated ours in the registration and kept them, enforced by our own processes:

- user space only: no network, no device files, no privileged calls, no reboots;
- 128 MB of address space per process (`RLIMIT_AS`);
- a CPU share stated in the registration (5% of one core for our first package);
- at most four processes at a time;
- a few kilobytes of output.

Agree your own with ESA, state them in your operator note, and enforce them in your code. Things we saw work as user `exp` on the SEPP: pinning a process to a core (`sched_setaffinity`), and sending signals to your own processes. Things that did not: setting thread priorities (a framework we used printed a note and ran without them).
