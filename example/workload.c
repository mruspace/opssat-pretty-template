/*
 * workload: a small example experiment for OPS-SAT PRETTY.
 *
 * It does a fixed amount of deterministic work, one "tick" at a time, at a
 * capped share of one CPU, and writes a key=value summary that the ground
 * can check against a prediction. Replace the body of tick() with your own
 * work; keep the rest, which is what makes a run predictable and safe:
 *
 *   - the work is counted in ticks, not seconds, so the result is the same
 *     on a laptop, ESA's sandbox and the satellite, which run at different
 *     speeds;
 *   - a time cap (--max-seconds) checked inside the tick loop, never slept
 *     past, so the program stops on time even if the host is slow;
 *   - a CPU share (--cpu-percent) kept by sleeping after each tick;
 *   - a memory limit set by the process on itself (RLIMIT_AS);
 *   - SIGTERM and SIGINT end the run cleanly, with the summary written;
 *   - CPU time reported by phase (start-up, run, end), user and kernel apart.
 *
 * Build it static for the SEPP (32-bit ARM, hard float, musl): see
 * scripts/build-example.sh.
 *
 * Usage: workload [--ticks N] [--max-seconds S] [--cpu-percent P]
 *                 [--memory-mb M] [--seed X] [--summary FILE]
 */
#define _GNU_SOURCE
#include <errno.h>
#include <inttypes.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

#define BLOCK_WORDS 1024 /* 8 KiB of working memory per tick */

static volatile sig_atomic_t stop_requested = 0;

static void on_signal(int sig) {
    (void)sig;
    stop_requested = 1;
}

static double now_s(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
}

struct cpu {
    double user, sys;
};

static struct cpu cpu_now(void) {
    struct rusage u;
    getrusage(RUSAGE_SELF, &u);
    struct cpu c = {
        (double)u.ru_utime.tv_sec + (double)u.ru_utime.tv_usec / 1e6,
        (double)u.ru_stime.tv_sec + (double)u.ru_stime.tv_usec / 1e6,
    };
    return c;
}

/* splitmix64: a small, well-known generator; the same seed gives the same
 * numbers on every host. */
static uint64_t next(uint64_t *s) {
    uint64_t z = (*s += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

/* One tick of work: fill a block from the generator and fold it into the
 * running checksum (FNV-1a over the words). Deterministic: the checksum after
 * N ticks depends only on the seed and N. */
static uint64_t tick(uint64_t *state, uint64_t *block, uint64_t checksum) {
    for (int i = 0; i < BLOCK_WORDS; i++) {
        block[i] = next(state);
    }
    for (int i = 0; i < BLOCK_WORDS; i++) {
        checksum ^= block[i];
        checksum *= 0x100000001b3ULL;
    }
    return checksum;
}

/* Sleep for s seconds, but never past the deadline, and wake on a signal. */
static void sleep_until_at_most(double s, double deadline) {
    double left = deadline - now_s();
    if (s > left) {
        s = left;
    }
    if (s <= 0) {
        return;
    }
    struct timespec t = {(time_t)s, (long)((s - (double)(time_t)s) * 1e9)};
    while (nanosleep(&t, &t) == -1 && errno == EINTR && !stop_requested) {
    }
}

static long arg_long(const char *name, const char *v) {
    char *end;
    errno = 0;
    long x = strtol(v, &end, 10);
    if (errno || *end || x < 0) {
        fprintf(stderr, "workload: bad value for %s: %s\n", name, v);
        exit(2);
    }
    return x;
}

int main(int argc, char **argv) {
    double t_start = now_s();
    struct cpu c_start = cpu_now();

    long ticks = 2000, max_seconds = 60, cpu_percent = 5, memory_mb = 128;
    uint64_t seed = 1;
    const char *summary_path = "toGround/summary.txt";
    for (int i = 1; i < argc; i++) {
        const char *a = argv[i];
        const char *v = (i + 1 < argc) ? argv[i + 1] : NULL;
        if (!v) {
            fprintf(stderr, "workload: %s needs a value\n", a);
            return 2;
        }
        if (!strcmp(a, "--ticks")) ticks = arg_long(a, v);
        else if (!strcmp(a, "--max-seconds")) max_seconds = arg_long(a, v);
        else if (!strcmp(a, "--cpu-percent")) cpu_percent = arg_long(a, v);
        else if (!strcmp(a, "--memory-mb")) memory_mb = arg_long(a, v);
        else if (!strcmp(a, "--seed")) seed = (uint64_t)arg_long(a, v);
        else if (!strcmp(a, "--summary")) summary_path = v;
        else {
            fprintf(stderr, "workload: unknown option %s\n", a);
            return 2;
        }
        i++;
    }
    if (cpu_percent < 1 || cpu_percent > 100) {
        fprintf(stderr, "workload: --cpu-percent must be 1 to 100\n");
        return 2;
    }

    /* The memory limit, set by the process on itself. The kernel refuses
     * any allocation above it. */
    struct rlimit lim = {(rlim_t)memory_mb << 20, (rlim_t)memory_mb << 20};
    if (setrlimit(RLIMIT_AS, &lim) != 0) {
#ifdef __linux__
        perror("workload: setrlimit");
        return 2;
#else
        /* macOS does not enforce RLIMIT_AS; the SEPP runs Linux, which does. */
        fprintf(stderr, "workload: memory limit not supported on this host, continuing\n");
#endif
    }

    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_signal;
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGHUP, &sa, NULL);

    FILE *out = fopen(summary_path, "w");
    if (!out) {
        fprintf(stderr, "workload: cannot write %s: %s\n", summary_path, strerror(errno));
        return 2;
    }
    uint64_t *block = calloc(BLOCK_WORDS, sizeof *block);
    if (!block) {
        fprintf(stderr, "workload: out of memory\n");
        return 2;
    }

    /* The deadline counts from process start, so the cap is the whole life
     * of the process, start-up included. */
    double deadline = t_start + (double)max_seconds;
    double t_run = now_s();
    struct cpu c_run = cpu_now();

    uint64_t state = seed, checksum = 0xcbf29ce484222325ULL;
    long done = 0;
    const char *stopped = "done";
    double work_s = 0;
    while (done < ticks) {
        if (stop_requested) {
            stopped = "signal";
            break;
        }
        if (now_s() >= deadline) {
            stopped = "time-limit";
            break;
        }
        double t0 = now_s();
        checksum = tick(&state, block, checksum);
        done++;
        double w = now_s() - t0;
        work_s += w;
        /* Keep the share: after w seconds of work, rest w * (100 / P - 1). */
        sleep_until_at_most(w * (100.0 / (double)cpu_percent - 1.0), deadline);
    }

    double t_end = now_s();
    struct cpu c_end = cpu_now();
    double run_wall = t_end - t_run;
    double run_cpu = (c_end.user - c_run.user) + (c_end.sys - c_run.sys);

    struct rusage u;
    getrusage(RUSAGE_SELF, &u);
    fprintf(out, "ticks=%ld planned=%ld stopped=%s seed=%" PRIu64 " checksum=%016" PRIx64 "\n",
            done, ticks, stopped, seed, checksum);
    fprintf(out, "wall=%.3fs startup_wall=%.3fs run_wall=%.3fs work=%.3fs\n",
            t_end - t_start, t_run - t_start, run_wall, work_s);
    fprintf(out,
            "cpu: startup_user=%.3fs startup_system=%.3fs run_user=%.3fs run_system=%.3fs run_share=%.2f%%\n",
            c_run.user - c_start.user, c_run.sys - c_start.sys, c_end.user - c_run.user,
            c_end.sys - c_run.sys, run_wall > 0 ? 100.0 * run_cpu / run_wall : 0.0);
    fprintf(out, "limits: cpu_percent=%ld memory_mb=%ld max_seconds=%ld max_rss=%ldKiB\n",
            cpu_percent, memory_mb, max_seconds, u.ru_maxrss);
    /* The end phase: anything after this line (closing files, freeing
     * memory) is not counted. Keep it short. */
    fclose(out);
    free(block);
    return (strcmp(stopped, "signal") == 0) ? 0 : (done == ticks ? 0 : 3);
}
