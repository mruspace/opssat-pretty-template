# Our four runs, a worked example

Our experiment ran Mru Flight, fault-tolerance software that votes on three replicas, compares two and self-checks one, on OPS-SAT PRETTY four times in October and November 2026. Every run in orbit matched the prediction written to ESA before it. The packages, the run scripts and every file that came down are public in [mruspace/flight](https://github.com/mruspace/flight/tree/main/opssat).

## Timeline

| Date (2026) | Step |
|---|---|
| October 7 | Registered on opssat.esa.int (mission OPS-SAT PRETTY, not confidential) |
| October 13 | ESA replied and offered an introductory call |
| October 14 | Call with ESA and TU Graz; experiment confirmed with its ID; development environment received (link valid three days) |
| October 15 | Package v0.3.1 sent; ESA's software environment test passed |
| October 16 | FlatSat test passed; one note from ESA (hidden macOS files, [pitfall 1](pitfalls.md#1-hidden-macos-files-in-the-archive)); go-ahead sent with the validated file |
| **October 18** | **Run 1 in orbit**, 227 s: the shrinking quorum and fixed triple redundancy under the same injected faults |
| October 19 | Results received and checked: matched |
| October 20 | ESA agreed to a second short run; package v0.4.0 sent the same night |
| October 21 | Software environment and FlatSat tests; one finding from the run setup ([pitfall 2](pitfalls.md#2-state-left-from-an-earlier-run)) |
| **October 22** | **Run 2 in orbit**, 136 s: down to one replica and a safe halt, and a restart from a checkpoint |
| October 26 | Results reply sent, with the run 3 package attached |
| October 27 | ESA agreed to a third run and asked for the plan for the runs left |
| **October 28** | FlatSat test in the morning; **run 3 in orbit**, 148 s: the same decision core as F´ components (F´ is NASA JPL's flight software framework), each replica a process of its own on the SEPP's two cores, with a real process kill and a restore |
| October 29 | Results received and checked: matched |
| November 2 to 13 | ESA and TU Graz asked which failures the software can simulate; TU Graz suggested a unit that can only be reset, and sensors that disagree |
| November 16 | TU Graz approved run 4; package v0.9.0 sent the same day, as a link (Gmail blocked it as an attachment because the archive holds programs) |
| **November 20** | FlatSat test in the morning; **run 4 in orbit**, 244 s: automatic resets, a sensor voter, the same decision core as a NASA core Flight System (cFS) application, and real bit flips made by software in each replica's own memory |
| November 23 | Results received and checked: matched |

## What each run showed

| Run | Package | In orbit | Result |
|---|---|---|---|
| 1 | the demo, v0.3.1 | October 18, 2026, 09:45 UTC | Shrinking quorum 2,745 correct results and 0 wrong over 5,250 ticks; fixed triple redundancy 239, then a detected disagreement on every tick |
| 2 | the demo, v0.4.0 | October 22, 2026, 09:49 UTC | 698 correct and 0 wrong down to one replica, then a safe halt; after a kill, one resume with the retired replica still retired, 1,750 correct and 0 wrong |
| 3 | F´ deployment, v0.7.0 | October 28, 2026, 09:13 UTC | 342 correct and 0 wrong down to one replica after a real process kill; fixed triple redundancy 239, then none; one restore from the state file, 299 correct and 0 wrong |
| 4 | F´ and cFS, v0.9.0 | November 20, 2026, 20:28 UTC | Six segments, 0 wrong in each. Resets: 394 correct, a replica reset and taken back twice, another kept out after three resets; resets off: 271; fixed triple redundancy 148, then halted; sensors: 279 correct and 120 withheld while the sensors disagreed; cFS: 318; 173 real bit flips, one replica crashed, and the other two delivered all 399 results |

Scope, for all four: software replicas on one Linux payload processor, in user space, with faults injected from a schedule or a command sequence, and in run 4 bit flips made by software in each replica's own memory. Not a hardware-redundancy test, and not radiation.

## Where to look

- Run scripts and package builders: [`opssat/run`](https://github.com/mruspace/flight/blob/main/opssat/run), [`opssat/package.sh`](https://github.com/mruspace/flight/blob/main/opssat/package.sh), [`opssat/fprime2/`](https://github.com/mruspace/flight/tree/main/opssat/fprime2)
- Every file that came down, from the sandbox, the FlatSat and orbit: [`opssat/results`](https://github.com/mruspace/flight/tree/main/opssat/results)
- The operations note, with each prediction and result: [`docs/opssat.md`](https://github.com/mruspace/flight/blob/main/docs/opssat.md)
- The write-ups: [run 1](https://mru.space/research/flight-orbit/), [run 2](https://mru.space/research/flight-orbit-2/), [run 3](https://mru.space/research/flight-orbit-3/), [run 4](https://mru.space/research/flight-run4-package/)
