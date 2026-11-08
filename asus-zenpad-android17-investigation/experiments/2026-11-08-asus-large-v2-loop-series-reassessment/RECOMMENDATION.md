**Choose the return-boundary cold hook. One kernel build, one trial, zero helper changes.**

Why this one: your pinned-4.9 enumeration of `devkmsg_write` leaves exactly two unmeasured links around the existing log_store hook — entry→log_store (GFP_KERNEL kmalloc, copy_from_iter) and log_store→return (log_unlock tail, console_unlock, kfree, `return len`). The open question — did sched.original/500k actually return — *is* the second link. A new device endpoint or IRQ counter measures neighbors of that link, not the link.

**Design** (patch `fs/printk.c` `devkmsg_write` in the pinned tree; place by source, not memory):
- **WENT**: after validate/ratelimit pass, immediately before kmalloc.
- **WRET**: after kfree, immediately before `return len`.
- Payload both: magic + new format version, per-write seq, line length; optionally a free snapshot of the existing PPI30 count (payload, not a new experiment).
- Emit via the existing calibrated retained writer wrapped in `local_irq_save/restore`; no printk recursion, no allocation, no clock read; preformatted strings. Source-qualify the writer: verify it takes no locks and runs safely IRQs-off in process context (it already runs IRQs-off under logbuf in log_store).
- log_store hook unchanged → each helper write yields a strict **WENT→LOG→WRET** buffer order (single CPU, serialized helper); seq+len pairing; LOG may add an in-irq byte to reject rare interleave. Residual unmeasured sliver after WRET is only C-return + syscall exit — nothing blockable there.

**Trial**: rerun the current trial-3-state helper binary untouched — no milestone/priority/loop edits; same config/DT/nohlt/nr_cpus=1/console=null/printk.devkmsg=on; thermal/charging/reset protections on; run to normal stock return. This is a re-observation under a new instrument, not a new loop variant.

**Acceptance and freshness** (against stale trace): (1) first boot record = generation header: current build tag + format version + generation counter + buffer wipe; host reader must require the current tag and reject any trace lacking it. (2) In-run positive control: the initial-clock write (published in every trial to date) must show the full triple, else VOID. (3) Markers self-describe magic/version/seq/own buffer offset; reader enforces contiguity; a gap ⇒ dropped marker. (4) Rely on ordering only, no timestamps.

**Terminal outcomes**:
- **P1**: WRET(sched.original) present, WENT(final) absent ⇒ last write returned; loss inside the deterministic bounded compute window ⇒ **execution loss**; reporting exonerated at this boundary.
- **P2**: WENT(final) present, no LOG(final) ⇒ blocked/lost in kmalloc/copy_from_iter ⇒ **reporting-path (alloc) fault**; compute exonerated. (Blocked write + alarm/watchdog stock return is consistent with what you observed.)
- **P3**: LOG(sched.original) present, WRET absent ⇒ loss in the thin post-log_store tail ⇒ reporting fault localized; all prior completion silences reinterpret as never-returned writes.
- **VOID/UNKNOWN**: generation or first-triple failure ⇒ instrument fault; repair and re-run once (same experiment).

**Stop condition**: P1/P2/P3 each terminates the write-return-vs-execution question; add no further trace hooks. Next work becomes storage (P1) or a targeted devkmsg fix (P2/P3).

**Critiques**: A new retained-device endpoint needs new fops/device code *plus* helper edits, breaking frozen-helper comparability, and tests a parallel path rather than the suspect one — keep it as the FIX if P2/P3 lands. A standalone IRQ counter measures liveness, not the write boundary; WENT-absence plus deterministic compute already implies execution loss without it, and counter→lockup inference is already rejected. No better behavioral unit exists on this evidence: the two unmeasured links are enumerable in your own pinned source — anything else would be guessing.