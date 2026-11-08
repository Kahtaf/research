# ASUS Android 17 handoff — blocked on hardware boot tracing

The goal remains blocked. No full-OS flash was performed. The tablet was last
verified running stock Android over authenticated Wi-Fi. Further bring-up needs
independent early-boot checkpoint evidence; do not start more guessed probes.

The latest compiled SYSTEM includes the BPF program-name compatibility fix:
`/srv/android/asus-bpf-name-product-build-20261107/system-partition.raw`,
3,753,902,080 bytes, read-only, SHA256
`fa41395749229849344b216a8fa55de3c0a9fd029bc90f05543f6ba0cc8550f5`.
One native build exited0; original BOOT and older raw images were preserved.
The new native library differs from the earlier isolated runtime candidate;
complete framework, physical hardware and runtime equivalence remain unproved.

The public 1 MiB chunk table and native receipt are local in
`2026-11-07-asus-bpf-name-product-build/evidence/`. The raw remains on the build
VM's persistent disk. The build VM is now stopped (TERMINATED); its labels and persistent disks are preserved.
Do not restart it or a native build merely because a stale notification arrives.

The card still has the earlier manifest9fe4 and oldSYSTEMfff09, plus the original
rollback and privateDATA sources. It is unarmed. That manifest does NOT admit
newSYSTEMfa413. A future authorized installation needs a fresh parent-local
manifest/card update and working physical kernel; do not mix artifact versions.
ExistingBOOT784d is unchanged and still uses the hardware-unproved e9 kernel.

OriginalSYSTEM4597a7..., BOOT7bb685..., recovery902b2f... and privatefactory
preservation remain intact locally. PrivateDATA/calibration/manifests stay local;
none was sent to the VM by this build.

Read `CURRENT_STATUS.md`, `PARENT_SELECTION.json` and the real hardware blocker
report before resuming. Historical one-shot installers are pinned to particular
images/boots; do not rerun them blindly. This is not Android17 completion or
flash readiness.
