# Implementation handoff

Completed bounded source-evidence unit. Start with `report/REPORT.md`, then `evidence/sensor-facts.json`, `evidence/exact-source-receipts.json` and `evidence/metadata-input-coverage.json`.

Reproduce locally from this spike: `python3 scripts/run.py`. It verifies the parent's four OEM source pins, extracts/audits byte-exact mode/scenario/timing bodies, compiles a serial UBSan host recorder, executes 48 OV5670 + 45 OV2680 cases and runs 12 behavioral tests. No network/package install/device access is required. Do not regenerate golden traces to make a regression pass.

Concrete findings:

- OV5670 output is 1296×972, 2592×1944 or 644×480, while grab windows are 1280×960, 2560×1920 or 640×480. Capture150 selects HTS3352; all other capture inputs select HTS1676. Crop registers 0x3800–0x3807 remain unknown.
- OV2680 capture240 still programs HTS1700/VTS1294. Its scenario-rate setter computes VTS1617 but writes nothing; the separately tested legacy video setter writes VTS1617. This does not establish the active HAL call path or delivered FPS. Crop start high bytes 0x3800/0x3802 remain unknown.
- OV5670 custom1 dispatch exists, but crop-info falls back to row0 and its default-rate query leaves the fixture sentinel untouched. Declared row5 is currently numerically identical to row0; that does not repair dispatch completeness.
- Declared pclk/(recorded HTS×VTS), exact rational period and nominal max_framerate tenths are separate facts. No source clock is measured or independently PLL-qualified.

All source pin/write drift fails checks; declaration/register differences and unresolved mappings remain explicit. Development failures are retained in `evidence/development-failures.md` and individual receipts. Darwin rejected hard memory limits; observed compiler peak RSS (~82MB/~65MB), serial frontend/classic-linker execution and the 1GiB post-run gate are recorded without claiming a hard cap.

Next implementation boundary: a new independent local public-source spike tracing selected MT8163 frame-duration/shutter/dummy application and crop/grab-window-to-ISP coordinate transforms. Consume this ledger; preserve unknown initialization bytes and distinguish software state from actual register writes. Future metadata authorship additionally needs separately proven ISP stream/combination/3A/result/JPEG/lens contracts. No HAL3 contract, supported-stream/FPS advertisement, constructor borrowing, version/capability/property change, physical GO or camera enablement is authorized or implied here. The Android11 HAL1 donor remains unsuitable and its adapter stays shelved.
