# One controlled nohlt timer-wake experiment

Question: does the unchanged RAM helper return from 100ms CLOCK_MONOTONIC sleep when generic idle polling bypasses CPU low-power entry?

Status: one controlled candidate being prepared. Only nohlt is appended to both short header and chosen bootargs; preserve complete printk.devkmsg=on. Same compressed/raw kernel, complete helper ramdisk, hardware DT, initrd bounds and all other arguments. Normal Android partitions unchanged.

Source basis: ARM64 selects GENERIC_IDLE_POLL_SETUP (resolved config line222); kernel/sched/idle.c:44-50 registers nohlt, :245-248 selects polling before cpuidle_idle_call, :60-68 polls with interrupts enabled. MT8163 deep-idle state carries CPUIDLE_FLAG_TIMER_STOP. This bypasses governor and architectural idle fallback; tick_nohz_idle_enter still executes. A positive narrows idle/timer-wake interaction, not a specific driver fix. A negative requires event-delivery observation rather than another guessed flag.

Single trial only. Verify actual nohlt in the new kernel command line and exact new container readback, different returned stock boot, and complete retained log. Same helper UUID intentionally reused, not independent freshness evidence. Nearby Power fallback required. This is a short diagnostic, not a proposed everyday power configuration.
