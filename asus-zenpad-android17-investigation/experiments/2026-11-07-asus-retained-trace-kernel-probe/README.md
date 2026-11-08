# Retained trace + APXGPT diagnostic kernel probe

Question: can the full e9 Linux 4.9 fixture with the delivered retained startup logger and named APXGPT clk13m selection produce a recoverable execution boundary?

Status: full independent build exit 0; packaged recovery-only SD-report probe; actual default PLAN_ONLY passed. Physically untested. No device, ADB/USB, card, root helper, private DATA/calibration/table access, cloud lifecycle, process management or other-job contact occurred.

Important outputs:

- `artifacts/Image.gz-dtb`: 7,716,337 bytes, SHA-256 `81792d8df329f20d927325e3b46b6bd1c991742db25c6d0695f2e837c7755bc3`.
- `artifacts/resolved.config`: SHA-256 `0fddb41316305c672b0afd0a64b2615c6dae3c5727f5ff4ead791272ff71b696`. The only resolved delta is `CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE=y`.
- `artifacts/candidate.img`: 8,044,544 bytes, SHA-256 `189b64559cb8bb961301b54d21f4f2eafab84ef3494268635973c47b387811eb`.
- `artifacts/candidate.p10.raw`: 16,740,352 bytes, SHA-256 `553fae1260272ef5f161a0a468cb4c5683f8ab479db29c3ba7df82d97a8eb481`.
- `evidence/RECEIPT.json`, `build-status.json`, `build-receipt.json`, `changed-source-pins.json`, `original-selected-inputs.json`, `log-summary.json`, `layout.json`, `packaging-receipt.json` and `install-plan.json` preserve actual pins and checks.
- `source/install.py` is the minimal preserved installer. `execute()` and `Transport` and both legacy adapters are byte-identical to the silent single-CPU parent. Its new actual image length/hashes and profile are bound; only full preimage `5c8926304eaf38bbe9e2d5e8750c89cda025ce376c0103d3589f416e213cb453` is added alongside inherited pins. Original `902b` remains admitted. The inherited Wi-Fi transport and sibling dependencies remain required.

Release: `4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty`. Actual new build timestamp: `Sat Nov 07 14:20:45 UTC 2026`. No Git metadata was manufactured. The existing full e9 source was copied with ordinary `cp -a` into `/srv/android/asus-retained-trace-kernel-probe-20261107/kernel`; all make/config outputs are in the new `out`. Full source/out/logs remain there. The previous 276 source port delta and e9 config are inherited intact; selected original source/config/Image/generated inputs were checked unchanged. No full-tree rehash sweep was performed. Original/frozen/active/AOSP/product sources and output were not changed. Build used `-j8` with all 16 CPUs available and no artificial memory cap.

Both exact delivered patches were applied: retained trace `a0efbb7dee1688b07b0accebb8ef7f22a183fd58752aad9447bf89f1ba78cdbb` and timer clock `13294c10548d583e7fa86a4010fd3455822e3ba012a001cb40a6ecb1378d0816`. The timer postimage is `0c9e26f54ecbbdd8d60c9ed35cbfb62820b6a515ef25d0750fd16c3834db2913`; named `clk13m` replaces index 0 while the separate bus gate remains. It is not a proven boot cause.

The exact unchanged static SD-report wrapped ramdisk is SHA-256 `51a6d8deb3368c8b8a10d6d730ca21c6b157fda5f940d5ba7cdcb2d2a6788e46`. It still reports actual getpid/uname, uses `PROBE.TXT`, UUID `dbbb6afb-dd70-4c35-961e-9c977d7164a8`, and the inherited 60-second lifecycle. Both header cmdline and complete chosen bootargs are exactly:

```text
androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1
```

There is no initrd token. The 32-bit DT initrd cells describe the wrapper-stripped compressed payload `0x44000000..0x4404e898`. The actual new compiled Image stream is unchanged in the package; the actual compiled DT changes only chosen bootargs and initrd cells. Android v0/2048 pages, other header bytes, addresses and MTK wrappers are preserved, with actual lengths/ID regenerated.

Continuation: the parent owns fresh PROBE.TXT absence verification and the physical trial. Only the parent may run:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-retained-trace-kernel-probe/source/install.py --execute
```

That installer does not reboot. After verified install, parent owns ONE `adb reboot recovery`, the return to stock, and immediate stock `last_kmsg` collection with exact candidate/boot identity. Look for `ASUS-e9-retained-v1 01 paging_init returned; trace ready`, then markers 02..06 around setup_arch, IRQ and time_init. First marker is after paging and before IRQ/timer initialization. Missing markers can mean an earlier failure, refused memory/header guards, or lost retention; absence does not prove Linux never executed. Retention and startup remain physically untested. Parent-reported stock 3.18 SD probe works; e9 SD and independent USB probes have not produced a 4.9 report.

The full compile logged 24 warnings and zero errors; the warning details are retained in `log-summary.json`. The APXGPT object is exactly 8,536 bytes / `19893e566b1e527894299b07a2951a76e3cfde0d888f080075c04565b06a8cdb`, matching the prior isolated object result. ARM64/container layout and nonoverlapping kernel/initrd/retained-region bounds passed.

Only one actual default PLAN_ONLY was run. No execute command, reboot, physical GO, Android BOOT/SYSTEM/DATA product change, other kernel fix or subagent was used. The separate stock SD rescue worker/prefix remains untouched.
