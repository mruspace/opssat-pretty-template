# What comes back, and how to check it

## How it arrives

For our runs, after each test ESA emailed a link to a shared folder. **The link was valid for three days**: download at once. The folder held a zip with one archive per test:

| Archive | From |
|---|---|
| `pack-flatsat-NNNN_TIMESTAMP.tar.gz` | the FlatSat (host `sepp` in our runs) |
| `pack-NNNN_TIMESTAMP.tar.gz` | the satellite (host `sepp1` in our runs) |

`NNNN` is your experiment ID. In all six of our archives `TIMESTAMP` was the Unix time the run ended, to within a second. The software environment test passed each time, but its files did not always come with the results.

## Inside

```
log                    the SEPP's journal lines for your run
chg/toGround/...       what your run changed under $HOME: your outputs
```

The journal shows the runner around your run, for example:

```
Oct 28 09:12:59 sepp1 systemd[1]: Starting Experiment NNNN...
Oct 28 09:12:59 sepp1 spawn[2692]: starting experiment NNNN
Oct 28 09:12:59 sepp1 systemd[1]: Started Experiment NNNN.
Oct 28 09:15:29 sepp1 systemd-machined[2715]: Machine exp-NNNN terminated.
```

A process your experiment kills on purpose can show here as a "Killed" line. Name it in your operator note so nobody reads it as a failure.

## Check it

```sh
scripts/check-results.py prediction.toml pack-NNNN_TIMESTAMP.tar.gz
```

It prints the journal, the files, and one line per predicted value, and exits 1 if anything differs. Then read the files yourself: the checker checks what you predicted, and you should look for what you did not.

Check also:

- the checksums in `run-info.txt` against the files you sent, so you know which build ran;
- the host (`sepp` or `sepp1`) and the processor in `run-info.txt`, so you know where it ran;
- the start and end times and exit codes of every step.

## Dates

Use the SEPP's clock in `run-info.txt` as the record of when your run happened. For two of our runs it showed a time before our go-ahead email; treat it as the record of the run, not as proof of the order of emails.

## Reply

Reply on the same thread: the result in numbers, matched or not, and why. If you want another run, ask for it here, once. If you publish, say so in one line and credit the ESA OPS-SAT Space Lab and TU Graz. [docs/emails.md](emails.md) has a template.
