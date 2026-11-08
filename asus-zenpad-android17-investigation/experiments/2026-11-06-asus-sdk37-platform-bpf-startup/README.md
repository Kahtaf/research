# SDK37 platform BPF startup supplement

Question: Does the genuine SDK37 Rust loader, with the recovered ring-buffer debug self-test minimum-version patch, pass the observed startup abort on the qualified ASUS Linux4.9 kernel with all available selected BPF objects?

Status: **Completed as offline parent input.** All eleven selected platform `.bpf` files were captured and tested. The genuine preimage aborts on the ring-buffer debug object; the rebuilt exact postimage reaches actual SetProperty exit125. Mandatory corrupted-netd rejection remains intact. Optional platform features and property-service readiness are not qualified. The selected vendor power-supply BPF output remains missing.

Important outputs:

- [Report](report.md): actual tests, provenance, limitations and continuation.
- [Qualified handoff manifest](artifacts/supplement-qualified-r2/manifest.json): SHA256 `cdf539022affce9641cbe91da18e9323fb48322ad6443240c30d9bbf7f8a3fe2`.
- [Compact handoff archive](artifacts/supplement-qualified-r2.tar.gz): exact patch/pre-post source/ELFs/configs/build and runtime logs/object metadata/pins.
- [Future parent kit delta](PARENT-KIT-DELTA.md) and [machine-readable delta](parent-kit-delta.json).
- [Local archive verification](evidence/local-handoff-verification-r2.json): all201 manifest-listed files verified.
- `source/`: owned capture/build/test/package scripts. Earlier failed fixture/parser/package attempts are preserved; qualified-r2 is the final handoff, not a product staging revision.

Continuation: Review the report and new-kit delta. Only the parent may integrate into a newly reviewed kit revision; do not modify sealed staging/kit r2 or core handoff-r1. Rebuild the postimage in a separately authorized final product build and bind its actual ELF through installation and final SYSTEM payload validation. The fixture ELF is not a product drop-in. No new kernel config requirements, physical GO or full-OS-ready claim is made. This offline supplement does not block the first kernel RAM probe.

All remote writes stayed under `/srv/android/asus-sdk37-platform-bpf-startup-20261106`; its `supplement-qualified-r2` matches the local bundle. Larger immutable build dependencies, runtime shared libraries, Image and initramfs remain there. Builds/tests used one CPU; successful tests used a hard1GiB host-process address-space cap,384MiB guest RAM and under184,000KiB peak host RSS. Completed native jobs were reused after the refined selection audit.
