# Full SYSTEM observer prepared; synthetic QA passed

The fixed-path read-only guest observer and fail-closed admission/generation/execution interfaces are implemented. One fresh **32 MiB synthetic ext4 filesystem** passed the positive check on the accepted 4.9 kernel. Wrong content-hash and wrong run-as-mode controls each produced one guest failure and actual child exit 1. The production CLI refuses synthetic, missing or incoherent inputs and defaults to PLAN_ONLY. **No genuine SYSTEM was read, captured, mounted, copied or rehashed; no production observer input was generated.**

Decision and all pins: [acceptance.json](acceptance.json). Future commands: [PARENT-COMMANDS.md](PARENT-COMMANDS.md). Exact missing/new parent contracts: [receipt-contract.md](contracts/receipt-contract.md).

Owned remote root: `/srv/android/asus-full-system-observer-preparation-20261106`. The single raw specimen is `fixture/system.raw`. All tools, compiler support, generated ELF/initramfs files, fixture data, old source revisions and all six finite boot runs remain there. No previous fixture or completed mechanism artifact was altered. The local verifier independently matched all **72 previous mechanism payloads** and its parent-scoped acceptance.

## Implementation and pins

`source/observer.c` performs the test in a child of PID 1. PID 1 waits for the real child status and prints `FULL_SYSTEM_FS_EXIT`; it then powers off. Host acceptance requires that status and the unique result marker, QEMU exit 0, no timeout/kernel error and unchanged admitted host identities. Clean QEMU power-off alone cannot hide a failing observer.

The observer:

- Checks a single read-only virtio disk with `BLKROGET`, its admitted capacity and logical-superblock SHA256, exact masks `0x28/0x42/0x7b`, 4096-byte blocks/clusters and 256-byte inodes, clean state and no journal/orphan head.
- Mounts ext4 with `MS_RDONLY` and default options, confirms 4096-byte read-only statvfs, then accesses only `/system/build.prop`, `/system/bin/init`, `/system/bin/run-as`, `/system/vendor/etc/selinux/vendor_file_contexts` relative to the mounted root. Every path component is opened with no symlink following.
- Streams each regular file to EOF through 64 KiB buffers and its built-in SHA256, compares expected size/digest and uid/gid/mode, exact SELinux xattr bytes and capability bytes or explicit ENODATA absence. Reads are bounded to 16 MiB per file, 32 MiB total expectations.
- Requires EROFS on a write-open of the existing public build.prop and successful unmount. It does not execute any product binary. `selinux=0` qualifies xattr retrieval only, not enforcement or capability execution.

Exact source pins:

- Observer C: `8c0050562fca57dad3a8c65a540d635695f72337d8f64fd5eb41aababc126743`.
- Streaming SHA256: `21461ce6550921e7a903cb29cab9ce0733a8aa9a25909f0cc2a411673ae67ea1`.
- Final admission parser: `fbb721df792b07883f9c22b6de7f63072ef8797b041ae4bb693f745579960685`.
- Generator/runner: `f7067fa1afcc75d51916e00798ac37b49471a0dee62f9f6765efb6d675de6863`.
- Production CLI: `e0aba5e6ec36a937e3e98905884611df310f8c3d61a21c7eaf06bfd28057deae`.
- Kernel Image: `c59e030cdfc3e752eeddbbf62d091ae9760c94d5fbf780a22824e004ec872080`.
- Resolved config: `0426746d90db074dd026ae5d383e1cde27d587020699d5dc9af4faac0b54489f`.

The accepted original 83 copied tool/source inputs were cloned with their existing pins and before/copy/after equality. Ten previously pinned existing compiler support files and 2,275 existing public cross-compiler headers were additionally frozen with before/copy/after equality. **2,368 files** were reverified and the new immutable copies had write bits removed. Original inputs were not chmodded. Compiler invocations use copied cc1/as/collect2/ld, owned headers, explicit owned startup objects/static libraries, `-nostdinc -nostdlib -fno-use-linker-plugin`; no AOSP or kernel build is involved.

Immutable pin-map SHA256: `8eb3e5347dfb4d23caec1a566f50cf4df8b3cf2d0bd263a0b78cb96032e2b35f`. Copy-receipt SHA256: `6861e8a4571f7291a192edf90e79bd99d7493b8f26c7d5fca3886b4ffd9e1ca6`. The full maps stay on the VM as `immutable-pins.json` and `copy-receipts.json`; compact terminal evidence is in [setup.json](evidence/setup.json), [final-capture.json](evidence/final-capture.json), [immutable-seal.json](evidence/immutable-seal.json).

## Fail-closed admission and generation

The production trust root is the parent's independently reviewed admission file **and externally supplied fixed hash**. An arbitrary self-hashed JSON file is not an admission. `admission.py` checks pinned ordinary-file receipts, scopes, schemas/types, group hashes, terminal build/host-validator exits, actual complete/raw identity, source capture, independent installed-content provenance, resolved fs_config/context values and matching resolver stdout/exit evidence. Duplicate JSON keys, missing/unknown defined fields, symlinked inputs, arbitrary/duplicate guest paths, changed pins, and mixed groups fail.

Production source binding requires the later plan-resolved BoardConfig, selected creation Python/config, actual generated SYSTEM Ninja stanza/properties, fs_config source/overrides and final contexts. The completed raw/sparse headers must also match the qualified profile. Only after all admission succeeds can `engine.py` emit an `expectations.h`, compile and package the observer. There is no default or production placeholder header. Generated expectations contain numeric/byte data only; target paths are hardcoded in C.

Expected file content originates in a coherent frozen installed-output capture, not extraction of the same candidate image. Expected metadata originates in actual source-bound SDK37 fs_config/selabel resolution, including consumed overrides and final contexts. Capability mask zero explicitly expects absence; nonzero produces the revision-2 effective xattr. Labels and modes have no guessed defaults. Synthetic source/terminal/completion/producer schemas are distinctly scoped and cannot be promoted through the production CLI, even by retagging the outer admission. Known synthetic namespaces are excluded from genuine input groups.

`full_system.py` defaults to PLAN_ONLY. GENERATE and EXECUTE require the same admitted group and a fresh output under the owned `runs/` prefix. EXECUTE fixes both QEMU file and raw nodes to read-only and uses only the owner's `complete.raw_system.path`; no arbitrary raw path or command list is accepted. Whole product digests stay fixed in parent receipts and are not recomputed. `host_fsck.py` is a separate, independently invoked, similarly admitted PLAN_ONLY/EXECUTE interface fixing the host command to copied `e2fsck -f -n`.

`capture_expectations.py` prepares the later content/metadata input receipts from fixed frozen public files and pinned genuine source/resolver/complete receipts; it emits no observer header and still requires parent review/admission. It refused the synthetic fixture. Two fixed host query TUs are supplied for later real fs_config and selabel resolution. Their genuine SDK37 libraries/headers, build pins and execution receipts were not supplied; those TUs have **not** been compiled or run against a real product. No producer success was invented.

## Bounded QA receipts

The one ordinary raw specimen was created once with copied SDK37 mke2fs/e2fsdroid and the accepted Android mkfs config. It contains deterministic nonprivate text/binary-pattern fixtures at the four fixed public paths. Input sizes 65,561 / 100,003 / 129 / 513 bytes exercise streaming and SHA256 padding across multiple buffer/block lengths. Data are synthetic and no file is executed.

Final raw SHA256 is `48855edf681d88707370285a9d2db00b66cbb727a4fbe9a77712857f50eb6a1d`, identical before/after. It has masks `0x28/0x42/0x7b` and 4096/256 geometry. Genuine built-in fs_config selections used here yield build.prop mode 0600, init 0755/root:shell, run-as 0750/root:shell with effective SETUID|SETGID. Fixture contexts select `runas_exec`, not the previous specimen's generic system_file. These fixture labels/values do not become production expectations.

The final strict receipt revision passed:

- **Positive:** four file reads/digests, all metadata/xattrs, read-only checks, EROFS and unmount; unique `failures=0`, actual child exit 0, QEMU exit 0.
- **Wrong hash:** only build.prop's expected digest changed; the stream digest check failed, unique `failures=1`, actual child exit 1, QEMU exit 0. No success marker.
- **Wrong metadata:** only the expected run-as mode changed from 0750 to 0644; the metadata check failed, unique `failures=1`, actual child exit 1, QEMU exit 0. No success marker.

Final positive ELF SHA256: `aecaba609f5aaaceccfb344a2d270b58c588fc961172941b8ca4ad26397790fb`; initramfs SHA256: `012f1cb2eeadb321d3f15b5e2b820e80cdba376b1b7c44e83266555cc9a71d43`. Both embed `FIXTURE_ONLY` scope and fixture-specific admission/expectation pins and cannot be used as an actual product observer.

Serial/generation/actual-exit receipts: [strict-positive](evidence/runs/strict-positive/serial.log), [wrong-hash](evidence/runs/strict-wrong-hash/serial.log), [wrong-metadata](evidence/runs/strict-wrong-metadata/serial.log), [strict-qa-result.json](evidence/strict-qa-result.json). Nine strict parser rejection cases and all PLAN_ONLY/GENERATE/EXECUTE fixture refusals passed without output directories. Default absent-admission refusal, expectation-publisher refusal and host-fsck CLI refusal are retained. The final production-only rule/properties binding added no new guest logic and was checked through the unchanged fixture expectations and repeated CLI refusals.

There were two tested fixture-receipt revisions and six serial boots total on the **same** filesystem. Earlier source revisions, runs and controls remain intact. Final separate host `e2fsck -f -n` exited 0 after the last boot; no creation tool was used against any owner artifact, and no mke2fs noaction command was used. All host artifact identities remained unchanged and no kernel ext4/I/O errors appeared. [audit.json](evidence/audit.json) retains compiler commands, source dependency records, serials and terminal logs.

All remote processes ran with one host CPU affinity, a 1 GiB address-space cap, 60 CPU seconds and a finite 90-second wall alarm/timeout. Guests used one Cortex-A53 vCPU, 384 MiB, single-thread TCG/16 MiB cache and no NIC. Compilers and guests ran one at a time. Large fixtures remain on the VM. Local `python3 -B scripts/finalize.py` rechecks source pins, actual serial control outcomes, immutable receipt bindings, and unchanged prior payloads without SSH or runtime execution.

## Pending parent contracts and scope

Preparation is complete; genuine admission remains unavailable. The missing inputs are the later successful complete/native terminal binding, coherent exact source/generated-rule/properties/public-output group, actual SDK37 metadata resolver build/exit/stdout receipts, and the parent's final independent admission pin. [PARENT-COMMANDS.md](PARENT-COMMANDS.md) gives the exact staged commands and limits. No current validator or active kit was changed.

R8's 23:48:28 UTC WebView LFS failure remains parent-supplied coordination, not a filesystem observation. This task did not read/mount partial r8 outputs, inspect another agent/build, poll processes, mutate active AOSP/source/out/kits, access device/ADB/private keys/calibration, run AOSP/Ninja/fullkernel builds, or change parent/cloud lifecycles. No real full SYSTEM, Android runtime, wholekernel/hardware, physical boot, flash readiness or GO is established.
