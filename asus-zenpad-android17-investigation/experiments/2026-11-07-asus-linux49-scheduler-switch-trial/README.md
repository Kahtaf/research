# One scheduler-switch capture trial

Question: what finite task switches surround PID1’s unfinished runnable-clock loop?

Status: prepared. One recovery-only installation/entry; unchanged helper and timer/counter behavior, diagnostic scheduler recorder added. Require exact fullp10 readback, fresh UUID3d26cc95-11a8-41a2-ac62-3a2a33bd506e, complete loss-free old and scheduler captures. Owner authorized eventual manual fallback without availability questions. Normal OS partitions remain unchanged.

Continuation: install, one entry, collect complete console, decode privately and interpret finite switch bounds. No automatic retry or next variant.

## Result

One trial/full readback and fresh stock return verified. Legacy and scheduler captures complete, loss0. Total1234switches; last selects PID119/kworker0:3 at normalpriority120/policy0 from runnablePID1(state0), anchor1310. Latest PID1in1233, out1234; no later recorded switch. Helper still stops after initial0.650696768s sample. This identifies a scheduling boundary; active work function remains unknown. Next scoped observation can add the current worker function to the same scheduler record, using current_wq_worker already available at the hook. No worker disable/timekeeping change justified.
