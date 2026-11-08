# One sparse watchdog observation candidate

Question: can the sparse candidate publish actual generic watchdog probe, stop before/after, request configuration and restart-entry facts?

Status: **one candidate built, packaged and verified; STOP**. One first-attempt `-j8 Image.gz-dtb` build and exactly one isolated PLAN passed. No device/ADB/root/private factory/raw target-log access, execute or physical trial. Parent owns one physical trial and eventual Power fallback. VM **TERMINATED**, owned SSH master closed.

| Output | Bytes | SHA256 |
| --- | ---: | --- |
| [candidate.img](artifacts/candidate.img) | 7,989,248 | `e38c3753630b30bd3ca4d4d67ae49be130621ce7b2bf2d1774b9d78b6711b253` |
| [candidate.p10.raw](artifacts/candidate.p10.raw) | 16,740,352 | `86213b3aabb8a003ff19157ba5b1dbb29377e0cb14cd70f896fdeccbb944792b` |

[Handoff](evidence/handoff.json), [hashes](artifacts/SHA256SUMS), [scoped proof](evidence/scoped-proof.md), [233-line diff](source/changes.patch), [pre/post pins](evidence/prepost.json), [preservation](evidence/preservation.json), [PLAN receipt](evidence/plan-isolation-receipt.json), [commands](evidence/exact-commands.json).

Fresh UUID: `e0b1a1ba-ebd1-4454-a3fb-e8b05eedf5d9`. Exact compile-mode marker:

```
ASUS49-MODE run=e0b1a1ba-ebd1-4454-a3fb-e8b05eedf5d9 profile=sparse-wdt-v1 hot=disabled ordinary_printk=filtered delay=original-virtual
```

The [contract](evidence/mode-contract.json) defines the exact fresh `ASUS49-WDT run=e0b1a1ba-ebd1-4454-a3fb-e8b05eedf5d9 ` prefix and five canonical record forms. Watchdog facts can be admitted before PID1; liveness remains separate, including UNKNOWN. Missing records never prove not called. EN is one readback instant, and a symbolized caller names the immediate entry route. The retained sink can fail or perturb execution.

Continuation: parent independently binds full installed p10 readback and fresh stock boot. The guarded installer appends exactly the supplied current full p10 `8ed918339c0adcfdad461390b0316073b515b43e839ec8094975546e314f8b22`; this worker did not freshly observe it. Decode the complete parent-private console offline:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-sparse-watchdog-observation/scripts/decode_sparse.py /absolute/parent-private/complete-console.txt --system-map /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-sparse-watchdog-observation/artifacts/System.map.gz > /absolute/parent-private/sparse-wdt-result.json
```

[Genuine System.map.gz](artifacts/System.map.gz), [uncompressed SHA pin](evidence/System.map-uncompressed.json); large out/vmlinux stay on the stopped VM. No automatic retry, next unit, watchdog fix/GIC build or physical/fullOS GO.
