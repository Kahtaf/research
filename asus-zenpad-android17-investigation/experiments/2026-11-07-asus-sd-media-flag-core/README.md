# Corrected SD media flag common core

Question: can the existing selectable offline core use the pinned e9 Linux4.9 MMC sysfs removable=0 while preserving every fixed SD binding and normal/stock safeguard?

Status: implemented and built. All four static AArch64 programs and common rootfs are delivered; policy/contexts are byte-identical. Actual compilation/linking and two focused SD binding cases passed. No final candidate or physical/flash GO; genuine final SYSTEM/BOOT admissions remain pending.

Important outputs:

- [HANDOFF.md](HANDOFF.md): exact hashes, local final_package command, preserved behavior and parent continuation.
- [artifacts/ARTIFACTS.json](artifacts/ARTIFACTS.json): seven real compact products and hashes.
- [evidence/DELIVERY_PINS.json](evidence/DELIVERY_PINS.json): actual corrected core pins.
- [evidence/source.patch](evidence/source.patch): sole runtime source change, removable exact1→exact0 plus explaining comment.
- [evidence/admission.patch](evidence/admission.patch): unapplied two-line CORE/DELIVERY_SHA update for the old deployment adapter.
- [scripts/final_package.py](scripts/final_package.py): byte-identical sibling-relative packager, now bound to corrected real core pins.
- [evidence/build-log.json](evidence/build-log.json), [evidence/local-check.json](evidence/local-check.json): minimal actual build/check records.

Continuation: parent integrates the two adapter assignments, then runs HANDOFF.md's local packaging command only after genuine final SYSTEM/BOOT, five-role manifest (final DATA cf433efa509f09814bff0877368f0c1b811b7615eefd3cd2a02f58b57995131b), real parent arm and physical e9 kernel inputs exist. Output directory must be new. Normal custom recovery retention and stock OEM_RESET_REQUIRED remain. No fabricated authorities/bindings or private data access. Preserve all earlier spikes.

Owned VM fixture: /srv/android/asus-sd-media-flag-core-20261107. Fixed SSH helper, one CPU, serial compilation, 95MiB address-space cap, 8482816-byte owned allocation. No subagents or independent Android build/process/device/card/cloud operations. Separate probe untouched.
