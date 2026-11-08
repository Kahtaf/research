# Selected OV5670/OV2680 OEM metadata dispatch

Question: Can existing stock OEM common/dynamic paths provide a truthful HAL3 static/default-request contract for the actual selected sensors?

Status: COMPLETE bounded research and fixtures. Result: no complete contract supplied by the inspected stock paths; hardware feasibility remains open. No device, live vendor execution, product integration or active-build changes.

Important outputs:
- `report/REPORT.md`: exact dispatch, dynamic sources, failure propagation and implementation boundary.
- `HANDOFF.md`: continuation and local reproduction.
- `evidence/mapping.json`: qualified sensor/lookup/required-entry/blocker mapping.
- `evidence/fixture-results.json`, `fixture64-results.json`: 175 executed instruction-fixture cases.
- `evidence/complete-closure-constructors.json`: pinned stock ELF inventory.
- `evidence/schema-witness.json`: SDK37 compile-only enum witness.
- `inputs/`: copied public ELF/source inputs; `scripts/`: reproducible bounded analysis.

Continuation: read HANDOFF and report. Keep this source-contract gap separate from graphics/ioctl/closure/pipeline qualification. Parent owns devices and integration. Existing spikes remain immutable inputs; no matching public donor has been asserted.
