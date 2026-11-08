#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <sched.h>
#include <signal.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <sys/time.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <time.h>
#include <unistd.h>

#include "run_identity.h"

_Static_assert(sizeof(unsigned int) == 4, "32-bit unsigned workload required");
static int kmsg = -1;
static volatile sig_atomic_t alarm_seen;

static int report(const char *format, ...)
{
    char line[512];
    va_list ap;
    int n, prefix;
    ssize_t written;

    prefix = snprintf(line, sizeof(line), "<6>ASUS-MINPLAT run=%s ", RUN_UUID);
    if (prefix < 0 || (size_t)prefix >= sizeof(line))
        return -1;
    va_start(ap, format);
    n = vsnprintf(line + prefix, sizeof(line) - (size_t)prefix, format, ap);
    va_end(ap);
    if (n < 0 || (size_t)n >= sizeof(line) - (size_t)prefix - 1)
        return -1;
    n += prefix;
    line[n++] = '\n';
    do {
        written = write(kmsg, line, (size_t)n);
    } while (written < 0 && errno == EINTR);
    return written == n ? 0 : -1;
}

static void finish(int success, const char *operation, int error)
    __attribute__((noreturn));

static void finish(int success, const char *operation, int error)
{
    const struct itimerval off = { 0 };
    int saved;

    setitimer(ITIMER_REAL, &off, NULL);
    report("event=%s operation=%s errno=%d next=normal-reboot",
           success ? "success" : "error", operation, error);
    reboot(RB_AUTOBOOT);
    saved = errno;
    report("event=error operation=reboot-returned errno=%d fallback=manual-Power",
           saved);
    for (;;)
        pause();
}

static void require(int condition, const char *operation)
{
    if (!condition)
        finish(0, operation, errno ? errno : EPROTO);
}

static void on_alarm(int signal_number)
{
    (void)signal_number;
    alarm_seen = 1;
}

static int timer_irqs(uint64_t *value)
{
    FILE *file = fopen("/proc/interrupts", "re");
    char line[512], *colon, *end;
    char controller[32], trigger[16], name[32], extra;
    unsigned long long count;
    unsigned hwirq, seen = 0, rows = 0;
    uint64_t total = 0;
    int error = 0;

    if (!file)
        return -1;
    if (!fgets(line, sizeof(line), file) || !strstr(line, "CPU0") ||
        strstr(line, "CPU1")) {
        error = EPROTO;
        goto out;
    }
    while (fgets(line, sizeof(line), file)) {
        if (++rows > 256 || !strchr(line, '\n')) {
            error = EOVERFLOW;
            goto out;
        }
        if (!strstr(line, "arch_timer") && !strstr(line, "arch_mem_timer"))
            continue;
        colon = strchr(line, ':');
        if (!colon) {
            error = EPROTO;
            goto out;
        }
        errno = 0;
        count = strtoull(colon + 1, &end, 10);
        if (errno || end == colon + 1 ||
            sscanf(end, " %31s %u %15s %31s %c", controller, &hwirq,
                   trigger, name, &extra) != 4 ||
            strcmp(controller, "GIC-0") ||
            (hwirq != 29 && hwirq != 30) ||
            strcmp(trigger, "Level") ||
            (strcmp(name, "arch_timer") && strcmp(name, "arch_mem_timer")) ||
            (seen & (1U << (hwirq - 29))) ||
            UINT64_MAX - total < (uint64_t)count) {
            error = EPROTO;
            goto out;
        }
        seen |= 1U << (hwirq - 29);
        total += (uint64_t)count;
    }
    if (ferror(file))
        error = EIO;
    else if (!seen)
        error = ENOENT;
out:
    if (fclose(file) && !error)
        error = errno;
    if (error) {
        errno = error;
        return -1;
    }
    *value = total;
    return 0;
}

int main(void)
{
    struct utsname identity;
    struct sched_param scheduling;
    struct sigaction action = { 0 };
    struct timespec before, after;
    sigset_t block, old_mask, wait_mask;
    const struct itimerval one_second = { .it_value = { .tv_sec = 1 } };
    volatile unsigned int state = 0x12345678U;
    volatile unsigned long long checksum = 0;
    unsigned int i, cycle;
    uint64_t irq_before, irq_after;
    int policy, nice_value;

    /* The unpacked initramfs root is RAM. There is no storage or udev setup. */
    if (mkdir("/dev", 0755) && errno != EEXIST)
        finish(0, "mkdir-dev", errno);
    if (mknod("/dev/kmsg", S_IFCHR | 0600, makedev(1, 11)) && errno != EEXIST)
        finish(0, "mknod-kmsg", errno);
    kmsg = open("/dev/kmsg", O_WRONLY | O_CLOEXEC);
    require(kmsg >= 0, "open-kmsg");
    require(report("event=entry pid=%ld", (long)getpid()) == 0, "entry-write");
    errno = 0;
    require(getpid() == 1, "pid1");
    require(uname(&identity) == 0, "uname");
    require(report("event=uname sysname=%s release=%s version=%s machine=%s",
                   identity.sysname, identity.release, identity.version,
                   identity.machine) == 0, "uname-write");

    policy = sched_getscheduler(0);
    require(policy >= 0, "sched-get-policy");
    require(sched_getparam(0, &scheduling) == 0, "sched-get-param");
    errno = 0;
    nice_value = getpriority(PRIO_PROCESS, 0);
    require(errno == 0, "getpriority");
    require(report("event=scheduler policy=%d priority=%d nice=%d",
                   policy, scheduling.sched_priority, nice_value) == 0,
            "scheduler-write");
    errno = 0;
    require(policy == SCHED_OTHER && scheduling.sched_priority == 0 &&
            nice_value == 0, "normal-priority");

    if (mkdir("/proc", 0555) && errno != EEXIST)
        finish(0, "mkdir-proc", errno);
    require(mount("proc", "/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC,
                  NULL) == 0, "mount-proc");
    require(sysconf(_SC_NPROCESSORS_ONLN) == 1, "one-online-cpu");
    require(report("event=compute-begin iterations=2000000") == 0,
            "compute-begin-write");
    for (i = 0; i < 2000000U; i++) {
        state = state * 1664525U + 1013904223U;
        checksum = checksum + state;
    }
    require(report("event=compute-end iterations=%u state=%08x checksum=%llu",
                   i, (unsigned int)state, (unsigned long long)checksum) == 0,
            "compute-end-write");
    errno = 0;
    require(state == EXPECTED_STATE && checksum == EXPECTED_CHECKSUM,
            "compute-checksum");

    action.sa_handler = on_alarm;
    sigemptyset(&action.sa_mask);
    require(sigaction(SIGALRM, &action, NULL) == 0, "sigaction");
    sigemptyset(&block);
    sigaddset(&block, SIGALRM);
    require(sigprocmask(SIG_BLOCK, &block, &old_mask) == 0, "block-alarm");
    wait_mask = old_mask;
    sigdelset(&wait_mask, SIGALRM);
    for (cycle = 1; cycle <= 5; cycle++) {
        require(timer_irqs(&irq_before) == 0, "timer-irqs-before");
        require(syscall(SYS_clock_gettime, CLOCK_MONOTONIC, &before) == 0, "monotonic-before");
        require(report("event=timer-before cycle=%u irq=%" PRIu64
                       " monotonic=%lld.%09ld requested_interval=1s",
                       cycle, irq_before, (long long)before.tv_sec,
                       before.tv_nsec) == 0, "timer-before-write");
        alarm_seen = 0;
        require(setitimer(ITIMER_REAL, &one_second, NULL) == 0, "arm-alarm");
        while (!alarm_seen) {
            errno = 0;
            if (sigsuspend(&wait_mask) != -1 || errno != EINTR)
                finish(0, "sigsuspend", errno ? errno : EPROTO);
        }
        require(syscall(SYS_clock_gettime, CLOCK_MONOTONIC, &after) == 0, "monotonic-after");
        require(timer_irqs(&irq_after) == 0, "timer-irqs-after");
        require(report("event=timer-return cycle=%u signal=SIGALRM irq=%" PRIu64
                       " irq_before=%" PRIu64 " monotonic=%lld.%09ld",
                       cycle, irq_after, irq_before, (long long)after.tv_sec,
                       after.tv_nsec) == 0, "timer-return-write");
        errno = 0;
        require(irq_after > irq_before &&
                (after.tv_sec > before.tv_sec ||
                 (after.tv_sec == before.tv_sec && after.tv_nsec > before.tv_nsec)),
                "timer-observations");
    }
    require(sigprocmask(SIG_SETMASK, &old_mask, NULL) == 0, "restore-signal-mask");
    finish(1, "five-timer-returns", 0);
}
