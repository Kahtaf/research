# ASUS P00A: power integration for the Android 17 kernel port

Question: Can the real ASUS BQ25896 charger, pad battery policy and board routing be integrated into the MT8163 4.9 kernel without faking hardware interfaces or inheriting another tablet's charging settings?

Status: In progress. Power/board integration and host checks are implemented; clean Linux build and Android 17 integration remain. Read STATUS.md, including the case-insensitive Mac build correction. No flashing is a routine build step.

Inputs: The prior kernel bring-up and feasibility spikes; original ASUS GPL source and actual live device tree. Sources must remain pinned and changes replayable. Preserve all Google components on the stock tablet.

Outputs: implementation patches, meaningful power-boundary tests, build evidence, and remaining hardware/recovery/platform gates. A compiled kernel does not establish safe hardware behavior.

Continuation: Read STATUS.md and infrastructure/README.md. All development in this spike remains offline until a reviewed boot/recovery plan exists. Stop on evidence or resource blockers that cannot be resolved by reasonable further investigation; document attempted remedies.
