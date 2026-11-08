# SDK37 BMC156, platform BPF and vold build kit r3

Question: can the sealed r2 candidate be extended with the exact BMC156 kernel, genuine ARM64 sensor sources, platform BPF patch12 and sole vold include fix without changing active AOSP or prior revisions?

Status: implementation complete, sealed and tested. All 40 bounded Linux tests and the real 61,976-file baseline / 276-postimage / 62,228-file compiled-source audit passed. The actual sealed preflight at 2026-11-06 22:13:43 UTC refused absent parent acceptance of failed r5 (exit 20). No attempt or r6 build exists from this work. This is ready for parent review, not physical/runtime approval.

Important outputs:

- [HANDOFF.md](HANDOFF.md): exact builder launch command, parent failure-review requirements and remaining gates.
- [REPORT.md](REPORT.md): implementation, actual test results, native-check limits and preserved errors.
- [inputs/kit-pins.json](inputs/kit-pins.json): 90 sealed source/input/test files; SHA256 `a00ea8d7c944d45e3035296c81b31a369f13bde830f88a7165b0d7542960717c`.
- [kit-seal.json](kit-seal.json), [ARTIFACTS.sha256](ARTIFACTS.sha256), `evidence/`, and `source/combined-from-original.patch`: integrity and reproduction evidence.
- `artifacts/r3-kit-compact.tar.gz`: exact compact kit, documentation, seals and preserved evidence.

Continuation: use the existing `/srv/android/asus-reviewed-build-kit/r3` and `/srv/android/asus-product-integration-staging/r3`. Read HANDOFF.md, inspect current process identities, and allow any parent native build to release the original flock. Parent must explicitly review the exact failed r5 result before the one-shot foreground r6 launch. PLAN_ONLY is the default; there is no waiting supervisor, installclean or automatic retry. Preserve all earlier revisions, frozen probes, existing output and partial failures. Device operations, calibration, authenticated root runtime, full services and physical commissioning remain parent-only. Do not restart composition or substitute the separate audio experiment's kernel.
