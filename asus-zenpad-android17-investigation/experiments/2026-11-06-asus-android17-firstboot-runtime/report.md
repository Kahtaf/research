# SDK37 first-boot runtime: qualified gates and remaining dependencies

DRAFT: r7/r11 entries below await the final runtime rerun. Existing r6/r10 results are confirmed; placeholders are not qualifications.

The genuine init, ueventd, SELinux, cgroup and property-service gates now pass. Software Keymaster, keystore, APEX activation, final linker configuration and authenticated adbd remain unproved because genuine compiled prerequisites are still absent from the running main build. This is targeted virtual runtime qualification, not a complete Android boot or physical release approval.

All work stayed inside this spike and /srv/android/asus-firstboot-runtime. Physical source, active main r5 OUT, qualified pristine internal data, parent-only calibration records and the device remained untouched. No concurrent Ninja, physical ADB/USB, private key contents, signing or readiness-property injection was used. Compiles were serial; QEMU used one CPU, 1–1.5 GiB and no network interface.

## Preserved evidence and authoritative build state

Accepted capture-r1 remains SHA256 06dace070ff5e9ef11a48ae70fc718b1c42e00e11884ee619c5cdb06f5aa79c8. All 119 frozen entries were rehashed without a mismatch. Its policy-v30/enforce=1 and genuine init-stage/property-socket proof remains intact. Failed runs and failed preparation attempts are retained.

There was no live firstboot process at continuation. Isolated kernel-build-r5 was genuinely complete: returncode0, terminal Image link/objcopy log, and matching hashes. It was reused, not restarted. Main siso PID132874 was the original running product job. Completed r5 and r6 fixtures were preserved.

The final test kernel is kernel-build-r7:

- Image SHA256: @IMAGE@
- Config SHA256: @CONFIG@
- Authoritative command/status/log: evidence/kernel-r7-command.json, kernel-r7-status.json and kernel-build-r7-compile.log.

## Exact physical changes

The minimal defconfig patch, stagedpatches/blkio/0001-enable-blkio-cgroup.patch, adds only CONFIG_BLK_CGROUP=y after CONFIG_CPUSETS=y in arch/arm64/configs/asus_p00a_defconfig.

- Patch SHA256: b13f28962f985a0c50c8c5599ac6730df9361e6bc486fe4fb194ec4137df602f
- Physical before: 364ee3bbda2f7c8a2bf16508fff9da1a070de012ceecfb13209086240aaedde2
- Physical after: ae86c367dd8919e3fb55a18209a2075330f49c2b6e83b40226a38c832fd7e01d

That one line alone is insufficient. Fresh run-boot-r8 passed the blkio obstacle but failed the next mandatory cpuset mount. Its failure and normal apexd-bootstrap-failed shutdown are retained.

The additional source patch, stagedpatches/cpuset-v2/0002-cpuset-v2-mode-backport.patch, has SHA256 8290f3f6ebbfa81c630c76730b4bec701679995fcc502ef4666f8b050f941163. It changes only include/linux/cgroup-defs.h, kernel/cgroup.c and kernel/cpuset.c. It implements the requested cpuset_v2_mode option and real v2 cpuset behavior on a v1 hierarchy; the option is not ignored and userspace flags are not weakened.

It adapts upstream [mount-option support](https://github.com/torvalds/linux/commit/e1cba4b85daa71b710384d451ff6238d5e4d1ff6), [v2 semantics](https://github.com/torvalds/linux/commit/b8d1b8ee93df8ffbabbeadd65d39853cfad6d698), and [the safe bind-cached flag](https://github.com/torvalds/linux/commit/e06b678e3b4e12fdaa0b51a7a5a54abc5dbd6469).

Both patches applied with fuzz=0 to isolated copies of the physical baseline. Resulting source files byte-match tested source; physical files still match their before hashes. Exact per-file identities and commands are in stagedpatches/cpuset-v2/manifest.json and evidence/physical-apply-validation.json.

Final equivalence caught FILE_LOCKING=n in the old fixture, although the physical baseline already has FILE_LOCKING=y and MANDATORY_FILE_LOCKING=y. R7 restores both existing physical values. This is a fixture correction, not another physical defconfig patch. The first preflight rejected the dependent mandatory-lock option; its failed log is preserved, and compilation proceeded only after checking both values against physical configuration.

Evidence checks 288 selected Binder/filesystem/SELinux/cgroup source files and 134 core/runtime-prerequisite configuration options. Only the staged cpuset files and intended BLK_CGROUP enablement differ in those comparisons. The inherited virtual GIC guard remains fixture-only. These scoped checks do not make a QEMU board configuration a hardware defconfig.

## Runtime results

The unchanged SDK37 cgroups.json is SHA256 ab2ed667ff45958843fb0c6ee953a5512def0ae87470c4358aa9576a6a4b2e22.

- run-cpuset-r1 is the negative control: the old kernel rejects cpuset,noprefix,cpuset_v2_mode with ENOENT while blkio mounts.
- run-cpuset-r3 passes 13 actual kernel checks: mount support, empty configured CPU/memory masks, inherited effective masks, task attachment to the empty child, mask clearing, cleanup and blkio mount. CPU hotplug is not claimed on this one-CPU guest.
- run-locks-r1 passes five POSIX lock checks. Another process is denied while the first owns the file lock, then acquires it after release. This is a prerequisite test, not keystore crypto proof.
- run-policy-r4 loads the actual 872537-byte product policy on policy-version30. Enforcement is1 before and after loading.
- run-boot-r11 executes genuine first-stage, SELinux and second-stage init. SetupCgroups succeeds. Init creates /sys/fs/cgroup/system/uid_0 and ueventd's PID subgroup; the observer reads the actual ueventd PID back from cgroup.procs.
- Actual domains are u:r:init:s0, u:r:ueventd:s0 and u:r:shell:s0, with enforcement1. Genuine ueventd completes coldboot. Init's read-only property expansion confirms ro.cold_boot_done=true. Shell cannot read that protected property; its empty read is not evidence that the property is absent.
- Init creates both genuine property sockets. Allowed diagnostic-property IPC succeeds. The forbidden persistent-property write receives PROP_ERROR_PERMISSION_DENIED, identifying source_context shell and target_context default_prop, and remains unset.

Evidence/qualification-r3.json records @CHECKS@ assertions against raw commands, statuses and serial logs. QEMU exit0 alone is never a boot pass. Earlier init-builtin copies of /proc/1/attr/current were rejected as insecure; direct observer reads provide the SID evidence.

The physical baseline lacks MEMCG. SDK37 marks memory optional; memory_recursiveprot fallback and ignored activation warnings remain visible. Memory-controller enforcement is not claimed. The shell's denied stat of protected socket paths is also preserved; init's creation log proves socket existence.

The actual fatal next gate remains missing /system/bin/apexd. Init performs its ordinary bootstrap-apexd-failed shutdown. Optional missing init_dev_config/ODM files are distinguished from this fatal dependency. No crypto wait, service dependency or platform readiness gate is bypassed.

## Genuine generator progress

Captured Ninja/Soong inputs ran only in fixture mirrors with the product's pinned JDK21, ActiveProcessorCount=1 and a 1GiB Java heap.

- current.txt: 7,607,194 bytes; SHA256 4865a5551f39ddbf843900c915d63101e2809f4eafb782edb15466c26e31f86d; generator returncode0.
- system-current.txt: 2,609,874 bytes; SHA256 b9f4bf98c5cb7126326fa9ee8ea758a801c770c0b20013e2e681ad449e7f6b54; generator returncode0.
- Exact aggregate apexkeys packaging metadata: 39 entries; SHA256 @APEXKEYS@. This does not establish runtime APEX trust or activation. Apexd uses bundled public keys in preinstalled APEXes; no private key material was read or APEX re-signed.
- Exact generated vendor properties are used unchanged.

System/system_ext/product properties still need the real API fingerprint. Module-lib-current lacks the OnDeviceIntelligence module-lib API text. System-server-current lacks ConfigInfrastructure, HealthFitness and Media service API texts. Their underlying metalava manifests are captured too: genuine AIDL source jar, flags configuration, API-reference files and Java/protobuf jars are missing. Inputs/missing-api-rules-r1/inventory.json lists exact dependencies. No guessed SDK/version/fingerprint values were substituted.

## Remaining service gates

Final captured link dependencies remain incomplete; counts include TOC validation inputs:

- apexd: 22
- hwservicemanager: 7
- keystore2: 80
- servicemanager: 5
- SOFTWARE Keymaster service: 5

Evidence/service-dependencies-final.json records exact paths, variants and timestamp. Keymaster specifically lacks service.o and vendor-CFI ACCOUNT_REDACTED/libkeymaster4.so plus their TOCs. An isolated relink cannot replace these missing implementations.

The genuine linkerconfig binary and signed adbd APEX were frozen for continuation in inputs/late-outputs-r1. Their hashes are 84aed523ecc7be896ec0263b7d72a2ca693ab1a2168a471923a6da368d2e4515 and bab495f2bb19fa3b301e2c307d975f4e5f59df5bc27955a8141f3b3b32e6870d respectively. No normal service-chain startup or authentication result is claimed from their availability.

Still unproved: HIDL registration; SOFTWARE getHardwareInfo; key generation/sign/verify; keystore boot-level keys and module information; bootstrap/post-data APEX activation with real trust/verity; module-list/hash completion; final linker namespaces; and untrusted-denied/trusted-accepted adbd authentication.

## Networking coordination and continuation

Networking manifest d6790e2efde8ddb11102f561b5c58129660be09d41f1bbfb66402f3865ef13dd and all60 listed payload hashes match. Kernel patches01–04 and Connectivity11 are the qualified set; experiment10 is excluded. Their five kernel files do not overlap the three cpuset files. Retain physical FILE_LOCKING=y. DUMMY/VETH/NAMESPACES/NET_NS remain network-fixture-only.

The main owner received exact patches, hashes, runtime evidence and equivalence findings. Networking patches were not silently merged into this fixture. Final radio+network+firstboot integration/build/runtime remains with that owner; independent results do not establish combined hardware or Android/WiFi/Google readiness.

Preserve accepted captures, failed runs and completed kernels. Do not rebuild r7 because an agent turn ended: inspect its successful status, terminal log and hashes. Wait for the exact missing genuine outputs, copy/hash them into a new input revision, and continue normal init sequencing with real crypto and signed APEXes. Use new numbered runs and existing resource limits. Never force apexd.status, keystore.module_hash.sent, sys.boot_completed or equivalent readiness values. No device operations are part of this handoff.
