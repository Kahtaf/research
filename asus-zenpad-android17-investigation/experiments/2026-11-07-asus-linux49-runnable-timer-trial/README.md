# One runnable timer/IRQ observation

Question: does the counter advance and do timer IRQs and SIGALRM arrive while RAM PID1 remains runnable?

Status: owner freshly confirmed nearby Power fallback; fresh stock identity recorded. One recovery-only installation and one entry pending. New helper UUID bee07d4f-f6c2-4845-bfe8-c4745767c216, corrected GICv2/Level parser, same kernel and bootargs. No blocking sleep, normal OS changes, block-device opens or storage writes. Require actual loop duration, before/after IRQ counts, final alarm flag, complete log and verified stock return; a cap before one second cannot prove a missed alarm.

## Physical result

Exact installation and cleanup verified; one entry returned to fresh stock Android. 100 fresh helper records expose arch_sys_timer and mtk_tick as clockevent/broadcast devices. Initial monotonic read returned0.674848768s. The finite runnable loop did not emit its completion or after-snapshot; no alarmmarker was observed. The before snapshot found two arch_timer lines but rejected both, so there are no accepted timer counts. The remaining GIC-0 naming branch was missing from the corrected parser. No zero-IRQ or counter-frozen claim follows. Preserve raw console privately and public observations. Further userspace variant alone is not justified without inspecting the shared kernel counter/event path.
