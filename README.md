<p align="center">
  <a href="https://mru.space">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://mru.space/assets/readme/mru-github-dark.gif">
      <img src="https://mru.space/assets/readme/mru-github-light.gif" alt="Mru" width="120" height="120">
    </picture>
  </a>
</p>

# OPS-SAT PRETTY experiment template

A template and a step-by-step guide for running your own software experiment on ESA's OPS-SAT PRETTY satellite, from registration to the results in your hands. It comes from experiment exp4051, which ran Mru Flight in orbit three times in October 2026, each run as predicted. Part of [Mru](https://mru.space).

> **Unofficial.** This is not an ESA or TU Graz product, and they have not reviewed it. It is what one experimenter learned. ESA's rules and documents are the authority: where this guide and ESA differ, follow ESA, and tell us so we can fix it.

## What you get

| | |
|---|---|
| [`template/run`](template/run) | The entry point ESA's runner executes: foreground, a cap on every step, a budget for the whole run, a record of what ran, no state carried over from an earlier run, no process left behind. POSIX sh, so it runs on the SEPP's busybox. |
| [`example/workload.c`](example/workload.c) | A small example experiment that does a fixed amount of work at a capped CPU share and writes a summary the ground can check. Replace its work with yours, keep the rest. |
| [`scripts/package.sh`](scripts/package.sh) | Builds the `tar.gz` the way the runner needs it: relative paths, every file owned by `exp`, no hidden macOS entries, checksums in the operator note. |
| [`scripts/check-package.py`](scripts/check-package.py) | Catches what costs a round trip: wrong owner, macOS metadata, a 64-bit or x86 binary, a bash script, a non-executable `run`. |
| [`scripts/test-local.sh`](scripts/test-local.sh) | Runs the package as the runner does, in a 32-bit ARM container, twice in the same folder, with the five-minute limit checked. Works with ESA's own environment image once you have it. |
| [`scripts/check-results.py`](scripts/check-results.py) | Reads the archive ESA sends back and checks it against the prediction you wrote before the run. |
| [`docs/`](docs) | The guide, the rules, testing, predictions, results, pitfalls, email templates, and the exp4051 timeline as a worked example. |

## Quick start

You need Docker with ARM emulation (Docker Desktop has it) and Python 3.11 or newer.

```sh
git clone https://github.com/mruspace/opssat-pretty-template && cd opssat-pretty-template
scripts/build-example.sh                       # static 32-bit ARM build of the example
scripts/package.sh -n exp0000-example template/run build/workload template/README.txt LICENSE
scripts/test-local.sh dist/exp0000-example.tar.gz
scripts/check-results.py prediction.example.toml test-results/*/run-1
```

The last command checks the local run against [`prediction.example.toml`](prediction.example.toml): the same counts and checksums every time, on any host. To make it your experiment, follow [the guide](docs/guide.md).

## The path to orbit

```mermaid
flowchart LR
  A[Register at opssat.esa.int] --> B[ESA confirms:<br/>experiment ID and<br/>development environment]
  B --> C[Build and test<br/>locally]
  C --> D[Send the package]
  D --> E[ESA software<br/>environment]
  E --> F[TU Graz FlatSat:<br/>the flight processor<br/>on the bench]
  F --> G[Your go-ahead]
  G --> H[The satellite]
  H --> I[Results back:<br/>check against<br/>your prediction]
```

Each step waits for the one before it to pass, and results come back after each test. For exp4051 it took eleven days from registration to the first run in orbit, and about two days from package to orbit for the next runs ([timeline](docs/exp4051.md)).

## The rules on one screen

As we met them in October 2026 (ESA's experiment environment README v0.3, and our introduction meeting with ESA). Check them against what ESA sends you.

- **One `tar.gz`**, all paths relative, every file owned by user and group `exp`.
- **The runner executes `./run`** as user `exp`, in `$HOME`, which holds your files. `run` must be executable and must stay in the foreground until the experiment is done.
- **Everything changed under `$HOME` is sent down.** Write outputs to one folder, such as `toGround/`, and keep the rest clean.
- **Five minutes or less** per run.
- **The target is Alpine Linux 3.21 on 32-bit ARM, hard float, musl libc**: the SEPP, an Altera Cyclone V SoC with two Cortex-A9 cores at 800 MHz and 1 GB of memory. Busybox only: no bash, no Python. Static binaries need nothing from the image.
- **User space only.** Our experiment used no network, no device files and no privileged calls, and kept to 128 MB per process and the CPU share it registered. Agree your own limits with ESA.

More in [docs/rules.md](docs/rules.md).

## Five things that cost us a round trip

1. **Hidden macOS files in the archive.** macOS tar adds `._NAME` entries and its listing hides them. ESA found them in our first package. `package.sh` stops them and `check-package.py` fails on them.
2. **State left from an earlier run.** The FlatSat reused our home folder, so our restart test resumed from an old checkpoint. `run` now removes it first, and `test-local.sh` runs every package twice to catch this.
3. **Emulation is not the SEPP.** The SEPP ran our demo about three times slower per tick than a laptop emulating the same binary. Put your work in counts, not seconds, and give every step a cap.
4. **A time limit checked too rarely.** A long last step can run past the cap. Check the deadline inside long work and never sleep past it.
5. **CPU readings from emulation.** They read both high and low against the SEPP. Only the FlatSat measures the real figure.

All of them, with what to do: [docs/pitfalls.md](docs/pitfalls.md).

## The guide

1. [The guide, step by step](docs/guide.md): registration, design, build, test, package, send, check, reply
2. [Rules of the experiment environment](docs/rules.md)
3. [Testing on the ground](docs/testing.md): the stand-in, ESA's image, the FlatSat, and timing
4. [Writing a prediction](docs/prediction.md)
5. [What comes back, and how to check it](docs/results.md)
6. [Pitfalls](docs/pitfalls.md)
7. [Email templates](docs/emails.md)
8. [exp4051, a worked example](docs/exp4051.md)

## Questions or contributions

Ran an experiment and learned something we missed? Pull requests are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). Email [contact@mru.space](mailto:contact@mru.space).

## License

Code under [Apache License 2.0](./LICENSE). The **Mru** name and mark are trademarks; see [TRADEMARK.md](./TRADEMARK.md). OPS-SAT is a mission of the European Space Agency; OPS-SAT PRETTY is operated by TU Graz. Their names are used here only to say what this template is for.
