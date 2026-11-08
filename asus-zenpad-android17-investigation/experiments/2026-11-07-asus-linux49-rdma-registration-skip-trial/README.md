# One headless RDMA registration control

Question: does skipping RDMA0/1 registration clear the observed RAM PID1 clock-loop boundary?

Status: prepared; one recovery-only trial. Config, helper, runtime DT, timer and capture remain preserved. Require exact full-p10 readback, fresh UUID d140b2bf-e06f-4ba7-8203-83a1c4ce4119, both skip lines and complete loss-free capture. Positive clears this exposure only; no PID1 is inconclusive. Normal OS partitions remain unchanged. Owner authorized eventual manual Power fallback without availability questions.

Continuation: run one admitted installation and recovery entry, collect complete retained console, decode privately and report outcome. No automatic retry.

## Result

One installation/full readback and recovery entry completed; new stock Android boot verified. Both runtime RDMA skips (IRQs237/238) are present. Same unfinished loop, no after-counts or SIGALRM marker. All latest selected clock/counter/timer captures completed, loss0. This narrow control is negative; it does not establish a clock-core fault. Cached reset PC maps to PMIC ADC immediately after a udelay call, but its firmware capture epoch is unestablished and is only a clue. See evidence/RESULT.json and CAPTURE-SUMMARY.json.
