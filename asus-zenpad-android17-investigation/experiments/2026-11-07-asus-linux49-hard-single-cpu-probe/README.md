# Enforce the intended single-core control

Question: does the unchanged direct-clock observation finish when only CPU0 can be brought online?

Status: one boot-argument candidate packaged; default parent PLAN passed. Prior actual IRQ table showed two online CPUs despite maxcpus=1. Kernel source kernel/smp.c:513-523 defines nr_cpus as a hard limit; ARM64 smp.c:693 sets up secondaries only below nr_cpu_ids; cpu_up rejects non-possible CPUs. Replace only maxcpus=1 with nr_cpus=1 in both short argument strings. No kernel or helper code changes, hardware DT changes, driver writes or normal OS changes.

This corrects a newly measured CPU-topology confounder, rather than repeating another userspace clock variant. Require nr_cpus token and one actual CPU-count column in the complete new log before interpretation. Reused helper UUID is not standalone freshness evidence; bind exact full container and new stock boot transition. If it still stalls with one confirmed CPU, stop topology/boot-flag variants and use the bounded kernel-side capture.
