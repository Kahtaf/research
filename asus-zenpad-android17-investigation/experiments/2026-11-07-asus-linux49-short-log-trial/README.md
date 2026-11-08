# Single shortened diagnostic-command-line trial

Question: does complete printk.devkmsg=on reach the kernel and expose the suppressed helper observations?

Status: preparing one exact container installation then one recovery entry under active nearby Power confirmation. Same helper and kernel; unused Android-init argument removed to keep all real kernel flags and fit a conservative short header. No normal Android partition changes, driver changes, block opens or storage writes. Require actual kernel command-line confirmation and complete new retained output.

## Result

Actual kernel command line contained complete printk.devkmsg=on. The same helper emitted 76 records, resolving the ten-record truncation confounder. uname, proc/sysfs mounts, both bounded directory enumerations, clock_gettime and alarm(10) returned. mmc0/mmc1 controllers exist, but mmcblk0/mmcblk1 were absent at initial monotonic0.665806s; this early snapshot does not establish terminal storage failure. The last record is begin of relative100ms CLOCK_MONOTONIC clock_nanosleep. No return, alarm handler, or completion was recorded. Stock Android returned with a verified different boot ID. First focused boundary is timer interrupt/wake; no speculative watchdog or clock-rate change is justified yet.
