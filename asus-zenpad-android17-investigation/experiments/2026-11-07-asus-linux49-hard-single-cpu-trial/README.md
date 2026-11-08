# Single hard-CPU-limit recovery trial

Question: does the direct-clock control finish with a confirmed one-CPU possible/online topology?

Status: one trial prepared from fresh stock identity under the active nearby Power confirmation. Only maxcpus=1 becomes nr_cpus=1. Kernel/helper/hardware DT identical. Verify actual token and IRQ column count, counter/alarm/loop results and fresh stock return. No normal Android partitions changed.

## Result

Actual nr_cpus=1 reached Linux, core setup clipped to one, and both timer IRQ records have one CPU column (PPI29=0,PPI30=178 before observation). The explicit kernel clock read returned0.641996461s, followed by no loop completion/after snapshot/alarm marker. Stock Android returned verified. One confirmed online CPU is sufficient to reproduce; do not add another topology/clocksource guess. Next unit is bounded kernel-side capture using the existing retained-console path.
