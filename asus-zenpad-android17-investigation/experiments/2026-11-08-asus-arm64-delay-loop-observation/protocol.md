# A49DL1 fixed append

UUID: `f3da846c-cbd9-4623-adc2-5e54d097dfdc`. One candidate, parent one physical trial, then STOP. The entire old26752-byte layout and five old decoders are retained, with fresh runtime UUID. The append is2560bytes; combined29312. It uses the existing OEM console mapping and actual capacity check before writes, log_size or readiness. No new mapping/ring/history system.

All offsets below are relative to `A49DL1 uuid=...`, exactly26752bytes after `A49CAP1 uuid=...`. Lines are ASCII spaces with final newline. Each numeric field is16lowercase hex digits, separated by one space, starting at offset9. `sw_commit` invalidates the first byte, cleans to PoC+DSB, writes/cleans payload, then sets valid `V` and cleans+DSB. Header is invalidated before any generation reset. Generation/sequence tails reject interrupted publication.

| Offset | Bytes | Valid marker | Fields |
|---|---:|---|---|
| 0 | 64 | A49DL1 uuid=... | exact fresh UUID |
| 64 | 192 | VA49DH | generation,state,PMIC PREsequence,PID,PREhook caller,const caller,delay caller,stage mask; generation tail160 |
| 256 | 64 | A49DLOSS | `0 guard=0 busy=0 admission=0 overflow=0`; any1 is UNKNOWN |
| 320 | 64 | A49DGUARD BEGIN | exact UUID |
| 384 | 576 | VA49DJ | exact29 PMIC PREfields in old A49PM1 order, then new generation; PMIC sequence tail552 |
| 960 | 192 | VA49DC | generation,xloops,one LPJ operand,HZ,original unsigned product,requested cycles,const caller,calculation hook site; generation tail160 |
| 1152+192*slot | 192 each | VA49DS | generation,stage,original condition-read iteration,original counter value,cycles,actual preempt_count,actual context,PID; generation tail160 |
| 2496 | 64 | A49DGUARD END | exact UUID |

Stage slots0..6: BEFORE_FIRST_GET_CYCLES, START_RETURNED, FIRST_CONDITION_RETURNED(iteration1), ITERATION256, ITERATION65536, ITERATION1048576, RETURN_CONDITION_VALUE. Context is bit0 actual IRQ mask, bit2 task, bit4 hardirq, bit5 serving softirq, sampled BEFORE the brief publication lock. The BEFORE marker's counter0 is a sentinel. Start uses iteration0. Iterations count original condition reads including the terminating check; they do not measure wall time or count IRQs. A first delta0 can be normal at13MHz.

States:1 armed;2 calculation committed;3 selected delay begin/active;4 return marker committed;5 matching PMIC code39 POST committed. Fixed slots reset per matching target code38; every observed generation must match the copied immutable current PMIC/property/body/work identity and actual verified source caller. Historical PID119/sample3 are never constants. Duplicate/overlapping target, busy publication, guard/admission failure or saturation/overflow latches loss. Related refusal can invalidate a completed generation before rearm; no unrelated call is given a selected cookie or attributed as the target.

Decoder admission requires all five old statuses, exact append/UUID/guards/tails, canonical padding/fields, state/generation/milestone order, no loss, correct arithmetic, actual compiled caller sites and strict current PMIC/source/work/body/property join. A later pending PRE cannot use an earlier completed sample. Wrong route, missing arm, ambiguity or any loss is UNKNOWN STOP. Numeric kernel pointers remain parent-private until the supplied offline map verification/symbolizer. The genuine System.map.gz and uncompressed map pins are in evidence/System.map-uncompressed.json.

Parent commands (the worker ran only one isolated PLAN, never this delivered PLAN directly or --execute):

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-arm64-delay-loop-observation/source/install.py
# Parent's authorized one-trial installation only; installer does not reboot:
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-arm64-delay-loop-observation/source/install.py --execute
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-arm64-delay-loop-observation/scripts/decode_delay.py /absolute/path/to/parent-complete-console.txt --uuid f3da846c-cbd9-4623-adc2-5e54d097dfdc > /absolute/path/to/parent-private-delay.json
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-arm64-delay-loop-observation/scripts/symbolize_delay.py --decoded /absolute/path/to/parent-private-delay.json
```

Parent retains fresh helper/entry/full-p10 identity, complete retained-console collection and full readback, normal stock return verification and eventual manual Power fallback. No worker execute, device/ADB/root/private factory input or raw target logs. No automatic retry/variant/fix or full OS GO. The isolated PLAN substitutes truthful pinned public readers in memory; delivered guards/readers remain intact and private stock/root dependency chains are not validated by that check.

Claim limits: absent return is a finite publication/accessor/loop/return interval, not a permanent hang or source cause. Return marker precedes epilogue and POST publication. Milestones show executed checks only. LPJ/cycles are observed calibration operands, not corruption proof. Sparse task preempt/IRQ-mask contexts say nothing about intervening IRQ arrival history. Prior timer/counter completion predates prior final PRE. Normal return on a new boot does not explain the old capture. Consult exact Large before further guesses.
