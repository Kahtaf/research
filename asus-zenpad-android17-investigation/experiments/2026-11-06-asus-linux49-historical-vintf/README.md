# ASUS P00A historical 4.9 VINTF continuation

Question: Can a device-specific SDK37 experimental retrofit profile retain genuine historical AOSP 4.9 kernel predicates and modern installed HAL contracts, and what exact compiled-config gaps remain?

Status: **staged P/FCM3 candidate passes actual SDK37 checkvintf (exit 0)**. Genuine P requirements have zero config mismatches. A preserved Q diagnostic exits 65; Q has nine base gaps plus one active ARM64 conditional gap. No integration/build/device action occurred.

Important outputs:

- [Report](REPORT.md): full pinned provenance, semantic choices, exact changed constraints and remaining feature gaps.
- [Integration patch](candidate/integration.patch) and [staged device files](candidate/device/asus/p00a/vintf-legacy/Android.bp).
- [P check command](evidence/vm/05-p-checkvintf.json) and [raw compatible log](evidence/vm/05-p-checkvintf.log).
- [Q failure log](evidence/vm/10-q-checkvintf.log), [config comparison](evidence/config-comparison.json), [constraint audit](evidence/constraint-audit.json).
- [Machine report](evidence/final-report.json), [official fetched provenance](evidence/upstream-provenance.json), [VM preservation audit](evidence/vm/final-audit.json).

Continuation: parent reviews and integrates only after the current image owner's work, under the existing ownership/lock rules. No new kernel compile is required by the tested P profile. Normal native build and real runtime/feature checks remain parent-owned. The already-created VM sibling is `/srv/android/asus-linux49-historical-vintf-20261106` (~18.6 MB allocated at audit, below 256 MiB). All test metadata/config and tools are copied; do not rerun one-time setup/freeze/transfer scripts. Actual check commands, source preimages and hashes are recorded. Parent retains acceptance and physical GO. This is an experimental metadata profile, not official Android 17 certification or a hardware first-boot claim.
