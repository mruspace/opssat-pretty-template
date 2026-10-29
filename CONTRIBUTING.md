# Contributing

Thank you for your interest. This template is what one experimenter learned on OPS-SAT PRETTY. If you ran an experiment and found something it misses, a rule that changed, or a pitfall we did not hit, a pull request helps the next team. For questions, email contact@mru.space.

## Before you open a pull request

Run the same checks as CI:

```sh
shellcheck -s sh template/run scripts/*.sh tests/harness.sh
python3 -m unittest discover -s tests
tests/harness.sh sh                        # and "busybox sh" if you have it
scripts/build-example.sh
scripts/package.sh -n exp0000-example template/run build/workload template/README.txt LICENSE
scripts/test-local.sh dist/exp0000-example.tar.gz
scripts/check-results.py prediction.example.toml test-results/*/run-1
```

## Rules for changes

- `main` is protected. Make every change through a branch and a pull request.
- `template/run` stays POSIX sh: it must run under busybox on the SEPP.
- A rule in the docs names its source and date (ESA's README and version, an email, or a run you can point to). Where ESA's documents and this guide differ, ESA is right, and the guide gets fixed.
- Every number in the docs comes from a real run, with its scope.
- Do not add ESA's environment image, README or other documents to the repository. Link to ESA instead.

By contributing, you agree that your contribution is licensed under the [Apache License 2.0](LICENSE).
