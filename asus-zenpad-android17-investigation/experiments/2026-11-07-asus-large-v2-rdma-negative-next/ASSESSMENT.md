# Parent decision

Adopt one bounded scheduler-switch observation at finish_task_switch, preserving the RDMA-negative candidate and unchanged helper. No timer, IRQ route, scheduler policy, PMIC/thermal, bootargs or DT fix.

Corrections to Large’s interpretation: historical completed IRQ rows do not prove delivery continued after the latest task boundary; a latest-record snapshot alone cannot prove a permanent wedge. A switch to PID1 proves kernel context selection, not return to userspace. No resumption in a finite or wrapped ring does not prove indefinite starvation. Preserve latest PID1-out/in slots as well as a bounded latest-switch ring, explicit chronology/generations and loss status. Do not fit new records by overwriting any existing5952-byte capture area. Use separate guarded console space and bound reservation/decoder. Do not add a shared lock under rq lock; single-CPU/IRQ-disabled admission and separate writer discipline must be actual. No blind retry on UNKNOWN.

The next experiment remains the scheduler seam only. It must identify next PID/comm/effective priority/state and record raw counter/ordering without calling timekeeping, printk, allocation or sleeping. Existing clock snapshot and helper remain unchanged. One candidate, one build, one physical trial; stop for interpretation.
