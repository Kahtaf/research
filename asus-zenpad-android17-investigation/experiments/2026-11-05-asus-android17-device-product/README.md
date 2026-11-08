# ASUS P00A Android 17 device product

Question: Can a real ASUS-specific LineageOS 24 product consume the verified MT8163 kernel/header source and compile Android 17 init/adbd, clearing the generic mini_arm64 target's missing Lineage kernel-variable failure?

Status: SDK 37 / Android 17 init, ADB, networking modules and the broader
framework/runtime/SurfaceFlinger module builds passed. The latest framework
checkpoint has nine locally verified files, including real ARM64 binaries and
compiled framework/services DEX. The next live GCP job has applied legacy-kernel
compatibility and is building boot userspace, ASUS backlight/memory adapters and
the first framebuffer graphics stack. Full system/ramdisk, hardware runtime,
Google integration, data migration and custom-image restore remain unfinished.
No complete or flash-ready ROM is claimed.

Inputs: Pinned platform checkout on the labeled GCP VM; verified EROFS-capable hardware kernel from the sibling kernel-backport spike; actual ASUS architecture, screen and live GPT metadata. Kernel headers must come from that real source, never fabricated includes.

Outputs: device/asus/p00a configuration, repeatable deployment/build scripts, pinned kernel/header provenance, build logs and any successful init/adbd artifacts. The active module target keeps image generation disabled. candidates/full stages the actual full-system configuration separately; the measured MTK format is implemented in the sibling boot-image spike.

Continuation: Read STATUS.md when available. Use the existing experiment VM (resource ledger under ../2026-11-05-asus-p00a-power-port/infrastructure/README.md). Keep the tablet in Android during this source work. Do not infer hardware operation or a successful Android 17 boot from module compilation.
