# Contributing

Thank you for your interest. This template is what one experimenter learned on OPS-SAT PRETTY. If you ran an experiment and found something it misses, a rule that changed, or a pitfall we did not hit, tell us and the next team gains from it.

This repository does not take pull requests or issues. Email [contact@mru.space](mailto:contact@mru.space) instead.

## What helps most

- **What happened**: the step (registration, packaging, sandbox, FlatSat, orbit, results), what you expected and what you saw.
- **The source and date**: an ESA document and its version, an email from ESA (the gist, not the address), or a run you can point to.
- **The evidence**, if you can share it: a `run-info.txt`, a journal line, a result archive, a command and its output.
- **A fix**, if you have one: a patch or a diff in the email is welcome.

Every number in the docs comes from a real run, with its scope, and every rule names its source. Where ESA's documents and this guide differ, ESA is right, and the guide gets fixed. With your permission, we credit you in the change.

Please do not send us ESA's environment image, README or other documents. They are ESA's, and they stay out of this repository.

## If you change the template in your own copy

These are the checks CI runs:

```sh
shellcheck -s sh template/run scripts/*.sh tests/harness.sh
python3 -m unittest discover -s tests
tests/harness.sh sh                        # and "busybox sh" if you have it
scripts/build-example.sh
scripts/package.sh -n exp0000-example template/run build/workload template/README.txt LICENSE
scripts/test-local.sh dist/exp0000-example.tar.gz
scripts/check-results.py prediction.example.toml test-results/*/run-1
```

Keep `template/run` in POSIX sh: it must run under busybox on the SEPP.

The code is under the [Apache License 2.0](LICENSE).
