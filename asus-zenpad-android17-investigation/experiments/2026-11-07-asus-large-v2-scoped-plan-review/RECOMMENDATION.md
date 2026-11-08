## Verdict on the pending experiment

**Yes — run it. It is the first stock trial in this whole effort whose every outcome branch is decisive.** The failed positive control was non-decomposable by construction: its late path carried no marker of its own (wrapper had no UUID), so "zero tag" could not distinguish *writer didn't execute*, *guard refused*, *readback window missed the payload*, or *printk/retention broken*. The pending design fixes exactly that: pre-guard record (execution proof), x0/CurrentEL/SCTLR (ABI), refusal branch ID (guard outcome), unconditional late UUID (readback proof). It is also the right *vehicle* for one under-appreciated reason: the entry ABI is a property of the LK/ATF handoff, not of either kernel. Measuring it on stock calibrates the 4.9 guard directly — no 4.9 trial is consumed to learn it.

## The one change I'd make

**Give the late UUID+record line a second, same-boot exit: have the existing stock PID1 USB reporter dump a bounded kernel log (dmesg/`/proc/kmsg`) to the RAM FAT alongside PROBE.TXT.** The pending design's only weak branch is "late line absent in last_kmsg" — with one exit you can't tell *wrapper didn't run* from *printk didn't retain*. The same-boot USB surface is already physically proven (trial I: read-only RAM USB reported 3.18.35 in the same boot), the wrapper's printk lands in the printk ring well before PID1 exists, and dmesg bypasses the CON_PRINTBUFFER/next-boot-retention assumptions entirely. One added file, no new kernel code path, no parallel experiment.

If you insist on kernel-side-only fields: (a) bounded dereference of x0 — first 8 bytes, only if x0 ∈ [0x40000000, 0xbd600000) — to directly test the FDT-pointer premise without risking a wild physical read; (b) retarget the late snapshot dump to the **writer's published CGBD geometry**, not the stock `off_console` 234-byte window — that window is a live, unexamined suspect for the failed control (see H2).

## Predicted outcomes → next action

- **UUID present, magic set, success commit:** calibration complete. If the CGBD geometry dump is included and present, stage 1 is *fully* closed end-to-end → re-run the existing R2 4.9 candidate once, unchanged. Tag present → stage 2 proved, enter the ladder. Tag absent → 4.9-specific entry failure; port the position-independent pre-guard record into the 4.9 image, one trial.
- **UUID present, magic set, refusal branch + values:** the ABI is the answer. My top suspect is SCTLR.C=1 at handoff (firmware often leaves D-cache on; Linux tolerates caches-on entry, your guard doesn't). Fix the guard to the *measured* ABI, rebuild once, one 4.9 trial. One measurement can explain every zero-tag result to date with a single cause.
- **UUID present, magic zero:** early code never executed even on stock. Do **not** build another kernel. Use the working LK diagnostic RAMUSB to dump the inflated image at 0x40080000 and verify the redirected B and appended bytes are physically present at entry layout. Image correct + magic zero → LK's jump target ≠ image start; study actual entry PC.
- **UUID absent on both surfaces:** if dmesg has it but last_kmsg doesn't, the CON_PRINTBUFFER/retention assumption is falsified — adopt same-boot USB as the stage-2 reporting path (it's proven; that's acceptable). If neither has it, the borrowed clear-call-site assumption is wrong — one wrapper relocation, then stop.

## Three hypotheses, ranked

1. **Guard refusal at the true handoff ABI** (inference — no ABI value has ever been measured; its explanatory power across *all* zero-tag results, stock and 4.9, is circumstantial consistency, nothing more). Candidates: SCTLR.C=1, EL2 with EL2 SCTLR state, or a structural field (reserved-memory flags) refusing. **Falsifier:** the pending record's SCTLR/CurrentEL/x0 + branch ID — one trial confirms or kills the whole class.
2. **Readback geometry mismatch** (inference from a documented design asymmetry, not evidence): the writer's payload sits after its reason area at its own offsets; the stock wrapper printed 234 bytes at the stock header's `off_console`. If those windows don't overlap, the control failed while everything ran. This explains the stock-control zero but *not* the 523015B whole-region zero in trial E — check what mechanism produced that 523KB capture and whether it truly covered the whole 0x80000 before trusting it as a negative. **Falsifier:** the CGBD-geometry dump in this trial.
3. **Early code never executes** (inference; the post-inflate in-RAM image has never been verified against the staged bytes). **Falsifier:** magic==0 with UUID present; or pre-emptively, without a kernel trial, the LK RAMUSB image dump.

## Premise still untested

The stage-2 proof chain end-to-end: *a pre-MMU write to the OEM console surviving to the next-boot whole-region retained capture*. B proved a scalar store/current-read at the fiq register; A proved USB; neither proves an OEM-region write surviving LK→snapshot→whole-region retention. Without the CGBD-geometry dump, even a perfect pending trial leaves this unproven, and your first 4.9 re-trial would still rest on it. The x0-dereference premise is likewise untested (note: stock 3.18 boots, so x0 is *probably* a valid FDT — but "probably" is what stage 2 exists to eliminate).

## Gate plan and stop rule

The six gates remain structurally sound — the rabbit-hole risk was never the plan, it was that stage 1's instrument couldn't decompose a negative. Treat the pending trial as stage 1's closing measurement.

**Stop rule:** at most two more stock diagnostic trials. The breadcrumb is *calibrated* when the late UUID is physically observed on either surface; the route *stops* if two consecutive trials cannot observe it on the proven same-boot USB surface — then stage-2 proof must come from non-kernel observation (LK RAMUSB dump, same-boot RAM read), not a fourth kernel variant. Resume 4.9 only with {magic set, guard outcome known, late line observable}, at most one 4.9 trial per calibrated change. No gate-3 driver work, no Android17 flash, before a physically observed 4.9 tag — exactly as you have it.