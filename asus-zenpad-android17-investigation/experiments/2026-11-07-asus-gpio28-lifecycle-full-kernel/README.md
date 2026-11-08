# Complete ARM64 GPIO28 lifecycle kernel

Question: does the completed, independently reviewed GPIO28 lifecycle repair compile into a complete ARM64 kernel on the pinned physical BMC156 baseline?

Status: COMPLETE. All four compile stages exited 0 in 30 minutes 9 seconds; actual output checks and local artifact hashes passed. Compile proof only; HAL routes remain qualified=false. No hardware or product integration is authorized by this spike. The first physical trial and e9 BMC SD probes remain unchanged.

Owned VM prefix: `/srv/android/asus-gpio28-lifecycle-full-kernel-20261107-r1`. Baseline `/srv/android/asus-bmc156-full-kernel-r1` is read-only. Only the fixed SSH transport in the existing product-input kit is used. No excluded PCM-copy patch is accessed.

Outputs: `patches/` has the two reviewed source stages and config selection; `evidence/` has small pre/post pins and actual compile receipts; `artifacts/` holds the completed Image.gz-dtb (SHA256 ea567598778060428b55104bbbd2bddca5e36958a8e9b8a5ac93c0dce92dd52b), actual resolved config and compiled DTB. `report/HANDOFF.md` records commands, identities, limits and the corrected generic-symbol name check. Full source and objects remain on the VM.

Continuation: read `report/HANDOFF.md` and `evidence/build-status.json` before any action. Do not relaunch against an existing prefix or assume SSH interruption stopped a build. Do not install this candidate, replace product inputs or operate hardware based on compilation alone.
