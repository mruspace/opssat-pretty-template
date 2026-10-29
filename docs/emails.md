# Email templates

Short, plain, one ask per email. Use ESA's subject tag (for example `[expNNNN]`) and copy the addresses ESA names in every email; reply on the same thread. Fill in everything in angle brackets.

## Sending a package

> Subject: <title> package [expNNNN]
>
> Dear <name>,
>
> The package for <experiment> is attached: <file name> (<size>). <One sentence: what it does.>
>
> What runs: ./run in the foreground as user exp, in the home folder. <Steps, one line each, with their caps.> It stops by itself after about <N> seconds.
>
> What it touches: user space only, no network, no device files. At most <N> processes, <N> MB per process, <N>% CPU, set by the processes themselves. Everything it writes goes to toGround/, a few kilobytes.
>
> Expected lines that are not errors: <for example "Killed" for the planned kill at 35 s>.
>
> Tested full length in your environment image: <N> s, every step exited as planned.
>
> For the record before the run: <the prediction in one or two sentences, with the numbers>.
>
> Best regards,
> <name>

## Replying to the FlatSat results

> Dear <name>,
>
> Thank you. Please go ahead with the spacecraft run when you're ready, with the same package.
>
> We've checked the FlatSat results and they match the prediction: <the main numbers>. <One line on anything that differed, and why it needs nothing from you.>
>
> Best regards,
> <name>

If something must change, say exactly what, and whether the validated package can fly as it is.

## Replying to the results from orbit

> Dear <name>,
>
> Many thanks! We've checked the flight results: <matched / what differed>.
>
> <The main numbers, two or three sentences, the same items as the prediction.>
>
> <One ask, if any: another short run and what it would add, or a question.>
>
> p.s. We've published the results on our site, with credit to the ESA OPS-SAT Space Lab and TU Graz.
>
> Best regards,
> <name>

## What to leave out

- Checksums (they are in `README.txt` and `run-info.txt`).
- CPU shares measured under emulation.
- More than one ask.
- Requests for ESA to review what you publish about your own experiment. Credit them, and send them the link.
