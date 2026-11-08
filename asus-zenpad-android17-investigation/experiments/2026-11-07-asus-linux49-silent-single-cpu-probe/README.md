# Linux 4.9 silent single-CPU probe

Question: does removing inherited console/earlycon arguments and limiting secondary CPU bringup together let the unchanged SD-report PID1 run? These are combined diagnostic changes; a result cannot establish an exclusive cause.

Status: packaged offline from the exact prior 253a candidate; packaging assertions and actual default PLAN_ONLY passed. No device/card contact, compilation, private log/data reads, active Android job inspection, physical Linux 4.9 proof, or final product source changes.

Important outputs:

- `artifacts/candidate.img`: **8,044,544 bytes**, SHA-256 `827d338c1733665c5adb40daa4a20505ec9ca7e2e586decd6069e2299bf4e062`.
- `artifacts/candidate.p10.raw`: **16,740,352 bytes**, SHA-256 `ad32e78548ec22d03685839858bcbccd163465125d4fe7c6b68f86dd19f65982`.
- `evidence/packaging-receipt.json`: actual component/header/DT hashes and preservation assertions.
- `evidence/install-plan.json`: actual default PLAN_ONLY, device_contacted=false.
- `source/package_probe.py`, `source/package_probe.diff`: offline packager and diff against prior 253a packager; exact prior `bootformat.py` and `fdt.py` copies.
- `source/install.py`, `source/install.diff`: minimal prior installer specialization. Only image hash, full-p10 hash and the allowed-preimage tuple change; image length remains 8,044,544 bytes. The actually installed prior full hash `631cebb6df7be4b08edb713c976799ac60b4552e2caa3d4f1ea15b11a37610b9` is appended alongside the existing stock/780/716/4b entries. `execute()` and `Transport` remain byte-identical. `adb` and `legacy_adb.py` are exact prior copies, including their legacy dependencies and transport behavior.

Android header cmdline and the entire DT `/chosen/bootargs` are both exactly:

```text
androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1
```

The inherited chosen prefix is removed entirely, including tty0, ttyMT3, earlycon, root, vmalloc and androidboot.hardware arguments. No DT property other than bootargs changes. Actual initrd cells remain 32-bit `0x44000000` / `0x4404e898`.

Preserved components:

- Compressed Image: 7,653,276 bytes, SHA-256 `6e445d5000ad1d8dba7dd947945f2db417c45800a6036b995340b9ffc3b57b6d`.
- Decompressed Image: 17,345,024 bytes, SHA-256 `43ee0529e371575bfaddb9de392b77a2279cb44bc60649fcd8d9a88b6e613b09`.
- Exact wrapped ramdisk: 322,200 bytes, SHA-256 `51a6d8deb3368c8b8a10d6d730ca21c6b157fda5f940d5ba7cdcb2d2a6788e46`.

The unchanged static SD PID1 retains run UUID `dbbb6afb-dd70-4c35-961e-9c977d7164a8`, `PROBE.TXT`, permissions/policy and the 60-second lifecycle. No driver/config/kernel Image bytes or compiled code change. MTK wrapper length, Android kernel length, Android ID and zero padding are regenerated from the actual modified DT container. Other header bytes and wrapper bytes are preserved.

Parent-provided context: exact stock 3.18 plus this ramdisk booted PID1, wrote 175 bytes and returned; corrected 4.9 and the prior 253a experiment returned without a fresh report. Current host config is reported as SMP=y, HOTPLUG_CPU=y, MTK_PSCI=y, ARM_PSCI_FW=y, SELINUX_BOOTPARAM_VALUE=1, CMDLINE_FROM_BOOTLOADER=y; MTK_RAM_CONSOLE is absent, so retained stock logs do not prove any 4.9 stage. None of that source/job or physical evidence was inspected here. Single CPU is diagnostic and does not narrow final Android 17 scope or prove finished hardware support.

Continuation: root owns physical work through stable USB ADB. Root reports STOCK.TXT and host evidence are preserved and PROBE.TXT absence was reverified at 13:19 UTC; root must check absence again before trial. This worker never accesses the card. The inherited installer retains its prior legacy transport; it does not itself implement a new USB transport or reboot.

Exact parent install command, **not run by this worker**:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-silent-single-cpu-probe/source/install.py --execute
```

Offline reproduction (keep prior sibling dependencies):

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-silent-single-cpu-probe/source/package_probe.py
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-silent-single-cpu-probe/source/install.py
```

Owned files total about 24 MiB, below 48 MiB. Only packaging assertions and one actual default plan were run; no additional tests, review, audit or benchmarks.
