# ASUS stock-kernel SD control

Question: with the exact corrected SD-report initramfs held constant, does the original ASUS 3.18 kernel produce PROBE.TXT through the same recovery entry path?

Status: packaged locally; actual package parse/preservation assertions and default PLAN_ONLY passed. No compilation, remote work, hardware contact, or physical validation. The parent reports both corrected Linux 4.9 recovery trials returned healthy stock Android without PROBE.TXT; report absence was last observed by the parent at 12:59 UTC on November 7. This control does not establish the cause of either failure.

Important input discrepancy: the full original recovery matches the requested SHA-256 `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`, but its actual wrapped kernel is `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880` (7,472,341 bytes), consistent with the existing minimal-probe stock-input-pins.json. The supplied `7c7051c147b03ca865b3481d55cd832bc6f2732eef1c0063af9404823b0ceaa4` wrapped-kernel pin does not match that input. This package preserves the actual original kernel without modification and records the discrepancy explicitly.

Outputs:

- `artifacts/candidate.img`: 7,798,784 bytes; SHA-256 `eccfc87f28169bee14d0675f6ad31335f832ab25db46b013b03a06109b0df13d`.
- `artifacts/candidate.p10.raw`: 16,740,352 bytes; SHA-256 `4b564d404bc13b20ba44790733a37010fe0677bfced235de2b334c3bff08fa19`.
- `evidence/packaging-receipt.json`: input hashes, component equality and installer preservation receipt.
- `evidence/install-plan.json`: actual local default PLAN result.
- `scripts/build.py`: pure-Python packaging and minimal assertions; `source/bootformat.py` is the exact pinned local format helper.
- `source/install.py`, `source/adb`, `source/legacy_adb.py`: specialized installer and exact adapter copies.

The wrapped ramdisk is copied byte-for-byte from corrected candidate `999a575cc3dcb20b92f45a8281de19d1d452ad304836b5dded93422aca9d2510`: 322,200 bytes, SHA-256 `51a6d8deb3368c8b8a10d6d730ca21c6b157fda5f940d5ba7cdcb2d2a6788e46`. No recompression, kernel/DT rebuild, stock recovery binary, or stale BCB/wipe argument handling is added. The original header is unchanged except Android component sizes and image ID; page size, addresses and command line remain original.

The unchanged PID1 uses actual uname fields, the same 60-second lifecycle, read-only internal behavior, SD identity checks, removable=0 precondition and O_EXCL report creation. Paths remain `/sys/class/block/mmcblk1`, `/sys/class/block/mmcblk1p1`, `/dev/sd-report` and `/sd`. PROBE.ID remains exactly `dbbb6afb-dd70-4c35-961e-9c977d7164a8` plus LF; report is PROBE.TXT. A fresh report's actual uname is the runtime evidence: no 4.9 release constant is substituted. The packaged stock kernel differs byte-for-byte from the corrected 4.9 wrapped kernel (`a90d4a54522176f56df707dc6af1f40680ff77209da6dad7a006abeaae1d9464`).

Only four installer literals changed: image hash, padded hash, image length and addition of verified `7161898f7858c5eb2887a4589fce5a62d4b2d556e1413e36e4e53c3cd8431b09` to the existing allowed preimages. IMAGE remains ROOT-relative and therefore resolves to this spike. execute(), Transport, root/geometry/full-readback checks, single inverse, unknown-stop behavior and shared mutation lock remain exact. The inherited journal profile string still says linux49 because it was deliberately left unchanged. Local inputs use b.local_inputs(), not the Linux 4.9 candidate admission function. The exact adb shim retains its existing absolute legacy-adapter dependency in the prior wifi-microsd spike.

Continuation: parent alone handles root preparation, installation, recovery reboot and physical observation; do not boot the OEM recovery UI. This task ran only the first command below. The second is the exact parent installation command; the installer does not reboot.

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-stock-kernel-sd-control/source/install.py
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-stock-kernel-sd-control/source/install.py --execute
```

To reproduce packaging locally, run `python3 -B scripts/build.py` from this spike. Keep sibling source dependencies in place. All owned artifacts are below the 48 MiB budget; stock backups, SYSTEM and DATA are not duplicated here.
