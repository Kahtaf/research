# Work dispatch entry/return capture

Question: does the latest selected worker reach the actual `process_one_work` dispatch boundary, which function/work is about to be called, and is its token-paired postcall return retained?

Status: **ONE diagnostic candidate built and packaged; authorized VM verified TERMINATED.** Parent owns one physical trial, interpretation, and standing eventual manual fallback. No target contact or physical/fullOS GO was performed by this worker. Stop on UNKNOWN; no automatic retry, variant, or next build.

- [candidate.img](artifacts/candidate.img): 7981056 bytes; SHA-256 `404ec624191bb44a8cf126195addcb18e6835dd1431e025db461a1accca1286f`.
- [candidate.p10.raw](artifacts/candidate.p10.raw): 16740352 bytes; SHA-256 `7418c5d3a43c0b458311d880ec87f0d6b781794998d688153f31c3383f7c3752`.
- [System.map.gz](artifacts/System.map.gz): 877880 bytes; SHA-256 `e6de4c14be99f5d1db8f6c9224370b9f8521d35976006d60a47a414ad64cdbb4`. Genuine uncompressed map: 4391508 bytes, SHA-256 `76ee696f38cef952533aa61deb5391c10fb90b50736b78d20e8323e2fc3a30ba`; verified locally against the VM build receipt. `vmlinux` and `out` remain VM-only.
- Fresh entry/legacy/SW2/work UUID: `b4702f9a-6b32-423f-b789-d2bd515c0707`. Whole helper/wrapped-ramdisk UUID remains `f0c3c82c-d639-4d8a-90f2-155fd4224ceb`.
- [Handoff](evidence/handoff.json), [scoped source diff](source/changes.patch), [pre/post pins](evidence/source-pins.json), [source pre/posts](source), [actual linked capture](evidence/linked-capture.json), [hook ABI](evidence/hook-abi.json), [linked disassembly](evidence/scoped-hooks.disasm), [base seam](evidence/base-process_one_work.disasm), [ownership/lifetime proof](evidence/ownership-proof.md), [protocol](evidence/protocol.md), [host controls](evidence/encoding-controls.json).

The public prior complete nofault capture selected PID119 kworker0:3 at scheduler sequence1231 from runnable PID1, with own worker present but current_func/current_work NULL. Earlier PID42 `mmc_rescan` snapshots do not identify that final worker's later job. The helper remained after its initial0.650700153 sample without finite loop completion/alarm/after counts. This candidate asks only whether a worker later crosses the actual work dispatch boundary and its postcall record; it adds no driver, clock, PMIC or scheduler fix and uses no cached LASTPC evidence.

Only `kernel/workqueue.c:process_one_work` gains a new seam. All workers are observed with no hardcoded PID. Entry follows the existing execute-start tracepoint and snapshots numeric current_func/work before the original **unchanged** `worker->current_func(work)`. Postcall takes only the invocation-local token, before the existing execute-end tracepoint. No work pointer is dereferenced after the call by the new code. Actual linked entry/call/postcall addresses are `0xffffff80080c71c8` / `0xffffff80080c71d8` / `0xffffff80080c71e0`; callee-saved x26 holds the token across the original `blr x1`. Original unlock/lockdep/tracepoint/lifetime cleanup order is preserved.

A49WD1 appends5568 guarded ASCII bytes after the unchanged5952 legacy and3648 SW2 bytes. Actual OEM capacity checks reserve all15168 bytes **before any new capture write/readiness**, within the unchanged mapping/range. The16-event ring stores chronological entry/return events, monotonic per-entry identity, PID/all16 comm bytes, numeric pre-call function/work, raw single CNTVCT, task/readiness/IRQ/preempt validity, and read-only cap_serial/sw_total anchors. Returns append token-only identities, including when their entries were overwritten. Independent sticky loss, guard checks, overflow stop, invalid-before-payload, generation tail, PoC clean+dsb and valid-last publication are retained. Both old decoder files are byte-identical; pass the fresh UUID explicitly.

The writer uses an independent raw trylock with brief IRQ-save and actual runtime nr_cpu_ids1/CPU0/task/IRQ-off admission. It acquires neither trace_lock nor scheduler/pool locks, and the scheduler hook acquires neither writer lock. No new lock, IRQ mask or preempt disable spans the actual work function. The standard unlock helper may normally preempt **after** release/IRQ restoration; its linked instructions are included. There is no explicit recorder scheduling call or timeout, no printk/clock API/allocation/sleep or counter-hook recursion. Entry therefore bounds hook return, ordinary preemption, dispatch, callback and postcall observation; it does not itself prove callback-body entry. An unpaired entry never proves permanent hang or root cause.

The strict new decoder checks identities, complete areas/guards/loss, canonical generations/padding/rows, finite chronology, interleaved token pairs and scheduler/capture-anchor cross-joins. A return whose entry is outside the ring is explicit finite UNKNOWN. Target attribution requires the **latest retained entry** to match the latest scheduler-selected PID/all comm bytes, worker validity, exact scheduler anchor and normal entry context. If either overall decoding or target interpretation is UNKNOWN, stop this candidate. Raw addresses remain parent-private until local map-verified naming.

Exact base `/srv/android/asus-linux49-active-work-capture-20261107-8e5c5d4d/{kernel,out}`; owned candidate `/srv/android/asus-linux49-work-dispatch-capture-20261107-b4702f9a`. Whole kernel/out were independently copied with `cp -a --reflink=auto`; source/output inode checks and [repository preservation](evidence/repository-preservation.json) are scoped, with no full-tree audit or Git mutation. Exactly one make -j8 Image.gz-dtb succeeded, with24 retained warning lines and zero compiler/source corrections. Two checker-only corrections (host stub shadowing; expected unlock-helper allowlist) and initial failures are recorded separately in [checker corrections](evidence/checker-corrections.json); kernel source and build were unchanged.

Config remains `708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1`. Entire wrapped helper ramdisk, compiled/runtime hardware DT, bootargs, initrd geometry, load maps, legacy/scheduler capture and RDMA0/1 skips are preserved. [Packaging receipt](evidence/packaging-receipt.json), [packager diff](source/package.diff), [installer diff](source/install.diff). Preserved installer execute/Transport/Guard/adapters are unchanged; only pins/profile/actual length and append of parent-supplied current full-p10 `49e6519e4c4447b8c0b334e9991e8b011a6943cbcf79550648a33a5074bcfd4b` change. This pin was not freshly read from target. adb remains0755. [One isolated default PLAN](evidence/install-plan.json) passed with truthful in-memory restricted public-reader substitutions only; [limitations](evidence/plan-isolation-receipt.json). Delivered guards remain intact.

One owned persistent SSH master handled readiness/build/fetch, with ProxyCommand=false on channels and no TCP fallback. remote.py remains SHA `c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab`. Only this owned master was closed. [Final VM receipt](evidence/after.stdout): TERMINATED, ID8549823276971553556, PROJECT_REDACTED/us-central1-a. No new cloud assets, disks, firewall, credentials, resource caps or wall kill; no AOSP/product work.

Parent PLAN command (this handoff adds no execute authorization):

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-work-dispatch-capture/source/install.py
```

After the parent's one physical trial and complete-console collection, decode locally with parent-private paths:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-work-dispatch-capture/scripts/decode.py /absolute/path/to/parent-complete-console.txt --uuid b4702f9a-6b32-423f-b789-d2bd515c0707
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-work-dispatch-capture/scripts/decode_switch.py /absolute/path/to/parent-complete-console.txt --uuid b4702f9a-6b32-423f-b789-d2bd515c0707
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-work-dispatch-capture/scripts/decode_work.py /absolute/path/to/parent-complete-console.txt --uuid b4702f9a-6b32-423f-b789-d2bd515c0707 > /absolute/path/to/parent-private-work.json
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-work-dispatch-capture/scripts/symbolize_work.py --decoded /absolute/path/to/parent-private-work.json
```

Expected: fresh ASUS49-ENTRY/A49CAP1/A49SW2/A49WD1 identities; A49FAULT0, A49SLOSS0 and A49WLOSS0 with every reason0; both UUID-bound switch/work guards; VA49SH and VA49WH canonical metadata; ten320-byte VA49S rows; sixteen320-byte VA49W rows; unchanged RDMA0/1 skip markers with actual mapped IRQs. Exact marker strings are in handoff.json. Parent retains physical identity/geometry/full-p10 readback checks and all interpretation. Synthetic fixtures are host controls only, never target evidence.

Continuation: parent reviews this package, then owns its one authorized trial and manual fallback. A missing/torn/lost/nonadmitted or unjoined result is UNKNOWN and ends this candidate. No automatic retry, next build, or fullOS GO.
