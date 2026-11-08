# Active work at the scheduler capture seam

Question: what active work function did the selected current worker already own at the existing scheduler switch seam?

Status: **ONE diagnostic candidate built and packaged; existing VM verified TERMINATED.** Parent owns one physical trial, eventual manual fallback and interpretation. No device/ADB/root/private factory/raw target logs, execute, physical/fullOS GO or next build.

- [candidate.img](artifacts/candidate.img): 7979008 bytes; SHA-256 `3b75e5258c3613678458d6299fcfe23b15fb8f74ce9beb6dfd1f0ecc44d79f34`.
- [candidate.p10.raw](artifacts/candidate.p10.raw): 16740352 bytes; SHA-256 `49e6519e4c4447b8c0b334e9991e8b011a6943cbcf79550648a33a5074bcfd4b`.
- [System.map.gz](artifacts/System.map.gz): 877981 bytes; SHA-256 `23472869e7bafce2a5997e1a014704018be8cb6bf6f11265db6a24fe101b3d6e`. Genuine uncompressed map: 4391673 bytes, SHA-256 `03d0034e5949b7f1fd88cfd5d12d274e5d3536215359fee0d67ca9bcf15f66e1`; verified locally. `vmlinux` remains VM-only. Offline symbolization needs no VM restart.
- Fresh entry/legacy/switch UUID: `8e5c5d4d-6f94-4569-bfc6-63d92bac94a4`. Full helper/ramdisk UUID stays `f0c3c82c-d639-4d8a-90f2-155fd4224ceb`.
- [Handoff](evidence/handoff.json), [source diff](source/changes.patch), [source pre/posts](evidence/source-pins.json), [scoped preservation](evidence/linked-capture.json), [ownership proof](evidence/ownership-proof.md), [actual hook ABI](evidence/hook-abi.json), [disassembly](evidence/scoped-hooks.disasm), [layout](evidence/switch-layout.json), [host controls](evidence/encoding-controls.json), [synthetic decoded examples](evidence/decoded-examples.json).

The public prior result captured runnable PID1 out at sequence1234 to PID119 kworker/0:3, normal priority120/policy0, with no later switch in a complete finite nofault capture. It did not capture an active function or prove execution after finish_task_switch. This unit adds only own-worker `READ_ONCE(current_func)` and `READ_ONCE(current_work)` snapshots plus PF_WQ_WORKER/worker-present validity at that same seam, immediately after saved prev_state and before vtime/perf/rq unlock/lifetime changes. The exact branch already includes workqueue_internal.h and current_wq_worker() returns kthread_data(current) only in task context with PF_WQ_WORKER. Current task/worker lifetime and actual CPU0, nr_cpu_ids1, IRQ-disabled admission are explained in the ownership proof and linked ABI receipt. No last_func substitution, work->func dereference, pwq/name walk or new seam is introduced.

A valid own worker with a non-NULL current_func reports `active_function_snapshot`. A valid own worker with NULL current_func reports `no_active_function_at_seam`; this leaves later work inconclusive. Non-worker and worker-unavailable are explicitly separate validity outcomes. The host examples use fabricated numeric pointers and are **not runtime evidence**. None of these observations automatically establishes culprit, starvation, scheduler failure or execution after the seam. Actual raw pointer values must stay parent-private until symbolized.

A49SW2 uses 320-byte rows, 14 numeric fields, all 16 comm bytes, matching sequence/tail, eight bounded ring slots and fixed latest PID1-out/in slots. The old 5952-byte area/decoder are unchanged. The switch area is 3648 bytes; cap_init's existing actual OEM console bound check reserves all **9600 combined bytes before append/readiness**. It adds 640 fixed bytes within the same admitted console and preserves hardware DT/reservations/mapping. Invalid-before-payload/clean+dsb/valid-last publication, guards, sticky faults, busy/overflow and before-ready semantics remain. The decoder rejects wrong protocol, malformed/partial fields or loss, torn generations, cross-slot disagreement and inconsistent finite horizon. Timing can change from encoding/cache cleaning under the existing rq lock.

Base `/srv/android/asus-linux49-scheduler-switch-capture-20261107-3d26cc95/{kernel,out}`; owned output `/srv/android/asus-linux49-active-work-capture-20261107-8e5c5d4d`. Independent inodes via cp -a --reflink=auto, preserving frozen/nested repositories without a full-tree audit. Exactly one make -j8 Image.gz-dtb succeeded; 24 warning lines retained, zero compiler/source corrections. One checker-only correction resolved duplicate local trace_init symbol selection; initial output and script are preserved separately in [checker corrections](evidence/checker-corrections.json). Candidate source was unchanged. [Repository preservation](evidence/repository-preservation.json), [source-copy receipt](evidence/source-copy.json), [build receipt](evidence/build-receipt.json), [package receipt](evidence/packaging-receipt.json), [packager changes](source/package.diff), [installer diff](source/install.diff).

Config remains `708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1`. Genuine output config, runtime and compiled hardware DT, whole wrapped helper ramdisk, initrd geometry, bootargs/mappings and timer/counter/core behavior/RDMA skips compare unchanged. Installer execute/Transport/Guard/adapters are byte-identical; only pins, profile, actual length and append-only current full-p10 `ab1b388b1f48365edb5d0b554ac4151debe32638758aea0bd1ef1ea4b20b6ea6` change. This current pin came from parent and was not read from target. adb remains 0755. The previous preserved packager was reused with base/pin/profile updates. [One isolated default PLAN](evidence/install-plan.json) passed using only the prior truthful in-memory restricted public reader substitutions; [limitations](evidence/plan-isolation-receipt.json). Delivered readers/guards remain intact.

Readiness/build/fetch used one owned persistent SSH master with ProxyCommand=false on channels, preserving remote.py SHA c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab. Only this master was closed. [Final VM state](evidence/after.stdout): TERMINATED, ID8549823276971553556 in PROJECT_REDACTED/us-central1-a.

Parent PLAN (no execute authorized by this handoff):

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-active-work-capture/source/install.py
```

After the parent's single physical trial and established complete-console collection, decode locally; placeholder paths are parent-private:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-active-work-capture/scripts/decode.py /absolute/path/to/parent-complete-console.txt --uuid 8e5c5d4d-6f94-4569-bfc6-63d92bac94a4
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-active-work-capture/scripts/decode_switch.py /absolute/path/to/parent-complete-console.txt --uuid 8e5c5d4d-6f94-4569-bfc6-63d92bac94a4 > /absolute/path/to/parent-private-switch.json
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-active-work-capture/scripts/symbolize.py --decoded /absolute/path/to/parent-private-switch.json
```

Expected: fresh ASUS49-ENTRY, A49CAP1 and A49SW2 identities; A49FAULT 0; canonical VA49SH; A49SLOSS 0 guard=0 busy=0 admission=0 overflow=0; both UUID-bound A49SGUARD lines; ten 320-byte VA49S rows; unchanged RDMA0/1 registration-skip markers with runtime IRQ values. Full marker strings and exact commands are in handoff.json. Parent still owns identity/geometry/full-p10 readback checks. Missing/torn/nonadmitted results are UNKNOWN, with no automatic retry.

Continuation: parent interprets its one authorized physical trial. NULL does not exclude later work. Stop after this candidate; no physical/fullOS GO or next build.
