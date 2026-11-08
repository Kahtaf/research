# Diagnostic scheduler-switch capture

Question: what finite task-switch observations surround the unchanged PID1 helper boundary?

Status: **ONE candidate built and packaged; VM verified TERMINATED.** Parent owns one authorized physical trial, eventual manual Power fallback, collection and interpretation. No device/ADB/root/private factory/raw target-log access occurred. No `--execute`, physical/fullOS GO, automatic UNKNOWN retry or next build.

- [candidate.img](artifacts/candidate.img): 7979008 bytes, SHA-256 `84d721c2056a15e4e3a1a986fc015b9c0f595a6406ea590ac91a2cb52aeddb44`.
- [candidate.p10.raw](artifacts/candidate.p10.raw): 16740352 bytes, SHA-256 `ab1b388b1f48365edb5d0b554ac4151debe32638758aea0bd1ef1ea4b20b6ea6`.
- Whole entry/legacy/switch capture UUID: `3d26cc95-11a8-41a2-ac62-3a2a33bd506e`. Helper UUID stays `f0c3c82c-d639-4d8a-90f2-155fd4224ceb`.
- [System.map.gz](artifacts/System.map.gz): 877897 bytes, SHA-256 `5b447e350ba2a5057848139ed1322ddb7ec42f2e5a88dda7d773b0af5bb31e2e`. Its 4391672-byte uncompressed content was verified locally, SHA-256 `28e517aaac97a8fd31399358e008d9d4d1d505e242f63a9ba4ff5c73273be0b6`. `vmlinux` remains VM-only.
- Exact pins, commands, ABI, bounds and limits: [handoff.json](evidence/handoff.json). [Patch](source/changes.patch), [source pre/posts](evidence/source-pins.json), [preservation/packaging](evidence/packaging-receipt.json), [ELF receipt](evidence/linked-capture.json), [disassembly](evidence/scoped-hooks.disasm), [ABI](evidence/hook-abi.json), [layout](evidence/switch-layout.json), [host controls](evidence/encoding-controls.json).

`finish_task_switch()` calls the recorder immediately after its original `prev_state = prev->state` assignment, before `vtime_task_switch`, perf, `finish_lock_switch`, clearing `prev->on_cpu`, or freeing `prev`. Actual ELF passes `prev` in x0 and the saved long state in x1 at `finish_task_switch+0x54`; `prev->on_cpu` clears at +0x84 and original rq unlock calls at +0x8c. Reads of previous PID/priority and all current task fields finish before returning to that unchanged lifetime path. The original preempt-count warning/correction precedes the seam unchanged; recorded preempt count is the actual value at this seam.

The recorder admits only readiness + `nr_cpu_ids==1`, CPU0, IRQs disabled and task context. It neither acquires `trace_lock` nor changes IRQ masks, policy, priority, preemption behavior or routing. Actual ELF has one direct CNTVCT register read after ISB, no indirect recorder call or clock subsystem call, and no DAIF write. Normal calls are byte memset, cache clean and the private metadata writer; the inherited stack protector retains its canary-failure-only `__stack_chk_fail` branch. The cache-clean helper ends in actual `dsb sy`. No printk, allocation, scheduling, sleeping or dynamic memory is added to ordinary hook execution. Synchronous encoding and cache cleaning under rq lock can perturb timing.

Each 256-byte ASCII record holds sequence, raw counter, previous PID/exact saved state, next/current PID, next effective priority and policy, previous priority, preempt count, CPU/IRQ admission and the existing capture-serial anchor, plus all 16 current comm bytes as hex. Eight latest-switch rows wrap; slots8/9 separately retain the latest observed PID1-out/in through `total`. No shared raw spinlock is introduced under rq lock. Calls before readiness are outside the observation horizon. Post-ready admission, reentry, guard and overflow failures latch independent sticky loss.

The old 15 rows/5952 bytes and old decoder are preserved. `cap_init` checks actual OEM console bounds for **8960 combined bytes** before writes, places the new 3008 bytes immediately after the old capture, cleans/publishes the combined log-size reservation, then publishes readiness. Original mapping, DT/reservation guards and append writer remain intact. Both guard cache lines, UUID, total/first/last/wrap/count metadata, all rows and matching generation/tails are checked by the new decoder. Payload publication is invalid-before-write, clean-to-PoC+barrier, then valid marker; inconsistent cross-record snapshots fail UNKNOWN. A full append buffer still freezes instead of overwriting early capture.

The independent source/output copy uses `cp -a --reflink=auto`; scoped inodes differ and frozen repositories/artifacts remain unchanged. The four edited source files are scheduler core, recorder, recorder declarations and entry/capture metadata. Existing clock/counter/timer function bodies/hooks and RDMA skip source were preserved. Config SHA remains `708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1`. Runtime and compiled hardware DT, whole wrapped ramdisk/helper, initrd geometry, mappings, bootargs and installer `execute`/`Transport`/`Guard`/adapters are byte-identical. Source `adb` is 0755. Installer changes only exact hashes, actual length, profile and appended current full-p10 `5f07084ea1c5df8c6d6e76f99be264149c19b77a0a9265cc6a05db3b6258a412` supplied by parent, not read here.

```text
bootopt=64S3,32N2,64N2 build_version=3 console=null nr_cpus=1 printk.devkmsg=on nohlt
```

Base: `/srv/android/asus-linux49-rdma-registration-skip-20261107-d140b2bf/{kernel,out}`. Owned output: `/srv/android/asus-linux49-scheduler-switch-capture-20261107-3d26cc95`. One `make -j8 Image.gz-dtb` passed with 24 warning lines retained; no compile corrections, no full-tree audit, no product/AOSP work. Two checker corrections (memory alias/stack-canary classification; unrelated perf `sw_*` selector) and their failures are preserved; candidate source was unchanged. Readiness, build and fetch used one owned persistent SSH master with TCP fallback disabled for channels. It was closed after successful fetch; [final VM state](evidence/after.stdout) is TERMINATED.

Exactly one actual default installer PLAN passed with restricted public dependency readers substituted only in memory. [Isolation receipt](evidence/plan-isolation-receipt.json) states what was and was not checked. Delivered guards and readers remain intact. Parent PLAN command:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-scheduler-switch-capture/source/install.py
```

After the parent's ONE physical trial and established complete-console collection, decode locally (paths are placeholders; no raw private console was opened here):

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-scheduler-switch-capture/scripts/decode.py /absolute/path/to/parent-complete-console.txt --uuid 3d26cc95-11a8-41a2-ac62-3a2a33bd506e
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-scheduler-switch-capture/scripts/decode_switch.py /absolute/path/to/parent-complete-console.txt --uuid 3d26cc95-11a8-41a2-ac62-3a2a33bd506e
```

Expected readiness/guard evidence: fresh `ASUS49-ENTRY`, `A49CAP1` and `A49SW1` UUIDs; `A49FAULT 0`; canonical committed `VA49SH` metadata; `A49SLOSS 0 guard=0 busy=0 admission=0 overflow=0`; both UUID-bound `A49SGUARD BEGIN/END` lines; ten complete `VA49S` rows with matching sequence/tails; and the two unchanged RDMA skip lines. Their Linux IRQ values must come from runtime (prior physical trial verified237/238). Parent still requires exact full-p10 readback and the established physical identity/geometry guards. Missing/torn/dropped/nonadmitted data is UNKNOWN; stop for interpretation, without automatic retry.

An admitted decode reports only finite switch order, current task identity/comm/effective priority/policy and saved previous state, ring horizon and latest PID1 transitions. An observed PID1 switch-in establishes kernel selection; it does not establish userspace return. Fixed PID1-out newer than fixed PID1-in can establish absence of a later **observed** switch-in through captured `total`, not permanent starvation. Neither absent switches nor completed historical IRQ rows establishes a permanent wedge or continued later IRQ delivery. No clock-core fault, PMIC issue, named culprit or fix follows automatically. The cached PMIC-ADC reset PC epoch remains UNESTABLISHED and is not pursued.

Continuation: parent performs only its one authorized trial, interprets admitted evidence, and stops. This candidate is diagnostic observation only. Do not make a next build from this handoff.
