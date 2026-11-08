# ASUS early UART disabled diagnostic kernel

Question: does disabling the unused 8250 serial console remove the early UART path associated with actual cached core0 PC `0xffffff8008f31adc`?

Status: **one native `make -j8 Image.gz-dtb` exited 0; one candidate packaged; one isolated PLAN_ONLY exited 0. No install or reboot.** Cached PC resolves in the exact baseline layout to `serial8250_early_in+0x78`, `ldr w0,[x0]`, in UPIO_MEM32 readl. Cache epoch and UART failure mechanism remain unproved; this is a candidate blocker, with no causality or full boot claim. Public finding evidence is copied under `evidence/cached-public-finding/`. Existing trial results remain in the separate trial spike.

Important outputs:

- `artifacts/Image.gz-dtb`: 7711217 bytes; SHA-256 `063dad1d9cc03b1c335dd712c9fcb0c36a006e5e99ebee4577e73e669613ac2d`.
- `artifacts/resolved.config`: 126443 bytes; SHA-256 `708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1`.
- `artifacts/candidate.img`: 8038400 bytes; SHA-256 `1d406f3416e94e54219935cb76de338e10d3155fe555baad6cb7c2e38068c95d`.
- Full p10: 16740352 bytes; SHA-256 `e965b75979e02e5514418e706f42b7874e4f72d72754864e5af0959646d2c9b0`. Actual readback is recorded. Large file stays at `/srv/android/asus-early-uart-disabled-kernel-20261107/artifacts/candidate.p10.raw`; installer constructs the identical padded bytes locally.
- Guarded `source/install.py` and `source/install.diff`.
- `evidence/RECEIPT.json`, `config-delta.json`, `config.diff`, `dependency-gate.json`, `build-status.json`, `build-receipt.json`, `linked-image-assertions.json`, `original-selected-inputs.json`, `packaging-receipt.json`, `remote-delivery.json`, `install-plan.json`, and `plan-isolation-receipt.json`.

The only intentional change is `CONFIG_SERIAL_8250_CONSOLE=y -> n`. Actual olddefconfig naturally removes `SERIAL_EARLYCON`, `SERIAL_CORE_CONSOLE` (selected by the console), and `SERIAL_8250_FSL` (depends on the console). Exactly those four values changed y to n; no other config value changed. `SERIAL_8250=y`, `SERIAL_8250_MT6577=y`, and `SERIAL_CORE=y` remain. `FIX_EARLYCON_MEM=y`, an unconditional arm64 default, remains for the unchanged retained logger's `early_memremap` support. Kconfig/Makefile evidence and selected original source copies are included.

Source was independently copied using ordinary `cp -a`, with fresh out and TMPDIR, no hardlinks to baseline and no source edits. Selected baseline files and copied source hashes remained unchanged; no full-tree rehash. Unlimited RLIMIT_AS, same toolchain/command/release `LOCALVERSION=-g717bb3c9e13c-dirty`, no supervisor timeout, no build retry. Actual linked vmlinux nm plus System.map confirm `serial8250_early_in`, early setup/write and UART earlycon declarations absent. No 8250_early.o was built. Normal 8250/MT6577 symbols and early_memremap remain. This is a config/compile assertion, without simulation or physical testing. Full source/out/logs remain on the VM under the owned prefix; local log summary pins the actual build log.

Packaging preserves the actual compiled gzip Image and raw Image, v2 markers 00/01 and checkpoint strings 05/06. It applies only inherited chosen bootargs/initrd metadata; DT source and all other DT tokens remain unchanged. Same wrapped diagnostic ramdisk SHA-256 `51a6d8deb3368c8b8a10d6d730ca21c6b157fda5f940d5ba7cdcb2d2a6788e46`, v0 header, 2048-byte pages and stock addresses. Initrd remains `0x44000000..0x4404e898`. Header and chosen args are exactly:

```text
androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1
```

Installer specialization changes only candidate/full-p10 hashes, actual image length, profile, and appends prior observed full-p10 preimage `4fb2f280ba90e9e1487b3728056a67ccd4883f918cc81a1145c100a3eb999a26`. All existing preimages remain. `execute()`, `Transport`, `Guard`, and legacy adapters are byte-identical to the immediate baseline.

One isolated PLAN invokes the actual delivered main() branch with in-memory replacements for the two inherited restricted input readers, using the pinned public baseline candidate for stock header geometry. Audit isolation blocks private/device/root-helper reads, sockets and subprocesses. Actual candidate/full-p10 hashes, length and preserved header contract pass. Private stock backups and root dependency hashes were not validated by this worker; delivered input/source guards remain unchanged for root execution.

Continuation: root owns fresh USB identity/report absence, p10-only install/readback, one USB recovery entry and actual log/report collection. Next root command, under its standing authorization:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-early-uart-disabled-kernel/source/install.py --execute
```

This installer does not reboot. Do not rerun prepare/build scripts: existing owned attempts are refused. No device, card, ADB, root-helper, private-input access, cloud lifecycle/process inspection, other-worker/AOSP changes, subagents, independent review or broad suites occurred. Original BOOT/SYSTEM/DATA, frozen artifacts and existing VM/disks/labels were not modified by this worker. Local public delivery stays below 32 MiB and is pinned by `SHA256SUMS`.
