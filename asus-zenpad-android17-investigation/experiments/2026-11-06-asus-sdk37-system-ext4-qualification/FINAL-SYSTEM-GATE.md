# Future completed SYSTEM filesystem gate

This is a deferred acceptance proposal. No completed product image was read, copied, expanded, rehashed, or mounted in this qualification. Do not run it against active build output. A header pass always leaves actual kernel mount acceptance pending.

## Admission and read-only header check

The parent must supply a terminal successful build/validation receipt from the subsequent admitted product (the parent-reported failed r8 is ineligible), the genuine completed `system.img`, and `complete.json` from `validate_completed_product.py`. Recheck the later product’s actual BoardConfig, generated SYSTEM rule, wrapper/config and host-tool pins against this qualified selection; changes require review and any relevant repeat qualification. Use `complete.json.raw_system.path` for the already materialized, read-only raw partition. Its recorded digest and `source_system_sha256` identify the parent's artifacts; this task does not recompute those full-image digests. Do not guess output paths or materialize a second full SYSTEM. If the parent has supplied only sparse bytes and no admitted raw artifact, the kernel-mount gate is **pending: missing completed raw artifact from `validate_completed_product.py`**. The sparse header can still be inspected without expansion.

Run on the VM, with output in a fresh owned acceptance directory:

```text
python3 -B check_system_header.py <completed-system.img>
python3 -B check_system_header.py <complete.json.raw_system.path>
```

The script opens ordinary files with `O_RDONLY|O_NOFOLLOW`. It validates raw/sparse structure and logical superblock bounds, exact qualified feature masks `(0x28,0x42,0x7b)`, block/cluster size 4096, inode size 256, 32-byte descriptors, clean state, no journal/recovery/orphan head, and filesystem/container size within the 3,753,902,080-byte partition. It hashes only the 1024-byte superblock. Sparse CRCs and payload integrity are outside this header check. Require the same superblock digest and filesystem byte count for original and parent raw output. Reject any changed feature mask for independent review rather than silently broadening the allowlist.

A small filesystem may have more inodes per byte than the final filesystem. Do not require the specimen's inode count, free counts, group count, UUID, timestamps, or filesystem digest on the full product. Require authoritative final geometry and the qualified mechanisms instead. Unknown RO_COMPAT features may be accepted by the kernel for a read-only mount; this gate deliberately rejects them because they were not qualified here. COMPAT bits are not a kernel rejection mask; the exact profile check is a conservative evidence boundary.

## Actual kernel mount

Prepare a **new tiny observer initramfs**, using `source/guest_init.c` as the mechanism reference, then pin its source, compiler, ELF and initramfs. The specimen initramfs is not a full-image observer: its small fixture filenames and two-disk negative control must not be reused as product assertions.

The observer must perform these operations and count each failure:

1. Mount devtmpfs/proc/sysfs; identify the single virtio disk by the ext4 superblock, checking all three exact masks and 4096/256 geometry. Record kernel `uname` and the guest-observed header.
2. Mount that disk as `ext4`, with `MS_RDONLY` and no added mount options, matching the actual `fstab.mt8163` `ro` selection. The host block device must also be read-only. Require `statvfs` to show `ST_RDONLY` and 4096-byte blocks. Do not use a host mount as the kernel test.
3. Open and read to EOF bounded public files from the actual completed image: `system/build.prop`, `system/bin/init`, `system/bin/run-as`, and `system/vendor/etc/selinux/vendor_file_contexts`. Compare byte counts and bytes/digests to the parent's coherent installed-file receipts, not this specimen's contents. Resolve the image's `/system` directory relative to the observer mount; this is filesystem access, not Android switch-root qualification. Do not execute product binaries or read any keys/private files.
4. Compare `stat` uid/gid/mode, `security.selinux`, and `security.capability` for `system/bin/run-as` to metadata admitted from the same completed product and genuine fs_config/context inputs. The captured default is uid 0, gid 2000, mode 0750, effective CAP_SETGID|CAP_SETUID (20-byte revision-2 capability xattr); product overrides and the final SELinux label must be checked from final coherent inputs. Require real `getxattr` returns and exact bytes, and emit hex receipts. Do not infer enforcing-policy or capability-execution acceptance from retrieval. `selinux=0` remains a fixture adaptation for this mechanism-only check.
5. Require a write-open on an existing public file to fail with `EROFS`; require successful `umount`, a unique `FULL_SYSTEM_FS_RESULT failures=0` marker, and power-off. Inspect serial for ext4 errors/I/O errors. QEMU exit 0 alone is insufficient.

`propose_full_gate.py` consumes the admitted receipt and raw/sparse headers and prints the exact QEMU argv without executing it:

```text
python3 -B propose_full_gate.py --complete <parent-complete.json> --system-image <completed-system.img> --guest-initrd <reviewed-full-observer.cpio.gz>
```

Run that argv serially with one host CPU affinity, `RLIMIT_AS=1073741824`, `RLIMIT_CPU=60`, and a 90-second wall bound, as in this qualification's runner. It uses the existing pinned c59e Image, one Cortex-A53 vCPU, 384 MiB RAM, single-thread TCG/16 MiB cache, `-nic none`, and two read-only block nodes over the existing parent raw file. Retain command, observer input hashes, serial, terminal exit, limits, before/after file identity/size/mtime/ctime, and all guest results in the fresh acceptance fixture. Do not copy or rehash the full raw artifact. Require the recorded c59e Image/config pins; never copy the virtual configuration onto the device.

The existing parent `e2fsck -f -n` terminal receipt remains a separate required host check. If a new check is needed after the guest, run the copied/pinned host `e2fsck -f -n` directly on that same already admitted raw artifact under the same process limits, retaining exit 0; do not run mke2fs or use mke2fs `-n` as a checker. The no-journal image plus QEMU's read-only file/block nodes prevent guest writes.

Only accept **full-image filesystem header + actual 4.9 mount/read/xattr/unmount** after all of those receipts exist. This still does not establish whole Android runtime, APEX activation/trust, hardware storage behavior, wholekernel equivalence, physical boot, flash readiness, or physical GO. This proposal does not change either running r8 validator.
