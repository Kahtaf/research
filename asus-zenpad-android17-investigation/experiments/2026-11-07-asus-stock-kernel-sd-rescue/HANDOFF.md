# Parent handoff: stock 3.18 CHECK

Status: built and locally checked; **no final candidate assembled or physical qualification claimed**. The private five-role manifest, arm, DATA, calibration, device/card, and internal block tables were not opened. All existing source-spike baseline pins still match. No children, full kernel/platform build, VM lifecycle action, or existing process management was performed.

The new compiler fixture is `/srv/android/asus-stock-kernel-sd-rescue-20261107`, accessed through the existing product-kit helper. Compilation is serial on one CPU with a 95 MiB address-space limit. Final measured owned allocation is in `evidence/resources.json`; no parent manifest or arm is uploaded.

## Local join

Parent sets `ACTUAL_FIVE_ROLE_MANIFEST` and `EXISTING_ARM_FILE` to the genuine existing local files, then runs:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-stock-kernel-sd-rescue/scripts/assemble_check.py \
  --manifest "$ACTUAL_FIVE_ROLE_MANIFEST" \
  --arm-file "$EXISTING_ARM_FILE" \
  --output-dir /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-stock-kernel-sd-rescue/artifacts/check-physical-01
```

The destination must not exist. The assembler checks the full delivered input pins, the original-pair prefix, all existing five-role admission gates (including final DATA identity), and the parent-reported actual manifest SHA-256 `9fe4ec15800257262092f11698525939ebdfb404e150fbc7d308c7f8280ba534`. It requires the existing nonzero arm syntax but CHECK never uses it to select or authorize execution.

It reads only the specified local inputs plus the pinned original recovery at `2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin`. The complete original recovery must hash to `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`. Its exact 7,472,341-byte wrapped kernel is retained: `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`. The Android header changes only component sizes and image ID; original addresses and bootargs stay intact. The MTK kernel wrapper is exact; the original RECOVERY wrapper changes only its payload size. No kernel/DT modification occurs.

Outputs are the actual `candidate.img`, fixed-size `candidate.p10.raw`, `check-ramdisk.members`, `manifest.sha256`, and `assembly.json` containing their actual hashes and preservation assertions. No mode file or execution trigger is emitted. Assembly does not install, reboot, touch a device/card, or launch a transport. Parent handles any reviewed deployment separately using the actual resulting image/full-p10 pins.

## CHECK runtime

The common rootfs remains nonoperational until a final join. CHECK assembly replaces the normal launcher and frontend at their already-labeled paths, removes the offline selector service and p10 helper, and adds only the CHECK startup. It removes the absent helper from the explicit restorecon command, preserving all other real targets. Existing init, SELinux policy, compiled contexts, daemon protocol and binding formats are unchanged.

The runner waits up to 30 seconds for the real root daemon's exclusive ready publication, matching its RAM manifest hash. It discovers the fixed SD for up to 60 seconds and mounts only `/dev/block/mmcblk1p1` (179:129), after shared independent sysfs validation of SD 179:128, removable=0, type SD, the exact 31,116,288-sector disk, partition ancestry and containment, and internal-device separation. The mount retains VFAT, nodev/nosuid/noexec, UID/GID 2000, and the existing fixed SELinux contexts. If daemon readiness failed, mounting is used only for a diagnostic and no client is started.

`SDCHECK.TXT` is created exclusively at the card root. An existing file is never replaced or counted as fresh success. The file contains actual runtime uname, stages, the real frontend output, actual waitpid exit/signal status, and the final outcome. Total size is bounded to 16 KiB; the child's hard 12 KiB file-size limit reserves room for the runner's final report. Shell writes directly to the existing `rescue_sd_file` type because stock policy denies init-owned pipe writes; the relevant actual permission queries are retained.

The runner launches the **same frontend source's real PLAN path** with no arguments, UID/GID 2000, empty supplementary groups, explicit `u:r:shell:s0`, and enforcing SELinux. The CHECK build rejects all command arguments, compiles out the execution branch, and additionally rejects every daemon request except zero-payload STATUS before I/O. It generates no prospective execution trigger. Normal PLAN's immutable RAM manifest, authenticated daemon/run binding, source directory shape, actual card manifest binding, exact chunk length/type/device, omitted-zero chunk hashes, and full reconstructed SYSTEM/DATA/BOOT hashes remain required. The source roles are 2,4,3; the ~15.1 GB logical source is fully reconstructed and hashed. This does not reread internal targets or prove their contents.

The existing PLAN precondition `/asus-rescue-report` **must exist on the card**, even though PLAN creates no attempt report there. A missing directory or any bad source yields a real nonzero client result in `SDCHECK.TXT`. The parent reports that both card `manifest.sha256` files are already correct and no mode/trigger exists; this implementation did not observe the card.

The PLAN deadline is 600 seconds after child launch. Timeout kills only the restricted CHECK child, waits up to five seconds for reap, and records failure without asserting exit0. It never stops a daemon/writer. The runner makes no writer requests, inverse, trigger lookup, automatic retry or selector lookup. Known exit0 plus complete real preflight is required for PASS; reporting/sync errors cannot create a positive client result. It syncs the report, directory and filesystem, then normally reboots after success and safe CHECK failures. A sync failure leaves the session for the parent's known Power fallback. Discovery plus preflight/reap is nominally bounded to ~695 seconds; a blocked kernel I/O, failed init/policy/exec, or reboot failure still requires that already-known manual Power fallback. No interactive root console, adbd or network is included.

## Evidence and retained safeguards

Three focused behavior groups passed:

1. Synthetic sysfs: correct stock SD accepted; former 4.9 device number and wrong MMC type refused by both identity/mount checks.
2. Real frontend helpers: STATUS wire accepted, write opcode rejected before I/O, omitted-zero/full reconstructed source verified, corruption and unexpected directory entries refused.
3. Real child processes: actual exit0, nonzero exit7 and deadline/SIGKILL produce the correct wait result and report; timeout cannot become success.

Six actual static AArch64 ET_EXEC binaries compiled with warnings as errors. ELF program headers have no interpreter/dynamic dependency. `evidence/build-log.json` contains commands/results. `evidence/local-check.json` verifies actual common cpio contents, unchanged baseline files, byte-identical policy/contexts, CHECK restorecon targets/startup, and a conservative full-maximum-manifest packaging bound of 14,503,936 bytes within p10's 16,740,352 bytes. No synthetic manifest/arm/candidate or candidate hashes were created for testing. The real parent's final join must execute the final packaging/roundtrip preservation assertions.

Normal/stock common-core adaptation is retained for future qualification. All SD st_dev/rdev guards, including the p10 helper's inherited source FD, use stock minor129. Internal mmcblk0p9/p10/p25/p26 geometry and identity, chunk and full target readback, recovery stability, writer lifetime lock/retirement transfer, deliberate rollback/inverse rules, exact original pair and p10/container proofs are unchanged. `source/current_binding.h`, `prior_container.h`, `restore_core.h`, `recovery_phase.h`, `lock_transfer.h`, original stock pins and wire formats match the prior core. CHECK omits the p10 helper from its image. The separate normal `scripts/final_package.py` now expects the exact **wrapped stock kernel** as `--kernel`; its production paths remain physically unqualified.

`artifacts/ARTIFACTS.json` gives all actual hashes. `evidence/DELIVERY_PINS.json` pins delivered source/input/products. `evidence/source.patch` compares the copied baseline; `evidence/runtime.patch` focuses runtime changes plus the new runner/startup. `evidence/stock-inputs.json` records actual public stock component pins and original bootargs. The successful old stock-kernel PID1 probe establishes its own boot/uname observation; this new Android-init/daemon/full-SD-hash profile still requires the parent's physical CHECK trial. No static 2 MiB failure premise is assumed or investigated.
