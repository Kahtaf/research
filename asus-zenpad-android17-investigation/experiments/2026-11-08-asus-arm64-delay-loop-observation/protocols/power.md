# A49PS1 retained protocol

This is an independent 5,376-byte fixed ASCII area appended at legacy-start+15,168. Earlier regions remain 5,952 bytes of A49CAP1, 3,648 bytes of A49SW2, and 5,568 bytes of A49WD1. Combined reservation is 20,544 bytes. `cap_init` checks the actual OEM `sz_console` remaining capacity before alignment fill, initialization, append/log-size writes, or readiness. No new physical mapping, DT memory, reservation, or capacity assumption is introduced. If capacity fails, the captures remain unavailable and decoding is UNKNOWN.

Offsets relative to A49PS1:

| Offset | Bytes | Meaning |
| --- | --- | --- |
| 0 | 64 | `A49PS1 uuid=431dfb9c-8b78-4c8c-bd74-cc556adcf8b0` |
| 64 | 192 | Valid-last metadata `VA49PH   ` |
| 256 | 64 | Sticky `A49PLOSS 0 guard=0 busy=0 admission=0 overflow=0` |
| 320 | 64 | UUID-bound BEGIN guard |
| 384 | 3,584 | Eight 448-byte chronological event rows, slots 00–07 |
| 3968 | 448 | Fixed latest body checkpoint, slot 08 |
| 4416 | 448 | Fixed latest property entry/return snapshot, slot 09 |
| 4864 | 448 | Fixed latest external callback entry/return snapshot, slot 0a |
| 5312 | 64 | UUID-bound END guard |

Metadata has eight 16-hex-digit fields at `9+17*i`: generation=total+1, total, first retained, last retained, wraps, retained count, reserved zero, nr_cpu_ids. Generation repeats at160. First is max(1,total−7) when nonempty, last=total, wraps=floor((total−1)/8), retained=min(total,8). Empty first/last/wrap/count are zero. total stops at U64_MAX−1, before generation could wrap. Token is the entry event sequence in this new independent namespace. It is **not** the old WQ token. A caller-local context retains token, entry raw sample/sequence, numeric identities, two bounded names, and candidate body identity across preemption, nesting, callback return, and ring wrap. No table grows with calls or PIDs.

Rows start `VA49P ss `, newline at447. Twenty 16-hex-digit fields start at9+17*i. Supply and peer names occupy352..383 and384..415 as exactly16 hex-encoded bytes each; sequence repeats at424..439. All other bytes are spaces. Zero rows are valid committed empty slots, with every field/name zero. The fields, in order, are:

1. event sequence
2. local pair/body token
3. phase code
4. one raw CNTVCT sample
5. current PID
6. numeric work identity
7. numeric supply identity
8. numeric callback snapshot
9. detail: changed flag at body codes1/3/15/16; property enum at40/41; otherwise zero
10. actual pre-publication preempt_count
11. context bits:1=caller IRQoff;2=writer IRQoff;4=in_task;8=ready;16=hard IRQ;32=serving softirq
12. legacy cap_serial read-only anchor
13. scheduler sw_total read-only anchor
14. old WQ wd_total read-only anchor
15. body token (self for body; candidate or zero for callbacks)
16. original entry raw sample, retained through return
17. original entry event sequence
18. body phase at callback entry (body rows keep1; zero means UNKNOWN parent)
19. numeric peer/supplier identity for external callback only
20. return bits, zero-extended u32 for original class/notifier/uevent/get_property int returns; U64_MAX means no int return recorded

No property value, `val` contents, ADC payload, private driver state, formatted pointer, or pointer-following postcall data is stored. Names use strnlen(name,16), memcpy only that length, and zero padding. Names of length16 are explicitly truncated; short literals are never blindly read for16 bytes. A missing/null name is all zero; supply/peer numeric identities distinguish truncation collisions.

| Code | Checkpoint |
| --- | --- |
| 1 | Body entered, before original dev_dbg and first lock |
| 2 / 3 | First changed_lock pre / acquired; code3 snapshots changed |
| 4 / 5 | True decision, changed=false, before original unlock / after unlock |
| 6 / 7 | class_for_each_device pre / post with original int return |
| 8 / 9 | power_supply_update_leds pre / post |
| 10 / 11 | atomic_notifier_call_chain pre / post with original int return |
| 12 / 13 | kobject_uevent pre / post with original int return |
| 14 / 15 | Final changed_lock pre / acquired; code15 snapshots changed |
| 16 | Final changed snapshot before original unchanged branch decision |
| 17 / 18 | Original conditional pm_relax pre / post |
| 19 / 20 | Final unlock pre / body return checkpoint after unlock |
| 21 | Original first changed=false branch; still holding original lock |
| 40 / 41 | Common get_property actual driver dispatch entry / returned int status |
| 50 / 51 | Existing guarded external_power_changed actual dispatch entry / returned void checkpoint |

Code3 transitions to4 or21. Code4→5→6→7→8→9→10→11→12→13→14→15→16; code21→16. Code16→17→18→19 or directly19; code19→20. Callback events may nest/interleave between body checkpoints. `__power_supply_is_supplied_by` and the callback-presence test remain in their original order, evaluated once. Early common-getter use-count/initialized returns have no callback record because no original callback is dispatched.

Each event first commits its ring slot, then its category snapshot, then metadata. Every individual commit invalidates the destination first byte to `!` and cleans that cache line to PoC; writes the full payload and matching tail and cleans it to PoC; then changes only the first byte to `V` and cleans again. The actual linked clean helper ends in `dsb sy`. Snapshot or ring/header disagreement during interruption is UNKNOWN. The independent latch only moves0→1. Guard corruption, publication trylock/reentry loss, unsupported NMI/CPU admission, or numeric overflow latches a reason and globally stops decisive interpretation. Finite ring overwrite is normal, not loss.

The new independent raw trylock is brief and never spans an original operation. Recorders acquire no changed_lock, class lock, notifier lock, scheduler/pool lock, or earlier recorder lock. The allowed edge from an original lock to this nonblocking trylock has no reverse edge. UP plus the publication IRQ mask makes old-anchor reads coherent without changing old protocols. Actual preemption/IRQ/softirq context is recorded; nonzero alone is admitted. Callback parent candidacy requires same task PID and an active latest body snapshot. IRQ callbacks get UNKNOWN parent. Another task/body or nested body can overwrite that candidate; local callback tokens remain correct, and uncertain attribution is UNKNOWN. One CPU does not imply one worker.

`decode_power.py` first requires the unchanged three old decoders to admit the capture. It checks adjacency, all markers/guards/loss, canonical rows, generations, enum/source/config identities, pointer ranges/alignment, chronology/anchors, category snapshots, graph order and local pair identities. A returned callback whose entry fell outside the eight-event ring is `UNKNOWN_ENTRY_OUTSIDE_HORIZON`, without invalidating the entire area. Fixed snapshots can preserve older context beyond that ring. A target still needs a unique exact named-WQ-function/PID/work/time join. The unchanged WQ decoder additionally requires its latest entry to join the exact latest scheduler selection; a context switch that defeats that strict old join makes target attribution UNKNOWN.

Property attribution additionally requires the same body token/PID/work and time/phase anchors, plus exact numeric/name supply identity, or a retained exact external consumer/supplier relationship. An unrelated latest property snapshot is explicitly UNKNOWN, never assigned to the worker by proximity. A pending callback after the body has left that phase is inconsistent and UNKNOWN. Numeric callback symbols are resolved offline against the genuine exact-build System.map; non-exact/unavailable names stop symbol interpretation. Keep raw decoded addresses parent-private.

Body entry demonstrates reaching that checkpoint inside the C function. A pre-call checkpoint still includes recorder return, ordinary preemption, callback dispatch and entry, callback execution, and postcall checkpoint entry/publication. Code20 precedes canary/epilogue and actual C return; only the separate old WQ postcall observes return to its caller. A missing checkpoint in a finite snapshot never proves duration, permanent nonreturn, cause, a generic clock fault, or cached PMIC/ADC PC provenance. Cache cleaning and normal raw-unlock preemption can perturb timing. Parent interprets one physical trial; loss/torn/ambiguous joins are UNKNOWN STOP, without automatic retry, alternate build, disable/fake, charging/thermal change, or fullOS GO.
