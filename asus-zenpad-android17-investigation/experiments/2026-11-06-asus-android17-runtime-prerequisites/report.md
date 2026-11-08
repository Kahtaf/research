# Android 17 runtime prerequisites — implementation report

**PASS for the bounded filesystem and core Binder workloads.** On generic ARM64 Linux 4.9.337, the actual compiled SDK37 adbd APEX and exact Google GMS APEX both mounted through ext4-backed direct-I/O loops and AVB-derived dm-verity mappings. All 68 regular-file reads matched independently extracted reference hashes. Genuine SDK37 core libbinder completed cross-process IPC, thread-pool dispatch, replies, one-way calls, and client-death notification.

Authoritative run: [evidence/run-r5/result.json](evidence/run-r5/result.json), [serial.log](evidence/run-r5/serial.log), and [validation.json](evidence/validation.json). QEMU exit **0**, runner exit **0**, guest failures **0**, no timeout. No physical device, ADB, host block device, active AOSP build, active hardware-kernel tree, or cloud lifecycle was changed.

## What actually ran

The guest used two Cortex-A53 virtual CPUs, 1536 MiB RAM, a 300-second bound, `-nic none`, and one disposable 512 MiB virtual disk. The disk contains an actual writable ext4 filesystem, created with `mke2fs`, not tmpfs masquerading as `/data`. Its feature list excludes metadata checksums, 64-bit and orphan-file features; the exact creation command and superblock are captured. Each run has a separate disk copy. No disk image was downloaded to the Mac.

For each APEX, the static Linux fixture opened its complete APEX container on guest ext4 with `O_RDONLY|O_DIRECT|O_CLOEXEC`. An aligned 4096-byte `pread` succeeded. It followed SDK37 apexd's capability probe: `LOOP_CONFIGURE` with fd=-1 returned `EBADF`, proving this physical baseline has the newer ioctl backport despite its 4.9 version. Actual configuration with the payload ZIP offset, payload size, 4096-byte block size and AUTOCLEAR succeeded. `LOOP_GET_STATUS64` returned flags **21**: read-only, autoclear and direct I/O. No explicit `LOOP_SET_DIRECT_IO` override was needed in the final runs.

The adbd payload begins at byte **4096** of its decompressed original APEX; Google begins at **8192** of its signed APEX. The original CAPEX was decompressed on the host without altering the contained original APEX. Both original APEX containers were copied onto the disposable data disk; loop offsets select their real stored `apex_payload.img` members.

Two kernel mount/read levels passed for each payload:

1. Read-only EROFS directly over the loop device.
2. Read-only EROFS over a real dm-verity device using that payload's AVB descriptor: version, data size, data/hash block sizes, tree offset, SHA256 root digest and salt. Positive tables used `ignore_zero_blocks restart_on_corruption`, matching apexd's normal verification parameters. The final kernel also enables the physical baseline's verify-at-most-once default; actual `DM_TABLE_STATUS` output confirms `check_at_most_once` on all three mappings. This is the existing genuine hash tree, not a newly generated convenient tree.

All **30 adbd regular files** and **four Google regular files** were read and SHA256-checked at both levels. In particular, the guest decompressed and read the complete **217,107,692-byte Google Play services APK** from its EROFS image. The reads therefore exercise material filesystem content and compression, not only superblock acceptance. [payload-manifest.json](evidence/payload-manifest.json) records every file, size and expected digest; each actual digest is in the run result.

A separate corrupted adbd copy differs by one bit at payload byte 100. With the original AVB root retained, dm-verity reported `data block 0 is corrupted` and an actual direct read returned **EIO (5)**. The negative-control mapping deliberately uses apexd's verification-style EIO mode, without restart-on-corruption; a guest restart on corruption was not tested. The genuine payload inputs remain unchanged. This tests corruption present before the first verified read; the physical verify-at-most-once behavior is not a promise to detect later online changes to already validated blocks.

Before the guest run, the captured host `avbtool` verified both image signatures with their embedded RSA4096 public keys and verified both complete hash trees. This establishes image consistency/signature validity against those embedded keys. It does **not** prove Android's trusted-key selection, APK/container certificate allowlisting, rollback policy, or apexd activation.

## Genuine SDK37 Binder result

The probe is small C++ built outside AOSP with its existing Clang r584948b and the real exported headers from pinned Git archives. It links against the captured **core** Soong `libbinder.so`, with its genuine dependency closure. No old replacement library, fake Binder API, missing-function stub, fake ioctl acknowledgement, or platform rebuild was used. The ELF inputs were double-read and hash checked before freezing them outside changing product staging.

The test executes independent Android processes through the real SDK37 linker/libc:

- Server initializes `ProcessState`, configures and starts its thread pool, sets a real `BBinder` context object, becomes context manager, and joins the pool.
- A client obtains a remote service binder through a real transaction and registers another binder as a death-notification target. Its process then exits. The server receives exactly one real `binderDied` callback.
- Four client pthreads issue **200 synchronous transactions** and check all returned values. Multiple distinct server thread IDs appear in the captured log, exercising Binder thread-pool dispatch.
- The client sends **20 one-way transactions**, then confirms the server observed all **220** calls and exactly one client death. Transaction and reply statuses are zero; both clients exit zero.

`BINDER_CONTEXT_MANAGER ok=1`, `BINDER_MODERN_PASS`, and the structured `BINDER_RESULT` are in the serial log. The driver is protocol **8**. The server is deliberately terminated by the fixture after the checks; its final signal status is expected teardown, not a crash.

The unsupported-feature results are real and retained:

- `BINDER_ENABLE_ONEWAY_SPAM_DETECTION`: **EINVAL**. Real ProcessState startup tolerates this, and the explicit public API reports **-22**. The real libbinder diagnostic is captured.
- `IPCThreadState::freeze(pid, false, 0)` and `getProcessFreezeInfo`: **-22**. Freezer support is **absent**; these calls did not acquire successful freezer semantics. Ordinary IPC still proceeds.
- Raw `BINDER_GET_NODE_INFO_FOR_REF` from the non-context-manager fixture returns **EPERM**, which is a permission result, not evidence that the ioctl is absent. The physical driver implements this ioctl and extended context-manager registration. No legacy context-manager fallback was forced or claimed.

These results clear a specific basic modern-core-libBinder compatibility question. They do not establish every Binder ABI feature, frozen-state callbacks, framework cached-app freezer behavior, binderfs, HIDL/hwbinder or vendor namespace behavior. The guest uses the linker's default configuration and logs the absent generated linker configuration. Trace-file warnings are also retained. No Android init/property service or linker namespace readiness was fabricated.

## Exact inputs and source/configuration equivalence

The virtual source was extracted with `git archive` from committed **fcb1b6c2de6348e2724981dcd520dec631ed5255** into the owned remote fixture. It was never copied from a concurrently changing worktree. Comparison against physical baseline **717bb3c9e13ce573cfdd2dda856debd27a0fa17f** shows the **entire trees differ only in the existing generic GIC guard**. See [full-committed-kernel-difference.patch](evidence/full-committed-kernel-difference.patch).

[full-source-equivalence.json](evidence/full-source-equivalence.json) separately inventories Git object IDs and SHA256 for **282** files covering EROFS, ext4/JBD2, loop, dm, Binder, SELinux and relevant headers. The initial 27-option comparison was expanded to all relevant EROFS, ext4, dm, loop, Binder, SELinux and LZ4 options plus their key prerequisites. [config-expanded-comparison-r4.json](evidence/config-expanded-comparison-r4.json) confirms all **58** physical/runtime values match. Physical and startup baseline config hashes were independently matched against the existing local checkpoint files. This comparison is to the requested committed physical baseline, not a claim about later changes by the main-build owner.

Important SHA256 identities:

- Input adbd CAPEX: `ef9ffc28b94dc18e520f503d46ff099e7ef2e9fa366906b6d54bc2e7da6eea47`.
- Contained original adbd APEX: `bab495f2bb19fa3b301e2c307d975f4e5f59df5bc27955a8141f3b3b32e6870d`.
- adbd payload: `11e611a1745e1625c1ead03be133b866e0cec990105fd54dd8ad91c516f324a6`.
- Google release ZIP: `a6844eeb2613541558237e467b20feb01f8b45b2ebab0109834140ea59b6ca4d`.
- Exact Google GMS APEX: `fd56d1e45eb46c9a56253129242231c0d47555e568870ae39c1317ca818efa4c`.
- Google payload: `de1ccb4ea1967fc12be71fa3eeccaf3d6bd3ab6da7400ca0df192e6e07a4d162`.
- SDK37 core libbinder: `b431dce6d5d0c8cc2b4a8d32b09532c9abf94b1ebaf93d71d245cb1a8274e68a`.
- SDK37 libc: `151cc98631ea0621083d98704fed429c75514884ed16c55e91840da3b8d91a2a`.
- Passing virtual kernel Image: `113c4f19c736b949626c62bbf68cf23c9e3c5a821ec6ab031a5684cdcba14431`.
- Passing virtual kernel config: `63385c375a91fea35ae8c149295ce582c62fd02521d5766a592fad91043b6d7f`.
- Binder probe ELF: `953b94109b45ad470816449181b0072e6d72aac1e324e9a7f89beec061b22b7c`.

The complete 20-ELF closure's hashes, build IDs and dependencies are in [elf-manifest.json](evidence/elf-manifest.json); original paths are in [input-manifest.json](evidence/input-manifest.json). Header hashes, source revisions, actual compiler command and toolchain identities are captured. The original successful libc fixture is retained as a baseline; this experiment builds a different generic kernel with the additional real runtime prerequisites.

## Failures preserved and fixes made

- Binder compile r1: missing archived `libutils/binder/include` behind exported-header symlinks, plus a duplicate Android API macro. Fixed the real header fixture and removed the redundant define.
- Binder compile r2: outlined ARM64 atomic helper was not linked in the standalone command. Selected Clang's normal `-mno-outline-atomics` lowering for the Cortex-A53 probe; no symbol was stubbed. Later successful builds add real liblog stderr diagnostics and thread-ID reporting. Every compile log remains.
- Fixture run r1: the guest C probe ignored a `posix_memalign` result under `-Werror`. Fixed the allocation-error path; no VM ran for r1.
- Kernel build r1 / fixture run r2: Kconfig discarded EROFS because `MISC_FILESYSTEMS` was absent, and discarded SELinux because `AUDIT` was absent. EROFS mounts returned ENODEV. Modern context-manager registration succeeded, but transactions requesting security contexts failed with **EOPNOTSUPP (-95)** at the real `security_secid_to_secctx` path. Ext4/direct-loop/dm-verity/corruption rejection already worked. The run returned five guest failures and is preserved.
- Kernel build r2: enabled the real EROFS/SELinux dependencies and matched the physical baseline's selected options. These full kernel builds used **-j2** and exited zero. No kernel C code was changed. This is a fixture correction, not a required physical-kernel backport: those dependencies were already enabled physically.
- Fixture run r3: all guest operations passed, but the initial host parser required each digest immediately after its begin marker. Real linker warnings intervened. The original failed host result remains; independent marker-bounded reanalysis proves all 68 reads matched. Three parser tests check diagnostic tolerance and rejection of failed/missing/misaddressed reads.
- Fixture run r4: unchanged runtime workload with corrected result parsing; complete end-to-end pass on the initial 27-option-matched kernel.
- Expanded config audit: identified the omitted physical `DM_ANDROID_VERITY_AT_MOST_ONCE_DEFAULT_ENABLED=y`, plus dm-crypt, dm-uevent and LZ4 compressor differences. Kernel build r3 stopped before compilation when the new assertion caught that the hidden LZ4 compressor option needs its real `CRYPTO_LZ4` selector. That failed preflight is preserved. Kernel build r4 sets the real options, matches all 58 compared values, and completes with **-j2**, exit zero.
- Fixture run r5: final physical-option-matched kernel, same filesystem/Binder workload, plus actual active dm table capture. All 68 reads, corruption rejection and Binder checks pass; both QEMU and runner exit zero. No later runtime mutation or repeat is needed.

Fixture integration artifacts are [kernel-runtime-r4.config](artifacts/kernel-runtime-r4.config), [config-delta-r2.txt](evidence/config-delta-r2.txt), [config-delta-r4.txt](evidence/config-delta-r4.txt), [fix_kernel_config.sh](source/fix_kernel_config.sh), [match_dm_config_v2.sh](source/match_dm_config_v2.sh), and [check_expanded_config.py](source/check_expanded_config.py). The comparison now fails before compilation if the selected physical values do not match. Do not apply the virtual config or GIC fixture guard as a hardware configuration change.

## Parent integration and remaining prerequisites

No new physical driver patch is required by these successful workloads. Parent can advance the existing product build and its full first-boot services test without waiting for another EROFS/Binder prerequisite implementation. Preserve the physical EROFS, loop, dm-verity, Binder, AUDIT and SELinux options when integrating later kernel changes; rerun equivalence against the eventual committed kernel if relevant code changes.

The proof stops at verified kernel mounts/material reads and genuine basic core Binder IPC. **Not executed:** apexd itself, CAPEX decompression by apexd in the guest, trusted APEX key selection, APEX registration/activation, namespace construction, SELinux policy loading/enforcement, keystore/Keymaster crypto, module-hash completion, final APEX ready state, adbd execution/USB authentication, Android framework boot, or ASUS hardware. The guest has the real SELinux implementation enabled but loads no product policy. This is not an Enforcing-policy validation. No readiness properties or bootstrap services were stubbed.

Parent's next concrete gates remain the real product image/manifest/policy build; real internal-data provisioning/restore plan; integrated apexd + keystore + module-hash + final APEX + adbd path; and separately authorized hardware acceptance. Test app-freezer behavior explicitly because these Binder freezer calls are unsupported. Do not label this result a full-framework boot or use it to waive the physical restore gate.

## Reproduction and compact capture

Owned remote root: `/srv/android/asus-android17-runtime-prereqs`. Pinned inputs, extracted sources, all kernel build attempts and run directories remain there. No job is intentionally left running. All large kernels/initramfs/disks remain remote.

For another isolated run of the frozen fixture, choose a new unused revision:

```sh
python3 /srv/android/asus-android17-runtime-prereqs/source/run_fixture.py r6
```

The script refuses existing run directories, snapshots its source, builds only the small fixture init, copies its disposable ext4 base, bounds QEMU, and records the command, binary-input hashes, serial output and status. It uses the existing successful `build-r4` kernel and frozen real ELFs/APEXes. Inspect the failure log before changing anything. To recreate inputs in a separate authorized fixture, use the source scripts in order: `prepare_kernel.py`, `freeze_inputs.py`, `prepare_payloads.py`, `prepare_corruption.py`, kernel scripts and `build_binder.py`. They preserve or refuse existing inputs; do not rerun initial setup over this completed checkpoint.

Local checks:

```sh
python3 -B tests/test_material_parser.py
python3 -B tests/validate_evidence.py
```

[compact-r1.tar.gz](artifacts/compact-r1.tar.gz) is **268,757 bytes**, SHA256 `a12df32c40a7be53b27bfc06539955b124383784e0d75f204835b00f2b10b66b`. Its 92-file manifest verifies locally. The final supplement [compact-r2.tar.gz](artifacts/compact-r2.tar.gz) is **318,609 bytes**, SHA256 `319f3a56387e1e921c76a19d397e1adcdcc4663bb29b68f6ac9f96022891fed0`, and carries 119 manifest entries including the final run/config. Both captures verify: **211 manifest entries** in total. It contains compact evidence, source snapshots, configs and probe ELFs; no private keys, guest entropy seed, device data, or disk images. The final report, tests and supplemental baseline config checks accompany it in this spike.
