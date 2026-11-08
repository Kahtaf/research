# Decision: YES, build this one baseline and run one trial

## 1. Why YES, and what each result would teach

This is the first trial that changes the system as a whole instead of tuning hooks. Every earlier trial ran the full consumer set with more and more instrumentation, and the instrumentation itself (WENT/WRET, the sparse filter, the pwrap budget, uevent omission) could have changed the behaviour it was measuring. This build drops about 99 consumer DT nodes and their drivers, drops all of that instrumentation by going back to the clean ancestor, and runs on CPU0 only. That splits the problem in two:

- **Side A:** the removed consumers plus the instrumentation.
- **Side B:** the retained protection closure plus the core: BAT_thread/AUXADC, SPM/CPU_IDLE/HPS/CPUFreq, PMIC/pwrap, MD32/EMI/ATF, timer/GIC.

**Positive result:** the protection closure and the core can sustain normal userspace compute and timer interrupts on this 4.9 kernel. The earlier stall is then caused by something in Side A. That gives a clear way forward: add consumer groups back in coarse steps, starting from a known-good base. It does not show storage, display or full-OS readiness.

**Negative or no-progress result:** the stall is in Side B, or in something both builds share. That narrows the search but doesn't name a cause. In particular, it can't be called a bare-core failure, because BAT_thread channel 6, the SPM idle path and the HPS/CPUFreq interaction with maxcpus=1 are all still present. Of these, deep idle not waking on the timer is the most plausible suspect, and this design keeps it on purpose.

## 2. Is it different enough?

Yes. Keeping the known suspects makes it weaker as a root-cause experiment. It is not weaker as a partition, and a partition is what's needed after a run of trials that taught nothing. Accept two honest limits rather than designing around them:

- With nr_cpus=1, HPS still runs its hotplug policy against a CPU mask that is now different. That is a confound, not a blocker.
- The retained buffer may fill with vendor logs, so a negative result may come back unlocalised. That stays a declared UNKNOWN.

One requirement, which is part of the design rather than a new variant: the helper must write a short stage marker through /dev/kmsg at each point (start, checksum done, each of the 5 timer returns, before reboot). That way a partial run can be read in the retained buffer instead of looking the same as no run at all. If the helper already logs this way, nothing changes.

If a negative comes back, the boundary decision for the owner is a single question: **authorise changes inside the protection closure under manual power supervision, or end the 4.9 bring-up path.** For example, that could mean turning off SPM deep idle states, or gating BAT_thread while the owner watches temperature and can cut power. This is the owner's call. It is not something I can infer.

## 3. What counts as a pass

Confirmed, with one addition:

- The real 2M checksum matches the independently computed value.
- All 5 SIGALRM/sigsuspend returns happen.
- Both CLOCK_MONOTONIC and the CPU0 timer IRQ total (PPI 29+30) increase on every cycle.
- The helper triggers a normal reboot.
- **Added:** after that reboot, stock Android 7 is verified to boot normally from the intact BOOT/SYSTEM/DATA partitions.

A pass means the device is alive in normal RAM with interrupts working. It does not mean calibrated wall time, working storage, or OS readiness.

Build once and run once. If the result is negative or ambiguous, stop and take the question in section 2 to the owner. Don't re-tune, don't add hooks, and don't conclude "end 4.9 because the bare core failed." This build doesn't test a bare core, so its result can't support that conclusion.