Experiment expNNNN on OPS-SAT PRETTY: <one-line title>
Contact: <your email>

What it is: <two or three sentences an operator can read in thirty seconds:
what runs, what it computes, what it shows.>

How to run: ./run, in the foreground, as user exp, in this folder. It stops
by itself after about <N> seconds, under five minutes in total. Stop it early
with SIGTERM: the running step ends cleanly and its summary is written.

What it touches: user space only. No network, no device files, no reboots,
no privileged calls. At most <N> processes at a time. Memory limit <N> MB per
process (RLIMIT_AS), set by the processes themselves. CPU share <N>% of one
core. Storage: about <N> kB for the package, a few kilobytes of output.

Output, all in toGround/: run-info.txt (start and end times, host, processor,
checksums of the package files, exit code of every step), and per step
summary-NAME.txt and stdout-NAME.txt.

Expected lines that are not errors: <for example "Killed" in the journal for
a planned kill, or a library warning you have seen in testing.>

Source and documentation: <link to your repository>
