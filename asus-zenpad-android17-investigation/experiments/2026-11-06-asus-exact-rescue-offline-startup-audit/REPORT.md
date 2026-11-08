# Finding

**No deterministic boot/init/adbd contradiction was established in the exact installed image. Do not patch it on the basis of this audit.** The highest-confidence positive finding is that USB enumeration depends on successful userspace FunctionFS setup: the exact stock kernel deliberately keeps this gadget disconnected until FunctionFS is opened and descriptors are supplied. A failure in init, the proxy's admission checks, or stock adbd can therefore produce the observed screen with no usable ADB endpoint even after kernel execution.

The unresolved boundary is recovery handoff and the *runtime* initrd bounds, through init's first/second stages, ueventd/coldboot, service admission, and adbd's FunctionFS descriptor write. No retained boot error or positive execution marker from this attempt narrows that boundary further. This is not evidence that the kernel never ran.

The first host USB-bus snapshot was empty. The subsequent approximately 45-second observation sampled **ADB inventory**, not a continuous USB-bus trace. Transient hardware enumeration is unknown. Red warning/ASUS logo alone proves neither Linux nor init execution. The user subsequently reported normal Android returned using physical Power; this audit did not verify live device state. Under the latest steering, original-p10 restoration is deferred to the parent rather than prescribed as mandatory cleanup. No active OS flash is justified by this audit before boot-path/fallback proof.

# Exact artifact checks

`scripts/inspect_images.py` independently reads the saved candidate and original recovery, validates Android header component sizes and SHA-1 ID, validates both MTK wrapper lengths, parses all cpio entries, and computes the padded partition digest in memory. No image is emitted.

* Candidate: 10,412,032 bytes, SHA256 `5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f`.
* Full p10: 16,740,352 bytes, SHA256 `3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a`.
* Wrapped kernel: 7,472,341 bytes, SHA256 `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`, **byte-identical to original recovery**. Kernel gzip payload expands to 16,963,568 bytes; a valid 62,482-byte DTB follows it. The exact kernel identifies itself as Linux 3.18.35, built August 9, 2018.
* Ramdisk header size: 2,936,068 bytes including the 512-byte MTK wrapper. Payload: 2,935,556 bytes. Calling this entire payload a compressed ramdisk hides its mixed format.
* Payload member one: gzip at offset 0, 2,159,874 compressed bytes, 5,167,616 expanded cpio bytes. Two zero bytes follow it. Member two: raw newc at payload offset 2,159,876, 775,596 bytes through its trailer, containing the 775,344-byte `sbin/p10-restore`. Final payload padding is zero. Entries do not collide across members.
* `/init` SHA256 `e9594c0d1cbe7d05d34acd63e90b424672360ceb09112fa16b5b23390c21b7e5` and `/sbin/adbd` SHA256 `78a7adbda0a28da4055da1ea68a2ead8ee01764a365778930ef03e6649dcb450` are byte-identical to the original recovery binaries. They are static AArch64 ELF executables with no interpreter or dynamic-loader dependency. The actual proxy is static AArch64 too, SHA256 `f915eca1b2ae5250afef76d3154a853b933278c283f82cfb4eb0cee7d2736d0f`, matching its recorded tool pin.

Evidence: `evidence/image-audit.json`, `evidence/elf-audit.json`; selected original binaries/configuration are under `extracted/`. Public key contents were not separately extracted or printed.

# Range, DT and actual stock-kernel unpack contract

The header loads the ramdisk at `0x44000000`; including its wrapper it ends at `0x442ccd04`. Its payload begins at `0x44000200` if the loader leaves the wrapper at the load base. The saved appended DT reserves ATF at `0x43000000..0x43030000`, ram console at `0x44400000..0x44480000`, and minirdump at `0x44570000..0x44580000`. The candidate does not intersect these fixed reservations, and ends 1,258,236 bytes before ram console. The original recovery declares a larger ramdisk ending at `0x443ccab6`, also below ram console. The nominal expanded Image memory extent from its ARM64 header is `0x40080000..0x41335000`, far below the ramdisk. This checks saved static ranges, not the bootloader's live allocations or dynamically chosen consys reservation.

The appended DT's **static** chosen bootargs contain `initrd=0x44000200,0x200000`. Taken literally, that 2 MiB bound is too short even for the candidate's first gzip member. It is also shorter than original stock recovery's payload. It is **not proof of this failure**: the bootloader can replace bootargs and supply `linux,initrd-start/end`. Historical, publicly retained normal-boot DT properties in the kernel-bringup spike contain `start=0x44000000`, `end=0x442689e0`; those are different from the static defaults and belong to a different boot. The recovery attempt's actual DT/command line is unavailable. Do not silently substitute either static defaults or historical normal-boot values for it.

`scripts/kernel_contract.py` decodes **70,337 symbols from the exact kernel binary**, validating every compressed name, every marker, and all 256 token indices. Only small selected function slices are written as analysis ELF files; no full kernel copy is written. `evidence/kernel-contract.json` pins each slice; `evidence/kernel-functions.disasm` contains installed Apple LLVM 21 disassembly.

The actual `unpack_to_rootfs` at `0xffffffc000f15308` checks raw newc's `'0'` byte and stream-offset alignment at `...f153c4..f153d8`, skips zero padding at `...f15410..f15424`, invokes a decompressor at `...f1543c..f1546c`, advances by its consumed-byte count at `...f154d0..f154e4`, and loops. Thus **this stock kernel supports the gzip-plus-aligned-raw-cpio shape**, rather than relying solely on a different QEMU compatibility kernel. Full candidate parsing and a deliberately truncated 2 MiB gzip check are recorded in `format-boundaries.json`. These are host format checks, not execution of the hardware kernel.

Actual `populate_rootfs` at `0xffffffc000f156d0` passes `initrd_end - initrd_start` into that unpacker. Actual `early_initrd` at `0xffffffc000f180dc` parses the comma-separated command-line address and size and stores both bounds. Therefore wrong runtime bounds would matter, but this attempt's bounds remain unknown. No saved static-size contradiction justifies a resizing patch.

# Init, properties, labels and service execution

The actual init is the original SDK24 recovery init. Its disassembly and retained source explain first-stage basic mounts, SELinux policy load, relabel/re-exec of `/init`, second-stage property/default initialization, configuration parsing, early-init and ueventd/coldboot before init actions. Retained `inputs/init-main.cpp` / `init-service.cpp` are reference source; their exact build identity with the 2018 ASUS binary is **not established**. Decisions here use binary evidence where material.

The candidate's actual configuration explicitly starts ueventd in early-init and starts os-rescue/adbd during init. `disabled` services can be explicitly started; omitting class_start is not by itself a contradiction. `sbin/ueventd` is a symlink to `../init`, consistent with init's basename dispatch. Default properties retain `ro.secure=1`, `ro.adb.secure=1`, `ro.debuggable=0`, with no TCP listening port configured. The explicit init action starts adbd independently of a debuggable-property trigger. No imported stock recovery service, powerctl action, or automatic-return trigger is present. Physical Power was needed for the reported return.

**Rejected hypothesis, explicitly corrected:** the five-path `restorecon` line is valid for this binary. Its registration tuple is at `0x52bf50`: minimum 1, maximum unbounded, function `0x407ba0`; that function iterates over all supplied paths. The preceding single-argument tuple at `0x52bf38` belongs to `restart`, not restorecon. Initial inspection briefly misassociated those adjacent initializer entries; the full registration/copy layout and function disassembly corrected it. `evidence/builtin-contract.json` retains exact bytes and mapping. No split-restorecon proposal is warranted.

Actual compiled contexts were decoded from the extracted candidate, not assumed from current source. `/sbin/rescue-proxy` and `/sbin/adbd` match `rootfs`; `/system/bin/sh` has the explicit `shell_exec` override; os-rescue has `os_rescue_exec`. Native libsepol queries of the **actual extracted version-30 binary policy**, including its constraints, confirm:

* init can transition to adbd; adbd can enter/execute `rootfs` and execute the second stock adbd without another transition.
* ueventd can enter/execute `init_exec`, the target of its symlink.
* init can relabel the shell and rescue executable; `shell_exec` can associate with rootfs; init can enter os-rescue, create its socket/state, mount FunctionFS and write the queried USB/sysfs types.
* adbd can read its own proc-file label and SELinux enforcement file, getattr the shell executable, access FunctionFS files, and set the ffs property. A blanket `adbd -> proc:file` denial is not sufficient to prove `/proc/self/attr/current` fails: per-process proc inodes use process-derived labels, and the self-label permission exists.

The local query tool was compiled sequentially for this Mac using the existing public vendored Android 7.1.2_r39 libsepol sources, read only. It reads policy; it does not write/load policy. Sources, tool hash and compiler arguments are pinned under `evidence/native-policy-tool/`. `policy-queries*.json` holds actual outputs. Decoded context regexes alone are not a live xattr observation, and allowed policy queries do not prove successful mounts/relabels/service execution on this attempt.

# Proxy, stock adbd and FunctionFS lifecycle

The actual proxy's `main` disassembly at `0x4006d0..0x40075c` confirms that `--adbd` requires root UID, enforcement, domain `u:r:adbd:s0`, and the actual `/system/bin/sh` xattr `u:object_r:shell_exec:s0`. Failure returns 77. Success executes `/sbin/adbd`; exec failure returns 74. These are real possible failure points, but none was observed in a retained log. Source `proxy.c` is consistent with this binary; source-only reasoning is not being used to assert a runtime exit.

The actual stock adbd checks `/dev/android_adb` and `/dev/usb-ffs/adb/ep0` around `0x400c44..0x400c70`, initializes USB through `0x42116c`, opens FunctionFS endpoints/writes descriptors, and sets `sys.usb.ffs.ready` around `0x422bc4..0x422bd4`. Its static libraries do not require an absent `/system/lib*` tree. Authentication and restricted shell proxy remain separate later steps; no endpoint absence proves their failure.

The **actual stock kernel** `ffs_function_enable` at `0xffffffc000785914` sets enabled and increases disconnect depth while unopened. `functionfs_ready_callback` at `0xffffffc0007859b0` marks opened and, when enabled, decrements the depth and connects only at zero. `functionfs_closed_callback` at `0xffffffc000782850` disconnects an enabled function again. This confirms that writing gadget `enable=1` before `start adbd` is not itself an ordering deadlock. It also establishes why a proxy rejection or adbd endpoint failure can leave no enumerating gadget. Missing `on property:sys.usb.ffs.ready=1` is not demonstrated as a defect for this older android_usb driver: its kernel callback handles readiness, and original stock recovery uses the same enable-before-start ordering.

# Smallest discriminating next step

First, if the parent already has sanitized retained boot errors from the normal return, inspect only the short relevant lines: actual command line/initrd bounds, unpack errors, `init first stage` / `second stage`, coldboot timeout, init.rc parse/relabel errors, service exit 77/74, or FunctionFS endpoint/descriptor errors. No new target collection is authorized by this report. A single such line may avoid another recovery trial entirely.

If no retained execution marker exists, the narrow recovery-only **control test** is the already saved, hash-verified original stock recovery kernel+ramdisk in p10, with normal BOOT/SYSTEM untouched. The discriminator is the original stock **recovery UI**, not ASUS logo and not assumed ADB availability. Original recovery has `ro.debuggable=0`, so lack of ADB is not a failed control. Parent must first reestablish the cable/identity and handle its existing p10 writer/readback safeguards; this report provides no command or physical GO.

If that control reaches the stock recovery UI and physical return restores normal Android, recovery slot selection, loading, stock kernel, original initrd/init/UI are positively exercised; the custom ramdisk/services become the next target. If it fails before the recovery UI, changing rescue policy/proxy is premature. This is a reason to use original p10 **as a diagnostic control**, not a blanket restoration mandate. It does not commission the independent rescue endpoint or authorize Android17 flashing.

For any later custom-recovery trial, observe actual host USB-bus changes as well as ADB throughout the bounded interval, and retain positive startup evidence. Do not repeat the identical trial with ADB-only sampling and treat another absence as localization. A future instrumented recovery would be a separate parent-owned, source-reviewed task; no new diagnostic image or service change was created here.

# Reproduction and limits

Run the inspectors under `scripts/` by their file paths with `python3 -B`. `inspect_images.py` writes selected extracted startup artifacts and metadata; `elf_audit.py` reads those extracted ELFs; `kernel_contract.py` reads the original saved kernel and emits only selected function slices. `native_policy_tool.py` compiles the read-only host inspector from existing public sources; no network or target build is involved. The exact manual LLVM ranges are captured in `evidence/startup-windows.disasm` and binary tables in `builtin-contract.json`.

`public-input-pins.json` and `final-preservation.json` verify originals remained unchanged. Original images, production sources, flags and adapters were never modified. No source-only fix is staged because no defect passed the evidence threshold; `proposal/DECISION.md` records that decision.

Execution was local and sequential. Inspectors had finite CPU limits and bounded decompression/input sizes. Darwin rejected both 1 GiB RLIMIT_AS and RLIMIT_DATA requests (`current limit exceeds maximum limit`); that failed enforcement is recorded rather than claimed successful. Linux affinity is unavailable here; no parallel work was launched. No network, SSH, VM, cloud, device/ADB/root/USB command, process inventory, private-parent folder, key, factory/calibration input, active R9 source/output/cache, product build, image writer, reflash or reboot was used.
