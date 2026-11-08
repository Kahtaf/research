from pathlib import Path
import json,hashlib,gzip,datetime,subprocess,sys
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text())
def sha(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
v=read('evidence/full-verification.json');b=read('evidence/build-status.json');m=read('MANIFEST.json')
assert b['exit']==0 and v['full_kernel_compiled']
cmd=b['commands'][-1];seconds=(datetime.datetime.fromisoformat(cmd['finished'])-datetime.datetime.fromisoformat(cmd['started'])).total_seconds()
log=gzip.decompress((R/'evidence/Image.gz-dtb.log.gz').read_bytes()).decode(errors='replace')
verification=subprocess.run([sys.executable,'-B',str(R/'scripts/verify_bundle.py')],capture_output=True,text=True);assert verification.returncode==0,verification.stdout+verification.stderr
(R/'evidence/local-verification.txt').write_text(verification.stdout)
pins=dict(base_commit='717bb3c9e13ce573cfdd2dda856debd27a0fa17f',base_image_sha256='46895deb12ec94160ea5af0e85afa89c6de84971db126bb94c60cec1ec3ec401',base_config_sha256='067090e03ad762344308cebd0a71274d9943e299ded6707051ebfdc075dd045f',source_patch_sha256=sha('patches/kernel-from-physical-r5.patch'),pre_post_manifest_sha256=sha('patches/pre-post-hashes.json'),image_sha256=sha('artifacts/Image.gz-dtb'),image_bytes=(R/'artifacts/Image.gz-dtb').stat().st_size,config_sha256=sha('artifacts/resolved.config'),dtb_sha256=sha('artifacts/asus-p00a.dtb'),kernel_release=(R/'artifacts/kernel.release').read_text().strip(),full_verification_sha256=sha('evidence/full-verification.json'),compile_log_gzip_sha256=sha('evidence/Image.gz-dtb.log.gz'),compile_log_sha256=hashlib.sha256(gzip.decompress((R/'evidence/Image.gz-dtb.log.gz').read_bytes())).hexdigest(),compile_status_sha256=sha('evidence/build-status.json'),export_manifest_sha256=sha('MANIFEST.json'),source_manifests=v['source_manifests'],toolchains=read('evidence/toolchains.json'),compile_exit=0,compile_seconds=seconds,full_compile_commands=b['commands'],physical_tested=False,product_integrated=False)
(R/'report/SOURCE-PINS.json').write_text(json.dumps(pins,sort_keys=True,indent=2)+'\n')
text=f'''# Complete BMC156 physical ARM64 kernel receipt

Completed a genuine clean full `Image.gz-dtb` build from the exact compiled physical r5 source plus the unchanged completed BMC156 port. **Compile exit: 0. No product integration or physical hardware qualification is claimed.**

The local deliverable is `artifacts/Image.gz-dtb`, {pins['image_bytes']:,} bytes, SHA256 `{pins['image_sha256']}`. `artifacts/resolved.config` is `{pins['config_sha256']}`. The appended DT is byte-identical to physical r5: `{pins['dtb_sha256']}`. The large source tree, objects, raw Image and vmlinux remain in `/srv/android/asus-bmc156-full-kernel-r1` on the existing VM.

## Reconstruction and source scope

This is an owned kernel BUILD FIXTURE, not another agent checkout/workspace. The exact pinned `active-soc-source.tar.gz` reconstructed the 61,976-file baseline at commit `717bb3c9e13ce573cfdd2dda856debd27a0fa17f`. All 268 r5 combined-delta preimages were verified before extracting the exact pinned `combined-source-changes.tar.gz`; every resulting postimage and all 62,224 r5 regular source files matched the full receipt and original compiled fixture. Repository metadata was not copied or changed, and no source hardlinks were used.

The accelerometer patch applied with `git apply`, exact preimage/postimage verification, and no offsets or fuzz. Its hash remains `{pins['source_patch_sha256']}`. There are exactly nine changed source paths, including four new OEM-port files, producing 62,228 regular source files. **No additional kernel source fix was needed.** Original source files were checked again after the build. The compressed full r5 manifest plus nine-file postimage manifest reconstruct the full final source manifest; its canonical digest is recorded in `SOURCE-PINS.json` and independently checked locally.

An initial reconstruction assertion accidentally included original `.git` metadata in a source-only comparison. It stopped before patch/build launch. The corrected verifier excluded repository metadata and resumed from the verified r5 reconstruction. The failed recipe and error explanation are preserved locally. This was a verification-script correction, not a kernel source mismatch or a compile retry.

## Actual compile

The sole full compile ran from {cmd['started']} to {cmd['finished']} ({seconds:.1f} seconds), `make -j1` on CPU 0 with nice 10. It began with an empty output tree and the complete original physical resolved config, never a virtual-fixture config. Existing GCC 13.3.0/binutils/host tools were used; executable paths, hashes and versions are in `evidence/toolchains.json`. No packages were installed.

The exact command, PID, start/end timestamps and per-command exit codes are in `evidence/build-status.json`. The complete compiler/link/compression/DT log is `evidence/Image.gz-dtb.log.gz`; it includes {log.count('warning:')} warning diagnostics and was not filtered to conceal them. Compiler warning flags were not relaxed by this task. The output is a fully linked AArch64 vmlinux with no undefined symbols, a real raw ARM64 Image, gzip compression, and one complete appended board DT. This is not an object-only or symbol-stub result.

The release remains `{pins['kernel_release']}`. The explicit make `LOCALVERSION=-g717bb3c9e13c-dirty` carries forward the pinned r5 suffix without fabricating a Git checkout; generated compile metadata records this build separately. `compile.h`, `utsrelease.h`, the complete System.map on the VM, selected linked symbols locally, and all artifact hashes are retained.

## Preservation and limits

Only four resolved configuration values differ: `CONFIG_CUSTOM_KERNEL_ACCELEROMETER` and `CONFIG_BMC156_ACC` n→y; `CONFIG_MTK_BMA253` and `CONFIG_MTK_MC3416` y→n. The final embedded config exactly equals the exported resolved config, including the entire inherited option set.

All 58 core runtime options and 282 protected source files, 290 scoped firstboot source files and 134 selected firstboot options, and 16 network options remain exact. The complete source manifest also preserves all original combined charging/radio/network changes. All 18 selected r5 runtime/radio/charging/network linked symbols remain present with their expected symbol types; the real BMC156 callbacks are linked too.

The DT, its reservation map, static and dynamic reserved-memory definitions and all board properties are unchanged. `asus,allow-battery-charging` remains absent. ARM64 text offset, flags and reserved header fields are preserved; allocated Image size changes naturally with the compiled code. The actual new header and unchanged parent ramdisk/DT placements have no static overlap and fit the DT's declared RAM bank. Runtime LK memory/framebuffer placement remains untested. No BOOT repackaging or new physical probe was made.

`evidence/full-verification.json` passed {v['checks_passed']} remote full-kernel/source/config/DT/layout checks. The original accelerometer bundle passed 223 checks before work. {verification.stdout.strip()}

The exported payload is {m['total_bytes']:,} bytes across {len(m['files'])} pinned files, excluding local report/helper metadata. The first export with a full compressed System.map remains preserved on the VM; the smaller local export retains its exact pin and selected symbol receipts. Transfers were hash-verified, using only the authorized SSH helper and identity path. The frozen r2 kit seal remains unchanged; active AOSP r5 supervision/build, original physical kernel, old accelerator fixture and frozen artifacts were not modified or managed.

## Parent continuation

`parent-delta.json` and `HANDOFF.md` specify the smallest future candidate change: nine exact kernel source paths, the complete resolved config, the new prebuilt Image, and corresponding regenerated receipts/pins. Apply only to a future parent-owned candidate under the parent's original integration gates; frozen r2 stays frozen. No r6/Soong/Ninja/full-product build was started.

The HAL/service Soong integration, init/ueventd, policy/VINTF/ELF whole-product validation, private original calibration restoration, real sensor behavior and autorotation remain future work. No device, ADB, USB, root, reboot, flash, private calibration/key-content read, cloud lifecycle/resource operation, display/radio/charging/sensor physical test, or physical GO occurred.
'''
(R/'report/REPORT.md').write_text(text)
p=R/'report/HANDOFF.md';s=p.read_text();s=s.replace('Status: clean full kernel compile in progress; do not consume until evidence/full-verification.json and the local bundle verifier pass.',f"Status: complete full compile exit 0, remote static verification passed, and local bundle verification passed. Image SHA256 `{pins['image_sha256']}` ({pins['image_bytes']:,} bytes). No physical or product readiness claim.")
s=s.replace('`parent-delta.json` will contain exact old/new hashes.','`parent-delta.json` contains exact old/new hashes.')
p.write_text(s)
(R/'README.md').write_text(f'''# BMC156 complete physical kernel fixture

Question: Can the exact compiled physical r5 source plus the completed BMC156 port build a complete ARM64 Image.gz-dtb while preserving every inherited prerequisite?

Status: completed full compile exit 0 and source/config/DT/header/layout preservation checks. Physical behavior and product integration remain untested.

Important outputs:

- [Complete Image.gz-dtb](artifacts/Image.gz-dtb), SHA256 `{pins['image_sha256']}`.
- [Report](report/REPORT.md), [parent handoff](report/HANDOFF.md), [exact pins](report/SOURCE-PINS.json), and [minimal future product delta](parent-delta.json).
- Exact nine-file source patch and four-option resolved config diff in `patches/`; complete r5 source manifest and full build log in `evidence/`.

Continuation: run `python3 -B scripts/verify_bundle.py` locally. The existing owned VM BUILD FIXTURE is `/srv/android/asus-bmc156-full-kernel-r1`; inspect completed status receipts before any action. Do not rerun one-time reconstruction/launch/export scripts. Large source, objects, vmlinux and raw Image stay on the VM. Read the handoff before a future parent-owned integration. Original fixtures, active builds, sealed r2 and frozen R3 remain untouched. No hardware actions are authorized by this artifact.
''')
print(verification.stdout.strip());print('REPORT',pins['image_sha256'],pins['image_bytes'])
