# One PID1 FIFO loop control

Question: can the existing runnable RAM loop publish progress during a temporary, verified SCHED_FIFO priority 1 interval, then restore its saved normal policy?

Status: **one candidate packaged; STOP**. One static helper compile, one incremental `-j8 Image.gz-dtb` build and one isolated installer main() PLAN passed. No tablet/ADB contact, install, reboot, private factory payload or target-log reading. Parent owns actual PLAN/install/one physical trial. Owned SSH master closed; exact existing VM verified **TERMINATED**.

| Output | Bytes | SHA256 |
| --- | ---: | --- |
| [candidate.img](artifacts/candidate.img) | 7,993,344 | `0b2593007bbd475bd10534e03e095f7ddc23d4c09d408a788e70c5ac7d757d72` |
| [candidate.p10.raw](artifacts/candidate.p10.raw) | 16,740,352 | `6f5577f7330754c43c52ad4e522fd487fd1cb4d56331991684f8515b03eba353` |

Kernel UUID `f53fadc2-5cd5-4c44-b5a3-7a65567c6935`; helper UUID `ef56ad88-6904-4452-90a1-3744beaa3c78`. [Handoff](evidence/handoff.json), [source delta](source/changes.patch), [pre/post hashes](evidence/prepost.json), [focused proof](evidence/scoped-proof.md), [binary/source checks](evidence/focused-checks.json), [package/preservation](evidence/packaging-receipt.json), [PLAN limitations](evidence/plan-isolation-receipt.json), [exact System.map.gz](artifacts/System.map.gz).

The exact base is `2026-11-08-asus-sparse-watchdog-observation`, full p10 `86213b3aabb8a003ff19157ba5b1dbb29377e0cb14cd70f896fdeccbb944792b`, kernel UUID e0b1a1ba. This is the parent's supplied physical-current pin, **not freshly observed here**; it is appended to installer admissions. Extracted baseline helper/source are bound by the prior compiler receipt. Full config pin remains `708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1`.

After successful initial direct clock sample, direct scheduling syscalls save actual policy/param and refuse anything except SCHED_OTHER/priority 0. FIFO priority 1 requires rc 0 and observed policy/priority 1/1. At most three progress writes occur at 500k/1M/1.5M. The original 2M-call or >=1.5-counter-second loop exits, alarm, direct clock path and other helper operations remain. Every returning loop exit joins immediate restoration before final/after IRQ/MMC routines. Failed/unverified restore emits invalid and routes directly to existing finish/reboot without retry or fake acceptance. Boost failure/mismatch also invalidates and restores before finish. Original baseline refusal never boosts. This candidate does not perform storage work while RT.

Only fresh kernel identification and exact sparse scheduling/progress admissions changed in kernel code. Hardware/watchdog/PMIC/thermal/charging/clock/delay/RDMA behavior and disabled hot observers remain. Compiled DT/config are byte-identical. Runtime DT changes only actual `linux,initrd-end`; wrappers, header, hashes and padding follow actual payload lengths. Delivered gzip is 257,913 bytes, actual end `0x4403ef79`, unchanged guard `0x4403f007` (142 bytes spare).

Reflink was unsupported. Parent authorized independent full copies after metadata-only space confirmation; no hardlinks/shared mutable out/source, new disks/cloud assets or cleanup of other work. Copies and nested repositories were preserved; original scoped pins/inodes/mtimes verified. vmlinux/out stay at `/srv/android/asus-pid1-fifo-loop-control-20261108-f53fadc2/{kernel,out}` on the stopped VM. Local gzip recompression differed during preflight; the already-checked remote gzip was retained and its exact decompressed cpio verified. No recompilation or candidate variant followed.

The one isolated PLAN used documented restricted in-memory substitutions for public stock-header geometry and public code pins. Private stock/root dependencies were deliberately not verified. Delivered execute()/Transport/Guard/adapters remain byte-identical and adb 0755. Parent's actual PLAN retains its full existing dependency checks.

Parent continuation commands (provided for review; execute/trial were not run here):

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-pid1-fifo-loop-control/source/install.py
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-pid1-fifo-loop-control/source/install.py --execute
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-pid1-fifo-loop-control/scripts/decode_fifo.py /absolute/parent-private/complete-console.txt > /absolute/parent-private/fifo-result.json
```

Bind exact full installed p10 and fresh stock boot using the parent's existing trial flow. Installer does not dispatch recovery reboot. Use the already-accepted eventual manual Power fallback. Do not rebuild, rerun isolated PLAN, create another variant or start another trial automatically.

Marker/parser contract:

```text
ASUS49-MODE run=f53fadc2-5cd5-4c44-b5a3-7a65567c6935 profile=sparse-fifo-v1 hot=disabled ordinary_printk=filtered delay=original-virtual
ASUS49-SYSCLOCK run=ef56ad88-6904-4452-90a1-3744beaa3c78 phase=observe ...
```

Require one fresh entry/mode, PID1/release and initial direct clock records. `sched.original` rc is the **actual policy**, with actual getparam rc/errno/priority in value. `sched.boost` rc/errno is the **setscheduler result**; `sched.boost.observed` rc is the separately queried policy. Expected original=0/priority0, boost rc0, observed=1/priority1. `sched.restore` records actual restore rc/errno; `sched.restored` must report actual policy0/priority0 and successful getparam. `stage=accepted op=sched.control` follows verified restoration, preceding final/after records. `stage=invalid` refuses clean acceptance even if other rc values are zero. The parser rejects duplicate/stale/mismatched records; five focused synthetic controls cover acceptance, absent restore, restore failure, wrong observed policy and stale identity.

A published progress record following valid observed boost is **conditional evidence of execution**. It is not final acceptance without actual restoration. Missing final records yield UNKNOWN, including possible publication loss. A verified iteration cap is progress, not a timer pass. Counter-target/alarm/complete before-after IRQ growth remain separate facts; no calibrated walltime, exact 250 Hz ratio or timer-deadness assertion. A direct clock syscall may stall indefinitely. RT bandwidth source defaults (1,000,000/950,000 us) were not tuned or measured live; normal-priority work, including protection work, can be delayed. Even success does not establish a scheduling root cause or offending worker. No automatic storage-under-RT or fullOS advance. Return the single physical result to the parent for interpretation.
