# Actual pre-root-fix early-runtime result

**The bounded actual-image attempt reached genuine first/second-stage init, activated four bootstrap APEXes, passed all four BoringSSL self-tests, and mounted fresh DATA. Its first fatal runtime blocker is actual linkerconfig aborting on a duplicate `heapprofd_client_api.so` provider in the vendor namespace.** The 90-second run subsequently remained blocked waiting for `android.security.maintenance`, with keystore2 repeatedly exiting1. No platform fix was applied.

This is an adapted virtual early-runtime result against the explicitly authorized **preserved pre-root-fix revision**. Original R9 overall/root `ro.debuggable=0` and VINTF failures remain. This is not product, root, Android/framework/GMS, hardware, physical GO or flash acceptance. No children were used.

## Execution and success boundary

Owned remote prefix: `/srv/android/asus-r9-actual-early-runtime-20261106`. Actual run `run-runtime-1`, launcher1791425, **2026-11-07 03:08:24.284–03:09:54.415 UTC** (Nov6 Toronto). One actual Android run; timeout90s, no180s extension. `returncode:null` records the timeout, not an exit0 success. The timeout concerns only this owned QEMU invocation; no source/build job state was inspected or inferred.

The raw [serial log](run-runtime-1/serial.log) establishes:

- First-stage init at0.827s; SYSTEM `/dev/block/vdb` mount0.989s; second-stage init1.845s. Actual policy loads1.423s. The command requests `androidboot.selinux=enforcing`; actual vendor-init property accesses are denied with real SELinux SIDs. A direct `/sys/fs/selinux/enforce=1` observer reading was **not captured**, so that stronger direct measurement remains unqualified.
- Genuine apexd bootstrap scans39 preinstalled APEXes, identifies runtime/i18n/virt/tzdata as bootstrap packages, mounts four EROFS loop devices, activates4 packages, and exits0 at7.888s. This establishes bootstrap activation, not post-data activation/trust/verity or final linker namespaces. `ro.boot.veritymode` is empty in this fixture, and the log explicitly disables file-backed mount.
- At8.948s: `duplicate: heapprofd_client_api.so is provided by default and system in [vendor]`. Linkerconfig receives SIGABRT at8.963s and init records its failure10.856s. This is the **first concrete fatal platform/runtime error**, before observer startup11.369s. The later `No such file or directory` message must not obscure the preceding actual linkerconfig execution and abort.
- Vendor32/64 self-tests exit0 at12.557/13.024s; platform32/64 exit0 at15.069/15.380s. The previous missing-platform-test reboot is cleared for these actual artifacts.
- Actual servicemanager/hwservicemanager start as pid229/230; servicemanager processes real VINTF/service requests. Real Keymaster4 service starts as pid245 at18.354s. Start messages do not prove Keymaster registration, hardware-info or crypto IPC.
- Actual vendor fstab late-mount maps fresh DATA to `/dev/block/vda`, mounts successfully20.307s, and `mount_all --late` succeeds20.372s. Genuine e2fsck separately reports permission denied against the virtual block node; that check failure is retained, not described as a successful filesystem check.
- Actual keystore2 first starts18.159s and exits1 at20.605s; **15 exit1 observations** occur. At21.627s the genuine `vdc keymaster earlyBootEnded` exec begins waiting; vold/service-manager repeatedly cannot obtain `android.security.maintenance` through the deadline. No keystore registration or functional IPC is proved. The keystore process's internal exit reason is not captured, and causation from the earlier namespace failure is not asserted.
- Genuine post-data apexd startup is not observed. The actual `wait_for_prop apexd.status activated` and `wait_for_prop keystore.module_hash.sent true` remain byte-preserved. Neither property is forged or claimed satisfied.

Secondary retained errors include absent hwrng (prng_seeder hangs), cgroup-v2 memory-controller and newer tunable incompatibilities, unavailable binderfs/configfs/FunctionFS, missing `/metadata` during aconfig initialization, and expected virtual hardware paths. These were not patched. No ENOSPC is observed.

## Exact admitted inputs

[Input pins](evidence/input-pins.json), [ramdisk deltas](evidence/ramdisk-deltas.json), [selected actual files](evidence/blocker-inspection.json), and [final seal](evidence/seal.json) contain full paths, hashes and metadata.

| Input | SHA256 |
|---|---|
| Read-only actual full raw, 3753902080B | `baa69560ace09a478c902077d8ff926d7a079ecb9b9f1632e4c330169b243798` |
| Immutable packaged MTKBOOT, 9242624B | `784d4dc565e7742ea607683d2a67d1fdb066764bddfa369895cbaaf6f048b435` |
| Actual gzip ramdisk, 1520040B | `95f5c2a8aded2e081e30e72ebd37322a24aa895bbe7e334c79c1381bcd3fe240` |
| Actual first-stage init | `b2abeeb7dc01d884536dd38ebccd835a8589187a979cf84e51d78131ce800ed4` |
| Unchanged virtual Linux4.9 Image | `95a62a8bccd3085d682a89b6c74c7afd0961cebd1e3137b256229849920b549b` |
| Unchanged virtual config | `c2ea1277e1574da39d1d55d31bde7bda439ab624561ad3c6a6f4730e38f57834` |
| Retained seed-exec ELF | `eddd78f4558e38ba1a1b5f2d9a8420111859e70a1d9c0d3b9cd837a4207ecf60` |

The BOOT is `/srv/android/asus-r9-independent-packaging-r2/checks/UNTESTED-ROOT-ROUTE-FAILED-sdk37-combined-boot.img`; exactly its512B MTK ROOTFS wrapper was stripped. The full raw stays in `/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw`, mode0444. Its dev2049/inode27263347/size/mtime/ctime/mode remain exactly identical to the independent qualified mount. Its SHA is inherited from that admission; no additional whole-raw hash/copy was performed.

The kernel/config/adapter and immutable BOOT hashes pass before preparation and at the final seal. The290-source/134-option firstboot/BMC correspondence is inherited from the prior qualification, not a new current-source or whole-kernel audit. No kernel compilation/config mutation occurred. This run uses the actual image's876367B precompiled policy (`887a493f…`), not the older partial-fixture policy. Actual SYSTEM init is `3bf6dfd7…`; runtime APEX is7577600B, `638361e8…`.

Read-only blocker inspection finds the literal `heapprofd_client_api.so` in actual `/system/etc/linker.config.pb` at byte69 (1240B, SHA `0cb3b9fe157fc5fdba0873420d4304a20ff95302d95f86449e3d8001c67c6b35`). The serial names both conflicting namespace providers. No guessed provider-removal fix was applied, and the other side's generating rule was not investigated through changing source/out metadata.

## Fixture adaptations and exact COW scope

No full SYSTEM reconstruction or raw copy exists. The new QCOW2 is1048576B, SHA `a367784813f5b1fa748013c64a2b853f5fa306a31fb807e4fddd39c8da523322`, sealed0444. QEMU presents both the raw backing and runtime QCOW2 top read-only with explicit block nodes. Offline preparation wrote only the owned COW.

**One existing file changes:** `/system/vendor/etc/fstab.mt8163`,667→591B, only the two physical by-name paths become vdbSYSTEM/vdaDATA. Inode7858,0:0,0644, SELinux `vendor_configs_file`, atime/mtime and original inline xattrs are preserved. Its ctime/extent change is recorded.

**Two files are added:** `/system/bin/actual-runtime-observer`,17952B,0:2000,0755,`shell_exec`; `/system/etc/init/actual-runtime-observer.rc`,245B,0:0,0644,`system_file`. The async shell-domain observer only reads public guest diagnostics and attempts real Binder/HIDL PINGs plus an invalid-handle negative. All property setters from the retained probe were removed. It does not gate core init. Original init.rc/core actions, policy, real service definitions/ELFs, properties and APEX payloads stay unchanged.

[Block audit](evidence/cow-block-audit.json) compares every allocated guest-visible COW cluster with the read-only base: **17 changed4KiB blocks, no unaccounted blocks/inodes**. Changes cover those three payloads, the two parent directories, allocation bitmaps, inode tables and primary filesystem metadata. [File verification](evidence/cow-file-verification.json) checks exact bytes and raw uid/gid/mode/xattrs. New xattrs are exact inline copies from actual `/system/bin/sh` and `apexd.rc`; the unloaded-policy guest's earlier `unlabeled` rendering was not used as the raw-label truth.

Ramdisk records are preserved, including the duplicate `dev` record (14 records,13 unique paths). Only fstab backend paths and the entropy-adapter init payload change; byte-identical actual init is added as `/first-stage-init`. The retained adapter credits a fresh64B random seed and execs actual init. Entropy-bearing initramfs stays remote0400; seed values and hashes are not exported.

DATA is a fresh512MiB legacy ext4 created using the retained mke2fs feature profile; no old DATA/stock userdata/private calibration is reused. Commands and format output are retained. One vCPU/1GiB guest, no NIC/USB device or forwarding, single-thread TCG64MiB cache,2.5GiB process AS and one-CPU affinity. The seal measured37,187,584B allocated and557,227,677B logical owned storage before final small reports, below2GiB.

## Preserved failures, measurement limits and continuation

Exactly **three fixture-glue corrections** were used, all sources/logs retained: (1) wrapper name is `ROOTFS`; (2)14 CPIO records versus13 unique paths; (3) offline guest cannot set SELinux xattrs before a policy is loaded, so its partial COW is retained separately and final labels are copied/verified offline. There were two offline patch boots and only one actual Android boot. No fourth fixture correction or platform/hardware patch was attempted.

Observer `stdio_to_kmsg` produced no stdout markers in actual serial with preserved `ro.debuggable=0`. The exact reason is not proved. Its pid222 invalid-handle kernel negatives show execution but cannot replace positive Binder/HIDL replies or a direct enforcement reading. These qualifications, Keymaster registration/crypto, keystore IPC/module-hash handoff and post-data APEX activation remain open. The prior fixture's functional-PING proof is not transferred to this run.

The public export initially normalized serial line endings; it was re-exported as exact bytes, with matching SHA. No fixture change resulted. One scope limitation: the correction3 compiler invocation did not explicitly redirect `TMPDIR` before compiling; transient default compiler scratch outside the owned prefix cannot be excluded. All retained named outputs are inside the new spike/prefix.

[Qualification](evidence/qualification.json) passes36 evidence assertions, including expected failures and negative claims; this is not36 boot-success gates. Preserve all run directories and sealed disks. Do not rerun preparation against this prefix or reuse DATA. The concrete next parent-owned work is investigate the actual linkerconfig duplicate-provider failure against an independently admitted revision; separately retain the keystore maintenance dependency failure and improve diagnostic capture in a newly authorized unit. No need to extend this run merely to repeat the same dependency wait.

No changing out/BOOT/source metadata, active native processes, device/ADB/root/calibration/parent-private/key contents/cloud lifecycle, active AOSP/Ninja/source/output mutation, worker locks/polling/signals or unrelated restarts were used. Only this owned QEMU was bounded by timeout. Original root/VINTF and physical acceptance decisions remain with their owners.
