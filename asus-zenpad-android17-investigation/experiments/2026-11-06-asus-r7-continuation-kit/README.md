# ASUS P00A full-product r7 continuation

Question: can the already-integrated, reviewed r3 Android17 product resume as r7 with only the reviewed sensor BoardConfig path correction?

Status: sealed continuation prepared. Active AOSP/kernel/out remain unchanged by this work. Real product dumpvars, native compilation, and full image validation remain parent execute gates. No approval or build attempt was created.

Important outputs:

- `HANDOFF.md`: smallest review surfaces and exact parent describe/plan/execute commands.
- `scripts/continuation.py`: actual r6 failure acceptance, preserved-source checks, preservation receipt, and sole source write.
- `scripts/verify_config_paths.py`: actual dumpvars policy/manifest path gate before native compilation.
- `source/changes-from-r3.patch`: complete launcher/validator adaptation diff; `source/sensor-board-path.patch`: sole active source delta.
- `inputs/kit-pins.json`: 101 pinned kit inputs, scripts and tests; SHA256 `9287a07d243a9d70abefa0102de160d88af712a574c7fab6032ce9b36920f617`.
- `inputs/r7-staging-manifest.json`: exact 414-file VM staging copy, with only the source fix and its two receipts changed from r3.
- `evidence/linux-tests-and-source-audit.json`, `evidence/final-readonly-state.json`: bounded behavioral tests, real complete-source audit and preserved terminal/source observations.
- `artifacts/r7-continuation-compact.tar.gz`: compact delivery. Full staging and all eventual images stay on the VM.

Continuation: read HANDOFF.md, then let the parent author its own exact r6 failure acceptance. Use only `/srv/android/asus-reviewed-build-kit/r7/scripts/integrate.py`; PLAN_ONLY is the default. Preserve r3, all prior attempt/marker/log files and the incremental cache. Never rerun preparation/composition, apply the baseline kernel patch, reuse r6/r7, installclean, delete attempt markers or retry automatically. Hardware charging remains inhibited; authenticated userdebug root and normal Google remain selected. Audio PCM repair remains excluded and unaccepted. No device action, physical GO or flash-readiness is granted.
