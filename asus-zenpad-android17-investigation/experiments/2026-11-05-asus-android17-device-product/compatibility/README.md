# Android 17 on the legacy ASUS kernel

This is a first-boot compatibility path, using the real Android 17 / SDK 37
platform. Kernel releases and the ASUS identity are reported accurately.

The source reference is qcom-toolbox/EVOLUTION-X-DANDELION-17 at
`75f316ebd586d93e98fb912a273a33e8845dc3d7`. Four relevant patches apply cleanly
to our pinned platform revisions. The fifth patch adapts an additional 5.10
release check in our Connectivity revision to the same explicit legacy opt-in.
All patch contents and hashes are recorded in series.json.

The compatibility changes cover:

- libc random-state fork handling when the kernel lacks MADV_WIPEONFORK.
- Linker configuration when VNDK/sanitizer variable lists are empty.
- Missing AIDL Power HAL support information during system_server startup.
- Legacy BPF loading and unavailable ring-buffer consumers, selected only on
  an actual pre-4.14 kernel with ro.bpf.allow_legacy_kernel=true.

The network fallback can lose per-app usage accounting, offload and newer
network metrics. It is experimental and does not prove that ASUS Wi-Fi works.
Source review confirms BpfMap.h only requires map-info introspection on 4.14+;
full modern BPF introspection/tag parity is therefore deferred unless an actual
first-boot failure needs it. The completed ID/FD kernel work is retained.

The Linux build tree is changed only after the current framework job exits
successfully. continue_userspace.py checks the entire patch sequence on copies,
records the changed source, then invokes build_legacy_userspace.sh. That script
retains the framework checkpoint, builds static first-stage init, real linker,
shell/tools, framework/network compatibility and the ASUS lights/memory modules.
It then deploys the staged graphics library copies and compiles the platform's
legacy graphics adapters plus the actual proprietary ELF modules.

No script here flashes the tablet. The full-system candidate and data/Google
integration still need completion before an upgrade image is ready.
