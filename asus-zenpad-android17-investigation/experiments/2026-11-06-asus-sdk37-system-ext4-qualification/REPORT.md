# SDK37 SYSTEM ext4: bounded mechanism pass, full-image gate pending

**The actual SDK37 SYSTEM mkfs profile and e2fsdroid settings passed a real mount/read/security-xattr/unmount on the accepted 4.9.337 virtual Image.** The 64 MiB specimen passed host read-only e2fsck before and after; the unsupported-feature control was rejected by the real kernel. This does not establish compatibility of the uncompleted full SYSTEM, Android runtime, hardware, or flash readiness. Physical GO is false. No full-product ext4 failure is established.

Decision: [acceptance.json](acceptance.json). Future acceptance contract: [FINAL-SYSTEM-GATE.md](FINAL-SYSTEM-GATE.md). All large fixture files stay on the VM, under `/srv/android/asus-sdk37-system-ext4-qualification-20261106`. The accepted run is `fixture-r2/runtime-r4`.

## Authority and exact creation path

The remote r8 plan `/srv/android/asus-reviewed-build-kit/r8/inputs/plan.json`, SHA256 `0f458b6c488f771e6906103532ff7b02223c29a5c30751c6e65697c1d355f603`, resolved the AOSP, device and compiled physical-source roots. No local or guessed BoardConfig path supplied authority.

The actual `/srv/android/lineage24/device/asus/p00a/BoardConfig.mk` is SHA256 `e5296e182b457ec662694e044fffd322bdc246d556783743d080c23f5e4bde55`. It selects ext4, SYSTEM size 3,753,902,080 bytes, and no AVB. The actual fstab is SHA256 `04179d23e76be8755f6452319e05cc89f2438b51fcc539cb76695c9c65c57e75`; its SYSTEM filesystem option is `ro`.

The generated `out/build-lineage_p00a.ninja` SYSTEM rule creates `obj/PACKAGING/system_intermediates/system_image_info.txt`, then invokes `build_image` with the real SYSTEM input filter, input tree, properties file, output and target-out. Captured rule text is in [inspection.json](evidence/inspection.json). Its properties select `system_fs_type=ext4`, `system_size=3753902080`, `ext_mkuserimg=mkuserimg_mke2fs`, `extfs_sparse_flag=-s`, real SELinux contexts, root-dir staging and `skip_fsck=true`. Captured Ninja commands were **never executed**.

`build_image.py` stages root plus `system/`, changes the mkfs mount point and label to `/`, defaults read-only partitions to journal size 0 and reserved percent 0, and selects 256-byte inodes without project quotas. It computes UUID/hash-seed from the `/` mount point and absent fingerprint in this properties rule. The resulting helper arguments, emitted by the unmodified captured public functions, were:

```text
mke2fs -O ^has_journal -L / -I 256 -M / -m 0
  -U d392d8bb-6c67-58f7-b0b2-091ad46c5bc2
  -E android_sparse,hash_seed=baea5dae-7c08-5576-9e9b-a8d3c3d94800
  -t ext4 -b 4096 <owned-system.sparse> 16384

e2fsdroid -p <owned-target-out> -S <owned-file_contexts>
  -f <owned-input-root> -a / <owned-system.sparse>
```

Only size and fixture input/output paths changed. Fixture inputs were minimal nonprivate text files, a symlink, an empty target-out for device overrides, and fixture SELinux context mappings, including `lost+found`. The filesystem label remained `/`. No journal, shared-block, encryption, casefold, project-quota, timestamp or extra feature flag was introduced. Existing SDK37 `simg2img` converted only this tiny sparse specimen to raw.

At inspection, the installed packaged wrapper, its Soong intermediate, `tune2fs`, and the correctly resolved generated SYSTEM properties file were absent. This is an input-availability observation during active r8, not a product failure. The precise missing wrapper producer is `python_binary_host { name: "mkuserimg_mke2fs" }` in `system/extras/ext4_utils/Android.bp`, with bundled `mke2fs.conf`; its output is `out/soong/.intermediates/system/extras/ext4_utils/mkuserimg_mke2fs/linux_glibc_x86_64/mkuserimg_mke2fs`, then the generated installed-copy rule produces `out/host/linux-x86/bin/mkuserimg_mke2fs`. No producer/build was started. The specimen exercised actual existing SDK37 helper binaries and public argument-construction functions, **not the unavailable packaged launcher**.

## Exact pins and source support

| Input | SHA256 |
|---|---|
| Accepted virtual Image | `c59e030cdfc3e752eeddbbf62d091ae9760c94d5fbf780a22824e004ec872080` |
| Resolved virtual config | `0426746d90db074dd026ae5d383e1cde27d587020699d5dc9af4faac0b54489f` |
| Existing SDK37 mke2fs | `9c1bc44ee0043e53f4241f0c980c4e98bc78ca2e0ff19db78aa1e5e0d4e30b28` |
| Existing SDK37 e2fsdroid | `e4682b7440cdc7b551cb0772a97bffc508a9909ae63d33caffaa7d4b9985e055` |
| Existing SDK37 e2fsck | `5a39962bda4b5ce6e93d6b7f3ab75d48ed8fcda3f3b8748273e0878644148de4` |
| Android mkfs config | `ad58a58dcdd24d85055814ca9cac67db89d4e67c434e96774bdce0d0a007d067` |
| Public mkuserimg Python source | `8bda1a67fa742f06d8a23b905e544b3b0b327a83484df1f0b3c61c93b08468b1` |
| Public build_image Python source | `fb4282af1552d445b175bea8018105ef22002fa5e108519b843229069296cc94` |
| Accepted 64 MiB raw specimen | `bf934168d9154b46ae996c2c3060b80f332f86348bc9b6417c014875474516e7` |

The authoritative config is `system/extras/ext4_utils/mke2fs.conf`, bundled by the wrapper's Android.bp. The generic `external/e2fsprogs/misc/mke2fs.conf.in` is a different profile and was not used. In particular, its metadata checksum/64bit/orphan-file defaults were not inherited.

Actual superblock values and feature names:

- COMPAT `0x28`: `ext_attr`, `dir_index`.
- INCOMPAT `0x42`: `filetype`, `extent`.
- RO_COMPAT `0x7b`: `sparse_super`, `large_file`, `huge_file`, `uninit_bg`/GDT checksum, `dir_nlink`, `extra_isize`.
- Block/cluster size 4096; inode size 256; descriptor size 32; no journal or recovery bit; clean filesystem. Default mount options advertise `user_xattr,acl`.

All **41 files under `fs/ext4`** byte-match between `/srv/android/asus-sdk37-lmkd-functional/kernel-memory-r1/source` and the plan-resolved physical root `/srv/android/asus-bmc156-full-kernel-r1/kernel`. [source-support.json](evidence/source-support.json) preserves every per-path hash, the selected-map digest, extracted support masks, relevant config values, and parent authority hashes. `ext4.h` is SHA256 `e3dbb07b3d812ff9319b2f301ce6db20e3fdc0e922cbcaf5fc4c2b146707ae82`; `super.c` is `b941b6d5af7781d99bbcc5b429b3d62e515740b9a0d28675e1e10b080d630861`.

The source admits incompatibility mask `0x1a3d6` and read/write RO_COMPAT mask `0x277f`; the specimen's bits are subsets. `ext4_feature_set_ok()` rejects unknown INCOMPAT bits even for read-only mounts, and returns early for read-only before its unknown-RO_COMPAT check. It does not use `EXT4_FEATURE_COMPAT_SUPP` as a blanket rejection mask. Source checks admit power-of-two inode sizes from 128 through block size. The final gate uses the exact qualified profile rather than claiming all source-admitted features were exercised.

Both resolved configs have `ARM64_4K_PAGES=y`, `64BIT=y`, `EXT4_FS=y`, `EXT4_FS_SECURITY=y`, `EXT4_FS_POSIX_ACL=n`, and `EXT4_ENCRYPTION=n`. No POSIX ACL or encryption behavior was qualified. Security xattr retrieval was qualified; SELinux enforcement and file-capability execution were not.

The preexisting memory/firstboot parent acceptance remains scoped to selected correspondence with physical BMC Image `e9cde06e…` / config `10b212ca…`. Its explicit wholekernel/debug/crypto/platform differences remain. This task adds ext4 source/config inspection and filesystem execution; it does not erase those differences or assert wholekernel equivalence.

## Runtime receipts and limits

[Accepted serial](evidence/accepted-serial.log) records Linux 4.9.337, guest-observed superblocks, a successful read-only ext4 mount without journal, 4096-byte read-only statvfs, exact reads of all three fixture files and the symlink, uid/gid/mode checks, xattr hex, EROFS write denial, successful unmount, `SYSTEM_EXT4_RESULT failures=0`, and power-off. [runtime.json](evidence/runtime.json) records QEMU exit 0, no timeout, host e2fsck exit 0 and byte-identical before/after hashes for both tiny images.

Genuine built-in fs_config assigned `system/bin/run-as` uid 0, gid 2000, mode 0750. The guest retrieved `security.selinux` as the fixture's 26-byte `u:object_r:system_file:s0\0`, and the 20-byte revision-2 effective SETUID|SETGID capability xattr `01000002c0000000000000000000000000000000`. The final product's public file_contexts instead selects `runas_exec`; its actual final coherent label must be checked separately. No fixture binary was executed from SYSTEM.

The one meaningful negative clones the small specimen and changes only incompatibility bit `0x80000000`. Metadata checksums are absent, so this is not a checksum-corruption test. The real kernel emits `unsupported optional features (80000000)` and returns `EINVAL`; the header gate rejects it too.

The accepted guest used one Cortex-A53 vCPU, 384 MiB, single-thread TCG with 16 MiB cache, one host CPU affinity, no NIC, and host `RLIMIT_AS=1 GiB`, CPU 60 seconds, wall 90 seconds. Compiler processes were serial with the same one-CPU/1-GiB bound. Remote inspection/preparation processes inherited one-CPU/1-GiB limits and CPU caps. All used build helper binaries, QEMU/GCC driver and their copied dependencies, sources, Image and config have before/copy/after equality receipts; compiler cc1/collect2/as/ld add four more verified copies, **83 total**. System loader, Python, compiler support archive hashes and compiler logs are also retained. No arbitrary captured command executed against active out.

Size matters: the 64 MiB specimen selects `ext4,small` (4096-byte inode ratio), while 3,753,902,080 bytes selects `ext4` (16384-byte ratio). Explicit `-b 4096` and `-I 256` override the small-profile geometry defaults. Neither size profile adds features; both fit below automatic 64bit block-count thresholds. A full-size noaction resolution reported 916480 blocks, 229376 inodes and 28 groups; the specimen has 16384 blocks/inodes and one group. No full-size filesystem was created. These source/selection observations do not substitute for final feature masks or final group-metadata execution.

Historical preparation/run failures remain intact: r1 lacked a `lost+found` context; the first noaction probe required an existing path, and the Android sparse IO manager later truncated the **owned scratch raw file** despite `-n`; it was recovered into a new filename from the unchanged tiny sparse artifact. Two compiler attempts exposed relocated cc1/include search paths; copied subtools and explicit cross paths fixed them. Runtime r3 swapped positive/negative disk roles because QEMU enumeration differed from drive insertion order; accepted r4 identifies exact masks from both disks. None of those failures involved parent artifacts. Do not rerun historical preparation scripts; the read-only header checker is the intended reusable tool.

## Required final gate

The [header checker](scripts/check_system_header.py) passed real raw and sparse specimen inputs with identical logical-superblock SHA256 `8ce2ea6434cde06d74f2ab8d6a58f1a35df6510e77a92c90aaf81325b2b7b8c4`, and rejected the feature control. It opens inputs read-only, checks sparse structure, and does not expand, copy, or fully hash payloads.

After terminal parent validation, require this header check on the genuine completed raw/sparse image, then an actual c59e kernel read-only mount/read/xattr/unmount of the already admitted raw partition from `complete.json.raw_system.path`, with coherent final public-file expectations, terminal serial/exit/limits and host read-only e2fsck evidence. [propose_full_gate.py](scripts/propose_full_gate.py) only emits the deferred QEMU argv and explicitly leaves mount acceptance false. The exact admission, observer assertions, bounds, command proposal and required receipts are in [FINAL-SYSTEM-GATE.md](FINAL-SYSTEM-GATE.md).

No r8 validator was modified. No device/ADB/root/private calibration/key contents, active source/out writes, parent lock/process polling, AOSP/Ninja/fullkernel build, old fixture mutation, cloud/process lifecycle change, full SYSTEM copying/export or full-image rehash occurred. All new remote writes are inside the owned prefix. The current task ends at bounded filesystem mechanism acceptance; the final product gate remains pending.

Parent coordination received at handoff: r8 ended exit 1 at 23:48:28 UTC; first phase exited 0, and the full-image phase failed on a 134-byte WebView Git LFS pointer. The parent reports both native/supervisor processes absent and is preparing a separate r9 kit. This is parent-supplied status, retained in `evidence/parent-coordination.json`; this task did not poll those processes or inspect their frozen phase receipts. Source/out remain untouched. A later r9 must admit its own terminal receipt and recheck creation/profile/tool/context correspondence before consuming this qualification. The unavailable wrapper producer remains owned by native continuation.
