# The guide, step by step

From the idea to the results of your run in orbit. Each step ends with a short checklist. The dates are what happened for exp4051 in October 2026; yours will differ. Where ESA tells you something different, follow ESA.

## 0. Is PRETTY the right platform?

OPS-SAT PRETTY is a 3U CubeSat in a 520 km sun-synchronous orbit, operated by TU Graz, with experiment time offered by ESA's OPS-SAT Space Lab at no charge. Experiments run on the SEPP, the satellite's experimental processing platform: an Altera Cyclone V SoC with two ARM Cortex-A9 cores at 800 MHz, 1 GB of memory and Linux.

It fits an experiment that:

- runs as ordinary software in user space for five minutes or less;
- needs a real flight processor in a real space environment, not a radiation beam or a bench;
- can say in advance what it will do, so the result means something.

It does not fit an experiment that needs privileged access, long runs, or hardware you have not agreed with ESA. The platform has other payloads (a software-defined radio, a GNSS receiver, a dosimeter); what an experiment may use is ESA's decision. For exp4051, ESA told us the dosimeter and its data are not available to experimenters.

- [ ] The experiment fits five minutes, in user space.
- [ ] You can write down what it will do before it runs.

## 1. Register

Register at [opssat.esa.int/register](https://opssat.esa.int/register). The form asks for the mission (OPS-SAT PRETTY), a title, the aim, a description, and whether the experiment is confidential. Keep the aim to one sentence a reviewer can repeat. Say what success looks like and what comes back to ground.

If you plan to publish, say so and choose "not confidential". We did, and every result we published credits the ESA OPS-SAT Space Lab and TU Graz.

For exp4051, ESA replied six days after the registration and offered a short introductory call. In the call they asked one sharp question: were the faults real hardware faults or simulated? Have a plain answer to that kind of question ready. They also set the rule that each run completes in five minutes or less.

- [ ] Aim in one sentence; success described; outputs described.
- [ ] Confidential or not, decided.

## 2. Get the development environment, and save it at once

With the confirmation came an experiment ID (use it in every email subject as ESA asks) and a link to the development environment: a README and a root filesystem tarball of the SEPP's experiment environment. **The download link expired after three days.** Download everything at once and keep it.

Read ESA's README in full. [docs/rules.md](rules.md) lists the rules as they were in October 2026.

- [ ] Environment and README saved locally.
- [ ] Experiment ID noted; the subject tag and the addresses to copy noted from ESA's email.

## 3. Design for the window

Five minutes is short, and you cannot watch the run. Design so that the files that come down answer your question without you being there:

- **Put the work in counts, not seconds.** A fixed number of ticks, samples or iterations gives the same result on every host. The SEPP is slower than your laptop, and slower than ESA's sandbox: our demo ran about three times slower per tick on the SEPP than under emulation on a laptop, and about six times slower than in ESA's sandbox.
- **Give every step a cap in seconds**, as a safety net under the counts. The caps plus a few seconds per step must add up to well under five minutes. The template's default budget is 270 seconds.
- **Schedule events early.** If something must happen at tick 240, make sure tick 240 comes inside the cap on the slowest host.
- **Keep a CPU share** if you registered one, by sleeping between units of work, and count start-up in it.
- **Set your own memory limit** (`RLIMIT_AS`), so a bug fails your process, not the platform.
- **Write small, plain outputs**: key=value summaries and short event logs. A few kilobytes is plenty.
- **Record what ran**: host, processor, checksums of your files, start and end times, exit codes. `template/run` does this in `run-info.txt`.

- [ ] Work in counts; caps and budget add up.
- [ ] Every event lands inside the cap on a host three times slower.
- [ ] Outputs small and parseable.

## 4. Build for the SEPP

The target is 32-bit ARM, hard float, musl libc (Alpine Linux 3.21 armhf). A **static** binary needs nothing from the image and is the simplest choice. There is no Python and no bash on the target, only busybox.

| Language | Static build for the SEPP |
|---|---|
| C or C++ | In an Alpine armhf container: `gcc -O2 -static` (see [`scripts/build-example.sh`](../scripts/build-example.sh)). Or Debian's `arm-linux-gnueabihf-g++` with `-static` (static glibc works). |
| Rust | Target `armv7-unknown-linux-musleabihf`, for example with [`cross`](https://github.com/cross-rs/cross). Mru Flight ships this way. |
| Go | `CGO_ENABLED=0 GOOS=linux GOARCH=arm GOARM=7 go build` |
| Scripts | POSIX sh only (busybox `sh`). |

Build optimized. F´, the flight software framework we used, builds unoptimized by default: our first build spent 84% of its time in one hash and used 8% of the CPU at a 20 ms cycle, where we wanted well under 5%.

`scripts/check-package.py --binary FILE` tells you whether a binary is 32-bit ARM, hard float and static.

- [ ] Static, 32-bit ARM, hard float, optimized.
- [ ] No bash, no Python on the target.

## 5. Write `run`

Copy [`template/run`](../template/run) and edit only the section marked "Your experiment":

```sh
remove_state "$OUT_DIR/state.dat"                       # nothing carried over from an earlier run
step measure 120 ./my-experiment --samples 5000 --summary "$OUT_DIR/summary-measure.txt"
step_kill crash 60 30 ./my-experiment --resume "$OUT_DIR/state.dat"   # a planned SIGKILL at 30 s
```

`step` runs a command, sends its output to `toGround/stdout-NAME.txt`, stops it at its cap (SIGTERM, then SIGKILL after a grace) and records the exit code. `step_kill` adds a planned SIGKILL, for experiments that test what survives a crash. A step that would end the run after the budget is skipped and logged, never started. On SIGTERM from the runner, `run` passes it on, records it and exits.

Edit the operator note too: [`template/README.txt`](../template/README.txt). Operators read it before they run your package. Say what runs, how long, what it touches, what comes out, and which lines in the logs are expected and not errors.

- [ ] `run` edited only in its experiment section.
- [ ] `README.txt` filled in, with expected warnings named.

## 6. Test on the ground

```sh
scripts/test-local.sh dist/expNNNN-name.tar.gz                    # Alpine armhf stand-in
docker import --platform linux/arm/v7 exp_env.tar.gz opssat-pretty-env
scripts/test-local.sh dist/expNNNN-name.tar.gz opssat-pretty-env  # ESA's own environment
```

The test unpacks the package as user `exp` into an empty home folder, runs it, then **runs it again in the same folder**, because the FlatSat and the satellite can reuse it. Both runs must exit 0, finish under five minutes and leave no process behind. Run your full-length package this way before you send it, and keep the machine awake for the whole test.

Timing and CPU share under emulation are not the SEPP's. [docs/testing.md](testing.md) explains what to trust.

- [ ] Both runs pass in ESA's image, full length.
- [ ] Results checked against your prediction (next step).

## 7. Write the prediction, before you send

Write down what the run will produce: the counts and events your code decides, exactly, and ranges for what the host decides (time, CPU, memory). Put it in a TOML file for `check-results.py`, and put the main numbers in the email that carries the package. A prediction written before the run is what makes the result evidence. [docs/prediction.md](prediction.md) shows how.

- [ ] Prediction file written and passing on your local run.
- [ ] The main numbers ready for the email.

## 8. Package and check

```sh
scripts/package.sh -n expNNNN-name template/run build/my-experiment template/README.txt LICENSE
```

`package.sh` checks the archive at the end. Fix every error. Read every warning.

- [ ] `check-package.py` passes on the exact file you will send.
- [ ] You tested that exact file, not an earlier build.

## 9. Send

Send the package to ESA as they asked, with their subject tag and the addresses they named. Make the email an operator's note: what the package is, what it does, how long it runs, what it touches, what comes back, the expected warnings, and your prediction. Leave out what they do not need (checksums are in `README.txt`). [docs/emails.md](emails.md) has a template.

- [ ] One email, with the package, the note and the prediction.

## 10. Sandbox and FlatSat results

ESA runs the package in their software environment, then TU Graz runs it on the FlatSat, the flight processor on the bench. Results come back as an archive (see [docs/results.md](results.md)). For exp4051 the results of both tests came back one to two days after ESA accepted the package.

Check the FlatSat result against your prediction with `check-results.py`, then reply: the result matches, or what differs and why. **The FlatSat is your first real measurement of the SEPP**: timing, CPU share and memory are real here for the first time.

If something differs:

- **The code is right and the problem came from the run setup** (for example an old file in the home folder): fly the file ESA validated again, say exactly what to change in the setup, and fix it in your next package. A new package sends ESA back through both tests.
- **A bug that can change the result or affect the platform**: fix it, test it, send a new package.

- [ ] FlatSat checked against the prediction.
- [ ] A clear go-ahead, or a clear fix.

## 11. The run in orbit

After your go-ahead, TU Graz runs the package on the satellite and ESA sends the results. Check them the same way, then reply: confirm the result in numbers, thank the team, and make one clear ask if you want another run. If you publish, say so in one line and credit ESA's OPS-SAT Space Lab and TU Graz.

- [ ] Result checked and confirmed in numbers.
- [ ] One ask, if any.

## 12. Another run

Ask for one more run at a time, five minutes each, with the package already built and tested, and say what the run adds. ESA plans the platform's time across many experimenters: when they asked us how many runs we expected, a short, honest answer was the right one.
