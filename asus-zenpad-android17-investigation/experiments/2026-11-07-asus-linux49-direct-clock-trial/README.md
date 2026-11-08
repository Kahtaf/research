# One explicit clock-syscall physical control

Question: does the finite runnable clock loop complete when every clock read explicitly calls SYS_clock_gettime, bypassing vDSO?

Status: fresh stock identity and owner nearby Power confirmed. One exact recovery installation and one entry pending. Same kernel/bootargs/handler/bounds; corrected GIC-0 parsing adds observational output. New helper UUID f0c3c82c-d639-4d8a-90f2-155fd4224ceb. Require explicit path marker, actual counter/IRQ observations, loop and alarm outcomes and different returned stock boot. No normal OS partition changes. If same boundary remains, use kernel-side checkpoints next rather than another userspace variant.
