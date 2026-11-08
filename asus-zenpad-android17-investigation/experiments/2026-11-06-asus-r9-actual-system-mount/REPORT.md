# Actual r9 SYSTEM is filesystem-readable on virtual Linux 4.9

**The actual 3,753,902,080-byte SYSTEM raw passed a real read-only Linux 4.9.337 ext4 mount, six bounded full file reads, security-xattr retrieval, and clean unmount.** QEMU exited 0 without timeout; all 76 guest checks passed (`ACTUAL_SYSTEM_MOUNT_RESULT failures=0`). The admitted SHA256 remained `baa69560ace09a478c902077d8ff926d7a079ecb9b9f1632e4c330169b243798` in the single post-run full-image hash. Dev/inode/size/mtime/ctime/mode were unchanged.

This is a newly parent-admitted, narrow artifact readability test. Original r9 native phases exited 0, while original r9 overall exit 1 and the actual `ro.debuggable=0` root-check failure remain parent-reported failures. This result does not replace the stricter production observer admission/expectation gate. Product acceptance, Android init/services, SELinux enforcement, file-capability execution, hardware boot, physical GO and flash readiness remain unproved/false.

## Actual input and immutable reader

Input was reused in place: `/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw`. It was opened by the host reader as `O_RDONLY|O_NOFOLLOW|O_CLOEXEC`, and presented by QEMU using read-only file and raw block nodes. No full image copy or host mount was made. Source identity before mounting and after mounting/hash: dev `2049`, inode `27263347`, bytes `3753902080`, mtime_ns `1794019280920581777`, ctime_ns `1794019538990926800`, mode `0444`. The parent-supplied pre-run hash and the measured post-run hash match. The whole raw was hashed **exactly once**, after the run on the same initially opened read-only descriptor; the pre-run hash was inherited from the parent, not recomputed.

The retained runtime and toolchain were reused in place under `/srv/android/asus-full-system-observer-preparation-20261106/immutable`. All 2,368 manifest entries were checked against their retained pins before use. No kernel, AOSP or Ninja build ran. Only the small independent static guest reader was compiled.

| Input | SHA256 |
|---|---|
| Actual raw SYSTEM | `baa69560ace09a478c902077d8ff926d7a079ecb9b9f1632e4c330169b243798` |
| Retained virtual Image | `c59e030cdfc3e752eeddbbf62d091ae9760c94d5fbf780a22824e004ec872080` |
| Virtual config | `0426746d90db074dd026ae5d383e1cde27d587020699d5dc9af4faac0b54489f` |
| Current physical config | `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2` |
| QEMU | `b511b60cc31479b71dfdd589e6c981ae37b20ef0e75adc5a57bb0d6737e9b30c` |
| Guest init | `42d4dc31daa728ee0ca9aa0eae42566b838dc86028142c58d29d1369416b731c` |
| Guest initramfs | `6752d83eac1915d0b8809f2ffed9a74f645711c8aa9274092e0677bcbea80e37` |

## Filesystem and source correspondence

The reusable header check passed the actual raw: COMPAT `0x28`, INCOMPAT `0x42`, RO_COMPAT `0x7b`, 4096-byte blocks, 256-byte inodes, clean state, no journal inode/device, no orphan head. Filesystem size equals partition size. Guest superblock SHA256 `0f06eb7ae5145fd6cd4741c3d8b681ed19fb9fa79a5bdc3fbfff885605bacbdc` matches the host header.

The exact actual masks are the previously exercised profile: ext_attr/dir_index; filetype/extents; sparse_super/large_file/huge_file/GDT checksum/dir_nlink/extra_isize. Their INCOMPAT and RO_COMPAT bits fit the retained current-header support masks `0x1a3d6` and `0x277f`. The same pinned header and super.c logic from the earlier qualification applies; COMPAT support is not a blanket allowlist, and read-only mounts skip the unknown-RO_COMPAT rejection.

All 41 current `fs/ext4` files were rehashed in both `/srv/android/asus-sdk37-lmkd-functional/kernel-memory-r1/source` and `/srv/android/asus-bmc156-full-kernel-r1/kernel`; both copies match the retained per-path pins. Current ext4.h is `e3dbb07b3d812ff9319b2f301ce6db20e3fdc0e922cbcaf5fc4c2b146707ae82`. Selected current config options match: ARM64_4K_PAGES, 64BIT, EXT4_FS and EXT4_FS_SECURITY enabled; EXT4_FS_POSIX_ACL and EXT4_ENCRYPTION disabled. This is selected ext4 correspondence, not whole-kernel equivalence.

## Real mount and observed files

Guest `BLKROGET=1` and `BLKGETSIZE64=3753902080`. Mount used `MS_RDONLY|MS_NOSUID|MS_NODEV|MS_NOEXEC` and `noload`; the actual `/proc/self/mounts` line is:

```text
/dev/vda /mnt ext4 ro,nosuid,nodev,noexec,relatime,norecovery 0 0
```

The kernel confirmed mounting without journal. Statvfs reported read-only and 4096-byte blocks. Guest path traversal used fixed public paths with `O_NOFOLLOW` for every component. No SYSTEM program was executed. The root `init` symlink was observed as `/system/bin/init`; its target was opened through the fixed `/system/bin/init` path.

| Guest file | Bytes | Actual SHA256 |
|---|---:|---|
| `/system/build.prop` | 6183 | `49fac302ba8fc47213c89878190f96088b11084053ece23394b6368f1fae1904` |
| `/system/bin/init` | 2628192 | `3bf6dfd7d72361cbca869e36c13801e5a7a5829a478a529037a7d5c24c0633f2` |
| `/system/bin/run-as` | 18720 | `ce5c22a25f614e59fb0be44462bb69ee5210c2f9451194e23a2a464160778323` |
| `/system/etc/selinux/plat_file_contexts` | 50849 | `bc6f2ee366442c84221049130b8052578f1d9873cfac8d40f90efacd76521d96` |
| `/system/vendor/etc/selinux/vendor_file_contexts` | 27261 | `031b9597a3711985dec87036ceaeb90e168c49514fcb5f96b07a27b79f6696b1` |
| `/system/lib/liblog.so` (ARM32) | 42568 | `473bb94ce06678bffd72eb2c34d2f105d540cdedba6e5cc9c4f2c2d073449f9d` |

All six reached EOF at the stated size; the ARM32 liblog hash matches the explicit parent expectation. Actual uid/gid/mode/size/inode and security.selinux/security.capability values were recorded for these files plus `/`, `/system`, `/system/bin`, `/system/etc`, `/system/vendor`. The root init symlink also has lstat/readlink evidence. These are observations, with no production metadata expectation asserted. For example build.prop was observed uid/gid `0:0`, mode `0600`; run-as was observed `0:2000`, `0750`, `runas_exec` and the 20-byte capability xattr. Complete actual values are in [observed-metadata.json](evidence/observed-metadata.json).

## Evidence, bounds and continuation

[serial.log](evidence/serial.log) is the real kernel and reader output; [compile.log](evidence/compile.log) and [qemu-argv.json](evidence/qemu-argv.json) preserve exact commands. [result.json](evidence/result.json), [verified-inputs.json](evidence/verified-inputs.json), [seal.json](evidence/seal.json) and [verification.json](evidence/verification.json) hold terminal status, pins, current source/config correspondence, source identity and local evidence checks.

One Cortex-A53 guest vCPU, 384 MiB guest RAM, single-thread TCG with 16 MiB cache, no NIC. Host processes used one CPU affinity, 1 GiB address-space limit and 60 seconds CPU; QEMU wall timeout was 75 seconds and each remote script alarm was 90 seconds. Runtime plus single post-hash completed in 3.76 seconds. Own VM prefix used about 1.45 MB, below 128 MiB, with no full raw copy. Parent reported existing host e2fsck PASS; it was not repeated here.

No device, private/calibration data, SSH key contents, native build process state, cloud lifecycle, active source/out edits, earlier fixtures or validators were touched. Only new owned-prefix output was written remotely. Preserve this run and the earlier fixtures. Any future test must keep a separate output path and maintain the production gate's own requirements. This run qualifies filesystem readability of the pinned actual artifact on the pinned virtual 4.9 kernel only.

Separately authorized continuation planning is complete in [Actual runtime plan](../2026-11-06-asus-r9-actual-runtime-plan/REPORT.md). No runtime fixture was built or launched; the parent will schedule it against separately admitted post-fix images.
