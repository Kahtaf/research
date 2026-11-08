# Cached stock LAST PC capture

Question: does the stock boot-time cached reboot-reason report retain a useful numeric address from the failed recovery trial?

Status: one bounded USB read is being performed. The source-qualified proc route copies cached data; its reset epoch remains unproven. No reboot, image write, direct register read, or debug activation. Raw report/helper output stays in ignored private; public evidence contains capture status and numeric LAST PC lines only.

Continuation: inspect evidence/capture.json; resolve candidate numeric addresses against actual images with origin uncertainty preserved. Never infer previous-kernel execution from a stock symbol label alone.

The actual cached report yielded core0 PC `0xffffff8008f31adc`. Exact current vmlinux resolves this to `serial8250_early_in+0x78`, instruction `ldr w0,[x0]` in the UPIO_MEM32 branch. The preceding build has a different function base (+16 bytes). Source confirms early console parsing precedes the retained logger. This supports disabling the unused serial console for one targeted trial; cache epoch and exclusive failure cause remain unproved. All source/disassembly/map evidence is in evidence/. No sysfs register reread or further reboot was performed.
