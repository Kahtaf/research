# Early retained checkpoint kernel probe

Question: can the full retained-trace e9 Linux 4.9 kernel publish a guarded record before paging and retain it when switching to the linear mapping?

Status: **one full independent Image+DTB build exited 0; actual recovery candidate packaged; default PLAN_ONLY passed once. No physical trial.** Stock retention/reader transport was physically proven by the parent in the retained-report-control spike; this does not prove 4.9 execution or guard passage.

Important outputs:

- `artifacts/candidate.img`: 8,044,544 bytes, SHA-256 `2a0d400811292ece957bb00f632f56aef8e5967643bd5a0184c10eaeea051533`.
- `artifacts/Image.gz-dtb`: 7,716,951 bytes, SHA-256 `d94b26f4e806a0c86b28e42c7a8e7590bfefa96b5c91a50f3a80a05445c867b2`.
- `artifacts/resolved.config`: 126,511 bytes, SHA-256 `0fddb41316305c672b0afd0a64b2615c6dae3c5727f5ff4ead791272ff71b696`. Entire resolved file is byte-identical to the baseline.
- Full padded p10: 16,740,352 bytes, SHA-256 `c9d4506c90fa12f6a77a5e34368312307903eb9e0c04d47d5461f2e455b062e3`. Kept on VM as `/srv/android/asus-early-retained-kernel-probe-20261107/artifacts/candidate.p10.raw`; parent installer constructs these exact padded bytes locally in memory.
- Compiled DT SHA-256 `a099d0538b270e23ec0d034b507eef9248252a3c459a11aa70edb6520bfd2b77`; packaged DT SHA-256 `49ae75d4ee2e667a7242dae9d1fb659ffca7d82bda967956e8c00b14dde9d5f0`. Only chosen bootargs and initrd cells change from the compiled DT.
- `source/early-retained-checkpoint.patch`, `source/final/`, `source/install.py`, `source/install.diff`; `evidence/RECEIPT.json`, `build-status.json`, `build-receipt.json`, `Image.gz-dtb.log`, `packaging-receipt.json`, `install-plan.json`, `early-api-assessment.json`, `early-api-source.json`, `layout.json`, and `remote-delivery.json` record actual inputs and outputs.

Release: `4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty`; actual build version `Sat Nov 07 15:40:13 UTC 2026` (#1 SMP PREEMPT). No Git metadata manufactured.

The only source change is the exact three-file supplemental patch SHA-256 `2991e2f9fdab79af5d87783fec3f3e7f0721cb8911df9f172c355d272489643d`, applied with `--fuzz=0` after all three exact preimage pins matched, with no offsets or compile corrections. The source was copied only from preserved `/srv/android/asus-retained-trace-kernel-probe-20261107/kernel` using ordinary `cp -a`, without hardlinks or old output reuse. Existing retained v1 hooks, timer clk13m fix, prior port work and all other source/hardware settings are inherited. One `make -j8 Image.gz-dtb` ran with a fresh owned `out`, complete unchanged config, and unlimited RLIMIT_AS. The build log records 24 warnings and zero errors. Full source, output and actual build log remain under the new VM prefix. Original selected input pins remained unchanged; no full-tree rehash.

The early API check found flat-DT calls valid before unflattening, completed memblock/initrd/reserved-memory setup at this call site, and normal-cacheable `early_memremap`/unmap support through generic ARM64 headers. Every original guard and the payload-before-size PoC publication remain; extra bounds limit the first record and reason area to one 256 KiB mapping. The temporary pointer is cleared and mapping removed before paging. Late initialization revalidates the guards and exact early record. No OEM headers were invented or bounds weakened.

The same static diagnostic SD-report ramdisk is preserved byte-for-byte: SHA-256 `51a6d8deb3368c8b8a10d6d730ca21c6b157fda5f940d5ba7cdcb2d2a6788e46`. It uses `PROBE.TXT`, run ID `dbbb6afb-dd70-4c35-961e-9c977d7164a8`, and the inherited 60-second normal reboot lifecycle. Header and complete chosen bootargs remain:

```text
androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1
```

The DT's 32-bit initrd cells describe the wrapper-stripped compressed payload `0x44000000..0x4404e898`; no initrd bootarg. Actual new compiled Image bytes are preserved in the package. MTK wrappers, Android v0/2048 layout, addresses and all other header/DT fields remain under the inherited contract. No finalBOOT/product/audio kernel substitution; charging permission remains absent.

The installer is minimally specialized from the retained-probe adapter: exact new image length, candidate/full-p10 hashes and profile, plus only the exact parent-known preimage `a0e4856da4138dd401461add3104005fca67cf495da1a605c02392244dd757f8`, fully readback verified in parent run `a1c59781-d116-4fb2-a6f8-35fa37871452`. Every existing allowed preimage remains. `execute()` and `Transport` and both legacy adapters remain byte-identical. Full guarded readback, shared lock, bounded inverse, uncertainty-stop behavior and sibling source dependencies remain. Actual default PLAN_ONLY ran once, with `device_contacted=false`; no `--execute` was run.

## Parent continuation

Parent alone verifies fresh report absence, runs the guarded installer, owns one recovery reboot and safe normal return, then immediately collects complete actual last_kmsg plus exact candidate/install/boot identity and fresh SD report. Installer path: `/OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-early-retained-kernel-probe/source/install.py`. It does not reboot. No added review gate or alternative candidate.

Expected records:

```text
ASUS-e9-retained-v2 00 arm64_memblock_init returned; before paging_init
ASUS-e9-retained-v2 01 paging_init returned; trace ready
```

Inherited later v1 markers 02..06 and printk capture remain. Record 00 without 01 proves reaching the pre-paging checkpoint, but can still allow failure during paging, later guard revalidation or retention. No record permits earlier failure or guard refusal and does not prove nonexecution. Stock retention evidence proves the stock path only.

This worker made no device/card/ADB/root-helper call, private logs/factory/calibration/DATA access, active AOSP/product/source/out edit, other-owner process inspection/signals, cloud lifecycle action or subagent. The separate vendor-BPF worker is untouched. VM labels/disks and previously scheduled November 8 ~14:54 UTC stop were not changed.

For continuation, use the actual delivered candidate and receipts. `scripts/build.py` refuses an existing owned source/output and must not be rerun as a second build. `source/package_probe.py` reproduces packaging offline without compilation. Local public delivery is below 32 MiB; padded p10 stays on the VM.

`SHA256SUMS` pins the complete local public delivery. Actual candidate and padded p10 were read back on the VM with matching lengths and hashes; see `evidence/remote-delivery.json`.

## Parent physical result

Installed fullp10/readback/cleanup verified99a72150...; oneWiFiRecoveryrequest sent (host12secondtimeout/UNKNOWN). Previousstocklog independently records rebootcommandrecovery. WiFi-onlyobserver reconnected the existinghostendpoint and verified newnormalAndroidbootbf1566ca-25aa-4eec-96bd-6851f7fafdee, without device tcpip reset or USB action. Complete523005byte retainedlog has no v2checkpoint; freshSDPROBEabsent. No4.9execution/nonexecution or exclusivecause claimed.

Actualhost entry/query interval minus currentnormalstockuptime estimates33.075..33.341seconds outside the newstockkernel, compared with the diagnosticPID1 nominal60seconds. Assumptions and limits: evidence/return-timing.json. Actualcmdline containsboot_reason=4, whilepropertysys.boot.reason=0; enum/resetsemantics need exactsource interpretation. Config enablesgenericMEDIATEK_WATCHDOG andMTK_WD_KICKER, butlegacyMTK_WATCHDOG/COMMON areoff. This motivates a source-backed early-reset/watchdog investigation, not a speculative watchdog disable. Publicphysical-result.json records scope. RootprivateRAMlog and rawcmdline remain private.
