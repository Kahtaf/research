# Linux 4.9 stock bootargs probe

Question: does the existing corrected Linux 4.9 SD-report package produce a fresh report when its packaging uses the working stock diagnostic boot arguments?

Status: one candidate packaged locally; actual container parse, component equality, header/DT checks and default PLAN_ONLY passed. No compilation, hardware contact, recovery write, physical Linux 4.9 proof or flash GO. No other spike or Android 17 enforcing target/product source was modified.

The parent reports that the stock-kernel control booted the unchanged PID1, produced a fresh 175-byte report (SHA-256 `a258dec186b5f27912d666c9624e8d640da5a815328b23870482ff4a630f9483`) with Linux 3.18.35 / aarch64, and returned healthy Android. Its receipt is `2026-11-07-asus-stock-kernel-sd-control/evidence/report-after-trial.json`. This sub-agent did not read that receipt, raw logs or SD card. The parent reports the same ramdisk with the previous 4.9 package failed to produce a report through both manual and actual USB ADB recovery entry, then returned healthy stock Android. Cause remains unproven.

Important outputs:

- `artifacts/candidate.img`: **8,044,544 bytes**, SHA-256 `253a1cc0ab2e4119a8c77357c78fe6bec66f0fb13cba08a3488d6d3d9994ea13`.
- `artifacts/candidate.p10.raw`: **16,740,352 bytes**, SHA-256 `631cebb6df7be4b08edb713c976799ac60b4552e2caa3d4f1ea15b11a37610b9`.
- Actual container: Android boot image v0, 2,048-byte pages, 512-byte MTK KERNEL/RECOVERY wrappers, gzip Image followed by FDT; full p10 has zero padding.
- `evidence/packaging-receipt.json`: exact input/component/output hashes, header fields, DT arguments and preservation assertions.
- `evidence/install-plan.json`: actual default PLAN_ONLY output, device_contacted=false.
- `source/package_probe.py` and `source/package_probe.diff`: reproducible offline packaging and diff against the previous packaging script.
- `source/install.py` and `source/install.diff`: minimal stock-control installer specialization; exact adapter copies in `source/adb` and `source/legacy_adb.py`.

Android header command line is exactly:

```text
androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3
```

DT `/chosen/bootargs` preserves the existing console/platform prefix verbatim and replaces only its old header-argument suffix with that same exact stock command line:

```text
console=tty0 console=ttyMT3,921600n1 earlycon=uart8250,mmio32,0x11002000 root=/dev/ram vmalloc=496M androidboot.hardware=mt8163 androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3
```

Only that DT property changes. Actual initrd start/end stay `0x44000000` / `0x4404e898`, with original 32-bit cells. Kernel gzip stream and decompressed Image are byte-identical to failed `999a575cc3dcb20b92f45a8281de19d1d452ad304836b5dded93422aca9d2510`; no config, driver or ELF rebuild. Wrapped ramdisk remains exactly `51a6d8deb3368c8b8a10d6d730ca21c6b157fda5f940d5ba7cdcb2d2a6788e46` (322,200 bytes), shared with working control `eccfc87f28169bee14d0675f6ad31335f832ab25db46b013b03a06109b0df13d`. Wrapper length, Android kernel size, image ID and padding are regenerated. Addresses, page size and all other header bytes remain unchanged.

The unchanged PID1 retains PROBE.ID `dbbb6afb-dd70-4c35-961e-9c977d7164a8` plus LF, PROBE.TXT, the 60-second lifecycle and SD paths `/sys/class/block/mmcblk1`, `/sys/class/block/mmcblk1p1`, `/dev/sd-report`, `/sd`. No file permissions or policy are changed. This diagnostic command line is temporary and does not change the final Android 17 enforcing target.

Installer changes are only image hash, full-p10 hash, image length and addition of verified stock-control full preimage `4b564d404bc13b20ba44790733a37010fe0677bfced235de2b334c3bff08fa19`. `execute()` and `Transport` remain byte-identical; adapters are exact copies including their existing legacy dependency. Default remains PLAN_ONLY. Existing root/full-readback/inverse/unknown-stop behavior is preserved.

Continuation: parent owns hardware and the active Android native ordinal 8. Before an attempt, parent preserves the stock report to STOCK.TXT and proves PROBE.TXT absent. No physical preparation or inspection was done here. The exact parent install command below does not reboot; it was **not executed**:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-stock-bootargs-probe/source/install.py --execute
```

Offline reproduction (keep sibling dependencies in place):

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-stock-bootargs-probe/source/package_probe.py
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-stock-bootargs-probe/source/install.py
```

Owned local files total approximately 24 MiB, below the 48 MiB budget. No host mock suite, review, benchmarks or additional candidates were run.
