# Complete BMC156 physical ARM64 kernel receipt

Completed a genuine clean full `Image.gz-dtb` build from the exact compiled physical r5 source plus the unchanged completed BMC156 port. **Compile exit: 0. No product integration or physical hardware qualification is claimed.**

The local deliverable is `artifacts/Image.gz-dtb`, 7,716,897 bytes, SHA256 `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`. `artifacts/resolved.config` is `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`. The appended DT is byte-identical to physical r5: `a099d0538b270e23ec0d034b507eef9248252a3c459a11aa70edb6520bfd2b77`. The large source tree, objects, raw Image and vmlinux remain in `/srv/android/asus-bmc156-full-kernel-r1` on the existing VM.

## Reconstruction and source scope

This is an owned kernel BUILD FIXTURE, not another agent checkout/workspace. The exact pinned `active-soc-source.tar.gz` reconstructed the 61,976-file baseline at commit `717bb3c9e13ce573cfdd2dda856debd27a0fa17f`. All 268 r5 combined-delta preimages were verified before extracting the exact pinned `combined-source-changes.tar.gz`; every resulting postimage and all 62,224 r5 regular source files matched the full receipt and original compiled fixture. Repository metadata was not copied or changed, and no source hardlinks were used.

The accelerometer patch applied with `git apply`, exact preimage/postimage verification, and no offsets or fuzz. Its hash remains `1f40942ee014bda87c4e4c382b881e27c98b2034b227a06020a7e96126399cec`. There are exactly nine changed source paths, including four new OEM-port files, producing 62,228 regular source files. **No additional kernel source fix was needed.** Original source files were checked again after the build. The compressed full r5 manifest plus nine-file postimage manifest reconstruct the full final source manifest; its canonical digest is recorded in `SOURCE-PINS.json` and independently checked locally.

An initial reconstruction assertion accidentally included original `.git` metadata in a source-only comparison. It stopped before patch/build launch. The corrected verifier excluded repository metadata and resumed from the verified r5 reconstruction. The failed recipe and error explanation are preserved locally. This was a verification-script correction, not a kernel source mismatch or a compile retry.

## Actual compile

The sole full compile ran from 2026-11-06T20:45:30.744549+00:00 to 2026-11-06T21:18:01.746895+00:00 (1951.0 seconds), `make -j1` on CPU 0 with nice 10. It began with an empty output tree and the complete original physical resolved config, never a virtual-fixture config. Existing GCC 13.3.0/binutils/host tools were used; executable paths, hashes and versions are in `evidence/toolchains.json`. No packages were installed.

The exact command, PID, start/end timestamps and per-command exit codes are in `evidence/build-status.json`. The complete compiler/link/compression/DT log is `evidence/Image.gz-dtb.log.gz`; it includes 24 warning diagnostics and was not filtered to conceal them. Compiler warning flags were not relaxed by this task. The output is a fully linked AArch64 vmlinux with no undefined symbols, a real raw ARM64 Image, gzip compression, and one complete appended board DT. This is not an object-only or symbol-stub result.

The release remains `4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty`. The explicit make `LOCALVERSION=-g717bb3c9e13c-dirty` carries forward the pinned r5 suffix without fabricating a Git checkout; generated compile metadata records this build separately. `compile.h`, `utsrelease.h`, the complete System.map on the VM, selected linked symbols locally, and all artifact hashes are retained.

## Preservation and limits

Only four resolved configuration values differ: `CONFIG_CUSTOM_KERNEL_ACCELEROMETER` and `CONFIG_BMC156_ACC` n→y; `CONFIG_MTK_BMA253` and `CONFIG_MTK_MC3416` y→n. The final embedded config exactly equals the exported resolved config, including the entire inherited option set.

All 58 core runtime options and 282 protected source files, 290 scoped firstboot source files and 134 selected firstboot options, and 16 network options remain exact. The complete source manifest also preserves all original combined charging/radio/network changes. All 18 selected r5 runtime/radio/charging/network linked symbols remain present with their expected symbol types; the real BMC156 callbacks are linked too.

The DT, its reservation map, static and dynamic reserved-memory definitions and all board properties are unchanged. `asus,allow-battery-charging` remains absent. ARM64 text offset, flags and reserved header fields are preserved; allocated Image size increases by 4,096 bytes, from 18,837,504 to 18,841,600 bytes; the raw Image grows from 17,340,928 to 17,345,024 bytes. The actual new header and unchanged parent ramdisk/DT placements have no static overlap and fit the DT's declared RAM bank. Runtime LK memory/framebuffer placement remains untested. No BOOT repackaging or new physical probe was made.

`evidence/full-verification.json` passed 37 remote full-kernel/source/config/DT/layout checks. The original accelerometer bundle passed 223 checks before work. PASS 153 local bundle/hash/ARM64/config/source-preservation checks; no physical or full-product claim

The exported payload is 11,396,543 bytes across 52 pinned files, excluding local report/helper metadata. The first export with a full compressed System.map remains preserved on the VM; the smaller local export retains its exact pin and selected symbol receipts. Transfers were hash-verified, using only the authorized SSH helper and identity path. The frozen r2 kit seal remains unchanged; active AOSP r5 supervision/build, original physical kernel, old accelerator fixture and frozen artifacts were not modified or managed.

## Parent continuation

`parent-delta.json` and `HANDOFF.md` specify the smallest future candidate change: nine exact kernel source paths, the complete resolved config, the new prebuilt Image, and corresponding regenerated receipts/pins. Apply only to a future parent-owned candidate under the parent's original integration gates; frozen r2 stays frozen. No r6/Soong/Ninja/full-product build was started.

The HAL/service Soong integration, init/ueventd, policy/VINTF/ELF whole-product validation, private original calibration restoration, real sensor behavior and autorotation remain future work. No device, ADB, USB, root, reboot, flash, private calibration/key-content read, cloud lifecycle/resource operation, display/radio/charging/sensor physical test, or physical GO occurred.
