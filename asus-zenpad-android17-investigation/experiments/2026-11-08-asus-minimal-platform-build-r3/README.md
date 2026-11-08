# Minimal-platform recovery candidate — packaged, no trial

Question: can the same reduced-consumer baseline build after restoring its vendor infrastructure dependencies, while retaining the reviewed protection closure?

Status: **one genuine candidate and full-p10 package completed for parent review. No device contact or physical trial.** The single r3 continuation succeeded, linked checks passed, one isolated installer PLAN passed, and the strict decoder passed synthetic controls. The exact VM is verified TERMINATED; its owned SSH master is closed. Partial out/vmlinux and full native log remain at `/srv/android/asus-minimal-platform-build-r3-20261108`.

History remains explicit: initial compiler failure, r2 final-link failure, then this one successful r3 continuation — three kernel make invocations total. The helper compiled once in the first unit and was reused byte-for-byte here. Both failed prefixes, preparation and current installation remain unchanged. No full clean, timestamp/.cmd manipulation, source repair, warning suppression or runtime variant.

| Genuine output | SHA256 | Bytes |
|---|---|---:|
| [Recovery candidate](artifacts/candidate.img) | `7ccd7d4554a764d0717c79d30668626c1fbd032218f8598bf7e4a2913bce30a1` | 3565568 |
| [Zero-padded full p10](artifacts/candidate.p10.raw) | `9939e802ab349dd01fe5ab9c643f2ce0d3219846e3f54513a9b1e9982146965c` | 16740352 |
| [Actual Image.gz-dtb](artifacts/Image.gz-dtb) | `d164cbbee409d192caf9b0135238f0382c2f66ed31e622cc0bdb4f815baa8cec` | 3241432 |
| [Resolved config](artifacts/resolved.config) | `01d6729f825798899e21192e6c33f96a80b47ccbedd5dc6cab10f78c1f9c7f31` | 80695 |
| [Compiled/runtime DT](artifacts/compiled.dtb) | `156e92ec5d4f5c4bd20169128c8aed0a89b43636d945d648392aaaec8b9bf82e` | 65873 |
| [Reused static ARM64 helper](artifacts/init) | `37e9e2a2d73447947fb33e57e9513fa6079517b571f5a41bc58fbb91f84633fc` | 772248 |
| [Reused wrapped ramdisk](artifacts/ramdisk.wrapped) | `69535be3b3b3bf160a05fb555078dd7eca239db55980fd8732f14ee7d6cc6082` | 320474 |
| [Genuine System.map.gz](artifacts/System.map.gz) | `f023ed88ca2f582b99b1a962c543a303475a7e6883174df0605862989241e183` | 440368 |

The System.map's uncompressed SHA is `cd169931cd16ca97f2e77d55232a2693fb54422861d62bacc82ebb1862249237` (2185619 bytes), bound to the native output. No vmlinux was fetched.

The parent requested config SHA `80bb4ae33a870ba8cfb44d65677f5e5e346ef0ebc6c411de7b4a13fe858e8e23` is input only. The gate used one initial olddefconfig and its one allowed visibility correction. Every newly enabled symbol is listed/classified in [final-config-gate.json](evidence/final-config-gate.json); the exact delta is [final-config-vs-r2.patch](evidence/final-config-vs-r2.patch). Only core NET/trace closure and the absent-LCD cooler removal differ effectively from r2. All other effective r2 settings remain equal.

Actual source/default facts:

- MET's built-in `met_api.o` calls `tracing_record_cmdline` unconditionally. Its API file has no boot/module init hook that starts a sampler; callback pointers default unset.
- TRACING selects nop/events/ring-buffer infrastructure. `trace_init` starts with nop and an empty boot event list; the generic tracing-on flag is enabled after initialization. Main and event-temp rings allocate minimum buffers (two data pages each plus reader/per-CPU metadata), not zero memory. The expansion target is 1441792 bytes; this cmdline/config does not force expansion or select a vendor active tracer. Function, function-graph, sched, syscall, probe/BPF-event tracers and startup tests remain off; DISABLE_TRACE_PRINTK=y.
- Three visible unwanted defaults are off: ANDROID_PARANOID_NETWORK, NETWORK_FILESYSTEMS, TRACING_EVENTS_GPIO. Hidden core RPS/RFS/XPS/BQL/queue helpers remain default-y. SECCOMP_FILTER also remains y: `arch/Kconfig` defines it default-y under existing SECCOMP and NET, so an explicit n cannot suppress it. It is a mechanical NET-dependent capability restoring the ancestor setting, not an installed helper filter or hardware/protection change. SECCOMP itself is unchanged; the helper installs no filter.
- NET adds core initialization, netlink, loopback and generic queue/steering support. It is an explicit confound beyond uevents. Protocols, NETDEVICES, WLAN/BT/radio/CCCI/connectivity and all reviewed consumer drivers remain off. UEVENT_HELPER behavior is unchanged.
- VS_BACKLIGHT_COOLER controls only LCD brightness through `setMaxbrightness`; its public-symbol references in the scoped thermal source occur only inside that file. Bind-by-name cooler references can remain without that absent display consumer. CPU/battery/PMIC critical and shutdown paths were not removed.

The actual linked kernel defines tracing_record_cmdline and register/unregister_netdevice_notifier. setMaxbrightness, backlight_list_head and the backlight-cooler init are absent, and the new thermal built-in command excludes that object. A stale copied cooler .o remains on disk as preserved build cache; it is not linked. DEVAPC retains the ancestor TEE branch. Selected BAT/SOC/BQ, CPUFreq/HPS/GPUFreq, thermal shutdown, watchdog/reset and ordinary retained-writer call paths were checked. No new warning signatures appeared against the calibrated ancestor; existing linker -z norelro/RWX warnings are disclosed in the native log summary.

All 99 consumer DT status overrides are unchanged. DT bytes, reserved-memory block, secure pool and helper/initramfs hashes match the prior attempt. The only kernel source difference from r2 is entry config-hash metadata; the source DT identity is honestly labeled `dts-source`. UUID remains `a60fca94-e760-4ce5-a790-5c9a818ce406`. The entry text appears twice as binary constants (assembly payload and C authentication constant), but the physical decoder requires one unique fresh console entry. Early 8250 remains absent and watchdog registration level/order is unchanged.

Actual Image.image_size is 7593984, larger than the 7141888-byte raw file. At load `0x40080000` its end is `0x407be000`, below initrd start `0x44000000`. Reused gzip payload is 319962 bytes, excluding the 512-byte wrapper; exact end `0x4404e1da` remains below console `0x44400000`. Calibrated 0xc0 admission and all structural/memory guards remain. The package preserves Android-v0/2048-page geometry, MTK wrappers and load addresses, exact hashes/alignment and constant-zero full-p10 padding.

The one offline package was constructed and round-tripped once. A missing host Python `re` import then interrupted installer metadata generation; that error is preserved and corrected by metadata finalization from the same candidate bytes, without reconstruction or native rebuild. The exact [minimal profile](source/minimal-profile.json) validates actual compiled/config/DT/helper inputs and only the reviewed DT delta outside the common mutating controller. execute/Transport/Guard and adapters remain byte-identical to the inherited installer, with adb mode 0755. Only supplied current preimage `d78e6ddd7f4a555201515df3aef6d8d7f15203c20e3b8d201ea7eb2f4c5df081` was appended; it was not freshly observed.

Review [packaging receipt](evidence/packaging-receipt.json), [linked checks](evidence/linked-verification.json), [PLAN/isolation receipt](evidence/plan-isolation-receipt.json), [decoder controls](evidence/decoder-checks.json), and [parent commands/run contract](PARENT-HANDOFF.md).

This is a reduced-consumer baseline with retained thermal/PMIC/BQ inhibition, BAT/SOC/notifications, CPUFreq/SPM/HPS/idle, TEE and watchdog/power-key closures, plus core NET/trace infrastructure. It is not bare-core. A positive or negative trial cannot uniquely locate the prior fault. No physical protection, calibrated walltime, storage or fullOS qualification is asserted. Parent owns the same experiment's first trial; no automatic add-backs, repeat build or trial after an ambiguous/negative outcome.
