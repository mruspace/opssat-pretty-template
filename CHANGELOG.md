# Changelog

All notable changes to the OPS-SAT PRETTY experiment template. Versions follow [Semantic Versioning](https://semver.org).

## 0.1.0 (2026-10-29)

### Added

- `template/run`: the entry point for ESA's runner, in POSIX sh. Steps with caps (`step`), a planned kill (`step_kill`), a budget for the whole run, removal of output and state left by an earlier run, a record of host, processor, package checksums, times and exit codes in `run-info.txt`, a stop request passed on, no process left behind.
- `template/README.txt`: the operator note.
- `example/workload.c`: a deterministic example experiment in counts, with a time cap checked inside the loop, a CPU share, a memory limit, a clean stop on SIGTERM and CPU time by phase.
- `scripts/build-example.sh`, `scripts/package.sh`, `scripts/check-package.py`, `scripts/test-local.sh` (two runs in the same folder, in an Alpine armhf container or ESA's image), `scripts/check-results.py` (against a TOML prediction, reading ESA's result archives directly), `prediction.example.toml`.
- Docs: the guide, the rules, testing, predictions, results, pitfalls, email templates, and the exp4051 timeline.
- CI: shellcheck, tests of the package checker, the harness under sh, dash and busybox sh, and the full example on 32-bit ARM checked against its prediction.
- Tested on October 29, 2026, in ESA's OPS-SAT PRETTY experiment environment image (v0.3) on a laptop under emulation: both runs exit 0 (27 s and 41 s), the same checksums as in the Alpine stand-in, CPU share 5.00% in every step.
