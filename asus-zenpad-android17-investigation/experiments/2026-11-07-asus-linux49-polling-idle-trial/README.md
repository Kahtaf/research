# One same-kernel polling-idle trial

Question: does the same 100ms blocking sleep return when nohlt bypasses the normal low-power idle entry path?

Status: fresh stock baseline recorded, one exact recovery-only install/entry pending. Same helper/kernel; only nohlt added. Existing nearby Power fallback authorization persists in this active session. Require actual full nohlt command-line token, exact container installation and new stock boot transition. No everyday power behavior claim; tick_nohz_idle_enter still runs. Normal Android partitions unchanged.

## Result

Exact install/readback and cleanup verified; one acknowledged entry returned to a different stock boot. Actual nohlt and printk.devkmsg=on tokens reached Linux. The same 76 helper records ended at clock_nanosleep begin, without return, alarmhandler or completion. Normal hardware-idle entry is not necessary to reproduce this boundary; NO_HZ bookkeeping remains. Do not add another guessed boot flag. Next unit should observe timer IRQ delivery and a signal while the helper remains runnable, using the unchanged kernel.
