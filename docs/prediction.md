# Writing a prediction

Write down what the run will produce before it runs, and send it with the package. Then the result is evidence, not a story told afterwards. It also makes your own check quick: the files either match or they do not.

## What to predict exactly, and what as a range

| Decided by | Examples | Predict |
|---|---|---|
| Your code | counts, checksums, which event happens at which tick, exit codes, how a step ends | exactly |
| The host | wall time, CPU share, memory, ticks done inside a time cap | a range, with the reason |

If your work is in counts (see [the guide](guide.md#3-design-for-the-window)), most of what matters is decided by your code, and the prediction can be exact on every host.

## The file

`scripts/check-results.py` reads a TOML prediction. [`prediction.example.toml`](../prediction.example.toml) is the one for the example package:

```toml
[run]                          # the last line of run-info.txt
status = 0
seconds = { max = 270 }

[steps.baseline]               # the "baseline: exit=..." line of run-info.txt
exit = 0

[files."summary-baseline.txt"] # key=value pairs in that file
ticks = 20000
stopped = "done"
checksum = "b69fb37f92117726"
run_share = { max = 5.1 }
```

Check it on your local run first; it must pass there before it means anything in orbit:

```sh
scripts/check-results.py prediction.toml test-results/*/run-1
scripts/check-results.py prediction.toml pack-NNNN_TIMESTAMP.tar.gz   # what ESA sends back
```

## In the email

Put the main numbers in plain words in the email that carries the package, for example:

> For the record before the run: zero wrong results in every segment; about 340 correct results in segment 1, with the quorum down to its last replica; 239 for fixed triple redundancy, then a detected disagreement on every cycle; and one restore in segment 3, with the retired replica still retired.

That was the prediction for our run 3. In orbit: 342, 0 wrong; 239, then a detected disagreement on every cycle; one restore, the retired replica still retired.

## When a prediction can go two ways

Say so before the run. On our run 3, a rule in our code could withhold one cycle at a planned kill if the processor was busy at that moment. It did on the FlatSat and did not in orbit; the counts were the same either way, and we had predicted the counts, not the cycle. Predict what holds in both cases.

## Keep a scorecard

After the run, list each predicted item with what came down. For our run 1: the same events on the same ticks (yes), about 2,700 correct for the shrinking quorum (2,745), 239 for fixed triple redundancy (239), zero wrong (0), about 225 seconds (227), no unexpected upset line (none).
