# Normal-priority RAM compute control

Question: can the unchanged sparse kernel publish completion of 2M unsigned arithmetic iterations under verified SCHED_OTHER/priority 0?

Status: **one candidate packaged; STOP**. One helper compile, zero kernel builds, one isolated PLAN and focused checks passed. No children, device/ADB/private target-data contact, install or trial. Exact existing VM verified TERMINATED; owned SSH master closed.

Important outputs: [handoff](evidence/handoff.json), [focused proof](evidence/scoped-proof.md), [checks](evidence/focused-checks.json), [package/preservation receipt](evidence/packaging-receipt.json), [PLAN substitutions](evidence/plan-isolation-receipt.json), [source delta](source/changes.patch), [decoder](scripts/decode_compute.py).

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| [candidate.img](artifacts/candidate.img) | 7,991,296 | `85f282b8ac7cfb4ee8f85737bcc2d9760059a8363ad9f5c58a857cd7f6bd0bd6` |
| [candidate.p10.raw](artifacts/candidate.p10.raw) | 16,740,352 | `9a836b53aaf66366a93f2f715c73247ae49e889cb4bce4a369655939142c04ad` |
| [init](artifacts/init) | 598,000 | `f8d201a6b72b13a4068584f8a5e73526f8eef669eabc96975ca69547506d3b26` |

Fresh control UUID: `03f2153c-4faf-41ba-9f66-bcd8d4b1aa9f`. Reused kernel prefix `f53fadc2-5cd5-4c44-b5a3-7a65567c6935` and helper prefix `ef56ad88-6904-4452-90a1-3744beaa3c78` are **not fresh identity**. The unchanged kernel profile still says sparse-fifo-v1, while this helper requests no FIFO policy. Bind the variant through exact fullp10 readback, a new stock boot and the fresh clock.path VALUE:

```text
value=kernel-syscall:syscall(SYS_clock_gettime);vDSO-bypassed;control=03f2153c-4faf-41ba-9f66-bcd8d4b1aa9f;loop=pure-compute-normal
value=control=03f2153c-4faf-41ba-9f66-bcd8d4b1aa9f iterations=2000000 checksum=e4ca7075 reason=compute-cap
```

Actual original scheduling policy/getparam/priority must all be zero before compute. Refusal finishes without any scheduling mutation. Preserved alarm and successful initial direct clock precede the loop. The loop uses volatile uint32 arithmetic with no time-dependent exit, clock calls or sleep; at most three nonblocking milestone writes report iteration/checksum. Completion precedes afterIRQ/MMC and finish/reboot. No final clock sample is emitted. Existing setup, sink and timer/IRQ policies remain.

Exact kernel gzip/raw stream, wrapper/config/hardware DT are reused byte-for-byte. Only init and necessary packaging/length/hash/padding/runtime initrd-end change. Gzip 257,074 bytes ends at `0x4403ec32`, leaving 981 bytes under unchanged 0x4403f007. Supplied current p10 `6f5577f7330754c43c52ad4e522fd487fd1cb4d56331991684f8515b03eba353` is appended to installer admissions; it was not freshly observed here. execute()/Transport/Guard/adapters remain identical; adb 0755.

Continuation instructions for parent only (not executed here):

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-normal-ram-compute-control/source/install.py
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-normal-ram-compute-control/source/install.py --execute
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-normal-ram-compute-control/scripts/decode_compute.py /absolute/parent-owned/complete-console.txt --installed-full-sha256 9a836b53aaf66366a93f2f715c73247ae49e889cb4bce4a369655939142c04ad --fresh-stock-boot-reference /absolute/parent-owned/fresh-stock-boot-evidence
```

The decoder requires exact control values and checksum, successful initial clock and normal scheduler query. Prefix alone/stale UUID never accepts. Without both explicit fullp10 and fresh-stock-boot attestations it reports published completion pending physical binding. These arguments are parent attestations, not independent device observations. Give the parser the complete single-console horizon. IRQ/alarm records are retained separately. Private stock/root checks were omitted only in isolated PLAN memory; parent’s actual PLAN retains all original dependency checks.

Only bounded compute progress under changed timing/workload can be established. No sustained 1.5s, timer pass, clock rootcause, system stability or Android17 claim. Alarm absence is not timer failure. Missing marker stays UNKNOWN publication, never publication-failure proof or CPU lockup. Do not rerun the unchanged normal clock body, rebuild kernel, create another variant, repeat the isolated PLAN or launch follow-on work automatically. Parent owns interpretation and its single physical trial.
