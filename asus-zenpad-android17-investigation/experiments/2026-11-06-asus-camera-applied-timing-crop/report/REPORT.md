# Applied sensor timing and crop boundary

Completed as a bounded local public-source implementation unit: **three additional unchanged complete production bodies**, eight reused timing bodies, and exact selected feature/crop/grab switch fragments. Both fitted sensors pass **134 timing sequences, 646 stage observations and 14 crop/grab cases** (660 stage/crop comparisons). The prior 34-function / 93-case / 12-test mode ledger is accepted and pinned; no mode program is executed or retested here.

Only this new spike was written. No device, ADB, root, sensor read, probe/open/OTP, I2C/hardware transport, private calibration, key, network, SSH, VM/cloud, active AOSP/kernel/product/probe mutation, camera activation, metadata/version/readiness spoofing or physical GO. Main `ov5670mipiraw`, sub `ov2680mipiraw`; no OV2680B. No Echo Show HAL1 donor or ION/VA assumptions are used.

## Reproduce and inspect

Run `python3 scripts/run.py` from this spike, using installed Python/clang only. The runner pins all four source filenames directly from the accepted manifest and rejects changed accepted parent evidence, extracts byte-exact bodies, builds/runs sequentially, checks UBSan and imports, compares each stage with a separate integer model and fixed behavioral expectations, and rechecks pins. `inputs/public-transport-pins.json` additionally fixes the seven text-only transport/support sources. Original notices and kernel COPYING are retained.

`evidence/extraction.json` holds exact source paths, full-file pins, function/type/scalar/fragment hashes and inclusive lines. `generated/*-production.inc` contains unchanged bodies and fragments with original `#line` locations; wrappers and `tests/host.h` are explicitly synthetic. `evidence/applied-timing-crop.json` is the machine-readable applied state/register/crop ledger (about 7 MB; select fields rather than dumping it). Each byte has inherited or current source-write provenance; unknown bytes are null. `*-cases.json`, `*-traces.json`, compile/link/run/binary-audit receipts and `verification.json` support every case. `parent-inputs.json` and `inputs/parent-evidence-pins.json` pin consumption of the accepted report, facts, coverage and acceptance.

## What is applied

For a 100-line requested shutter with scenario-rate 240 tenths:

| Sensor / accepted capture seed | Software frame length after scenario-rate setter | VTS pair before shutter | VTS pair after shutter | New writes from scenario setter / shutter |
|---|---:|---:|---:|---:|
| OV5670, current_fps=240 | 2556 | 2045 | 2556 | 0 / 5 |
| OV2680, current_fps=240 | 1617 | 1294 | 1617 | 0 / 5 |

`SET_MAX_FRAME_RATE_BY_SCENARIO` changes frame/min-frame state and uint16 dummy lines. Its `set_dummy()` calls are commented out. `SET_ESHUTTER` narrows a 64-bit feature word to uint16, then applies VTS before the three shutter bytes. OV5670 uses `set_shutter` → `write_shutter`; OV2680 writes in `set_shutter` itself. Non-flicker exposure writes are ordered VTS high/low then shutter low/mid/high. No atomic group-hold or frame-latch timing is established by those writes.

Both use margin=4 and max_frame_length=32767. OV5670 min_shutter=4; after clamping it rounds shutter and VTS down to even values. A normal 2045-line minimum thus becomes VTS=2044 on shutter application while min_frame_length remains 2045. Requested zero remains zero in `imgsensor.shutter` but records coarse shutter=4; uint16 65535 records VTS=32766 and shutter=32762. OV2680 min_shutter=1, zero is locally promoted to one, no even rounding: max request records VTS=32767 and shutter=32763. Software shutter retains the input before the clamp on both sensors. The ledger decodes only the bit placement present in source writes; this is not a measured exposure.

`GET_PERIOD` reads software line/frame state into uint16 payload slots. It can report 2556/1617 before those values reach the VTS registers. `SET_FRAMERATE` narrows to uint16 and updates current_fps only. The legacy video-rate path invokes `set_max_framerate` → `set_dummy` and writes VTS and HTS; this does not show a real HAL invokes the path (OV2680 calls it “not used after ROME”).

Arithmetic is preserved in its original order: scenario timing is uint32 `pclk / rate * 10 / linelength`; the dummy difference then narrows to uint16 before addition to the base. At requested rate=1 tenths the OV2680 software minimum becomes 60555 through that narrowing, beyond the 32767 application maximum. A following legacy rate application clamps frame_length to 32767 and its uint32 negative difference narrows to dummy_line=37748. No cleanup of these production effects is applied. Separate explicitly synthetic fixtures exercise uint32 wrap and min_frame_length below margin; they are not plausible fitted sensor configurations or hardware claims.

Flicker uses uint16 realtime_fps from `pclk / line_length * 10 / frame_length`. Inclusive ranges 297–305 and 147–150 call `set_max_framerate(296,0)` or `(146,0)`, writing HTS as well as VTS before shutter (seven writes total). Synthetic threshold fixtures test both inclusive endpoints and immediate outside values. Non-flicker paths use five writes. Tests include 0/minimum/odd/margin/maximum shutters, 64→16 and 64→32 conversions, uint16 dummy-line narrowing, clamp behavior and current_fps capture selection. Unguarded zero-rate division, invalid pointers and undersized external payloads are never executed.

## Request and ABI boundary

Text-only receipts trace kernel ioctl dispatch → `adopt_CAMERA_HW_FeatureControl` → `kd_MultiSensorFeatureControl` → selected `feature_control`. The selected handler consumes 64-bit feature words; `SET_ESHUTTER` ultimately takes uint16 lines, scenario rate takes a uint32 tenths rate, and current_fps takes uint16. `SET_SHUTTER_FRAME_TIME`, `SET_TARGET_FRAME_RATE` and `SET_MIN_MAX_FPS` are not handled by either selected feature switch. An enum token and default ERROR_NONE return establish no implementation. No Android nanosecond request conversion or active caller is supplied by this release.

Two exact ABI gaps remain. The kernel `SET_SENSOR_SYNC` immediate shutter path (`kd_sensorlist.c:2013–2018`) passes length=2 and the address of `u2SensorNewExpTime`, whereas the selected sensor handler dereferences an eight-byte feature word. Its extent/packing must be reconciled; this witness uses valid two-word host payloads and never executes that path. `GET_CROP_INFO` casts word1 directly to a destination pointer. The inspected generic ioctl copies only flat payload bytes and its compat helper translates envelope pointers, without a crop-specific nested destination conversion. Host fragment execution proves table selection, not safe external ioctl marshalling. No transport is compiled or run.

## Crop and grab evidence

The exact inner GET_CROP_INFO switch is executed against an actual 16×uint16 winsize type and declaration, in a synthetic wrapper with a valid host destination. The exact get_info scenario switch is separately executed for grab starts; full get_info and get_resolution are text-only receipts. Every pre/capture/video/high-speed/slim mapping plus custom1/default is checked against the accepted declarations. OV5670 custom1 get_info selects custom1, while crop dispatch falls through to row0; row5 currently has identical numbers. OV2680 GET_CROP_INFO falls through to SET_HDR_SHUTTER logging in its full feature switch; no transform or write results there. The inner-switch fixture makes no full-feature-flow claim.

The ledger preserves these independent stages: raw sensor register crop/output → winsize `full_*`, `x0/y0/w0/h0`, `scale_*`, `x1/y1/w1/h1`, `x2_tg/y2_tg/w2_tg/h2_tg` → OEM grab start/size → unknown ISP transform → unknown Android coordinates. These field names and values are provenance, not proof of a mathematical transform. No scale ratios, crop-high bytes or reset values are invented. Accepted mode programs do not establish 0x3800/0x3802; these remain null after all tested timing writes. OV5670 lacks all crop-start/end bytes in these accepted programs; OV2680 partial crop bytes remain partial.

Kernel `get_info` exports scenario grab starts and `adopt_CAMERA_HW_GetInfo2` copies them to PRV/CAP/VD/VD1/VD2 fields. `get_resolution` supplies grab dimensions. Independently, public ISP `ISP_WRITE_REGISTER` → `ISP_WriteReg` accepts a caller-supplied register list, holds it or calls `ISP_WriteRegToHw`; the latter applies Addr/Val pairs within its address checks. These bodies do not compute a winsize/grab-to-ISP mapping. The mt8163 Makefile includes camera_isp.o, but build inclusion is not evidence of a fitted live pipeline.

Local public release search inventories 48 hardware files and 9547 vendor files: no camera/sensor-HAL/ISP-builder path match and no GET_CROP_INFO/SensorGrabStartX/SET_MAX_FRAME_RATE_BY_SCENARIO C/C++ reference. Exact search scope and expressions are retained in `public-path-boundaries.json`; this is an absence claim for inspected local public userspace, not all possible vendor sources. The last sensor outputs and next ISP entry ABI are concrete; the intervening proprietary function name is unavailable and is not fabricated.

## Exact body receipts

Full-file source hashes and exact filenames are the accepted four pins in `inputs/parent-evidence-pins.json` / `evidence/extraction.json`. OV5670 C SHA256 `aad8723995f1e02d3202bd9b0d085eaeca98cd93829379c8550d69fd29cfd7fc`; OV2680 C SHA256 `e0d768a30788e0027df9160c95024f9e4d418438915efb68f7c3263d896eabff`. Header pins are `b5ee4568eae2903d72cb99d13ddbfa57f9c100e7cebb0338f72219bad6cdba4a` and `a40bfc5dfb8bf387bf9ffb91096a36cf80d45cbd2876df86074df93eeca88398` respectively. Inclusive lines below identify original OEM files, not wrapper files.

| Sensor | Complete unchanged body | Lines | SHA256 |
|---|---|---|---|
| ov5670 | `set_dummy` | 282–291 | `42b7232327d9da875763691ee25a8b34daf992aec188b82c813d08de06f8590c` |
| ov5670 | `set_max_framerate` | 294–320 | `cf47896f63e2dc2c597ae19a52eef2eb24f724d49f05be073a5ed61e37d0afcb` |
| ov5670 | `set_max_framerate_by_scenario` | 1876–1953 | `2e273af69a4844b1d839de9b9ca72d48041cd71fd51e11d2c14d5d04002debeb` |
| ov5670 | `set_video_mode` | 1843–1861 | `1324fb0126b2f7257cf13e2b46833b70f5452ab32b57902b9c36ae6bafb9b175` |
| ov5670 | `write_shutter` | 323–375 | `9856c058143b67d931663953ec240558e0b64dbd83421b7d976e52f30548409b` |
| ov5670 | `set_shutter` | 395–403 | `9f3a0cc6bd8cc08993d14c2b1aa9ac46d8b2d82fded3a8627ee2d0f1f4c5aace` |
| ov2680 | `set_dummy` | 205–220 | `c9484f6a55bc70e84a575885f67a4a547457a199817199c05b748ecc322569f1` |
| ov2680 | `set_max_framerate` | 226–253 | `5e35f95b4eae2691b57ad51f6299005b5b32ec9f60daf21f5806c86e5bb60ab0` |
| ov2680 | `set_max_framerate_by_scenario` | 1209–1286 | `6ab944b0be34a5d1428bbd8bd6323a7950dc691d2b74c10f694d0540ed0c94cd` |
| ov2680 | `set_video_mode` | 1177–1195 | `2d7f4cd15e2e3fbdc9671091954e4d7f89009959e57e705b5b589655c3abbfc0` |
| ov2680 | `set_shutter` | 273–327 | `3a2352bd4897a0823f1a2d49406920f044da32b1efa82b8fb41e99c53f8d224b` |

Three bodies are additional to the accepted parent: OV5670 write_shutter/set_shutter and OV2680 set_shutter. All other complete functions are reused dependencies; feature/crop/grab fragments have their own exact hashes/lines in extraction.json and are not counted as complete functions.

| Text-only public function | Lines | SHA256 |
|---|---|---|
| `adopt_CAMERA_HW_FeatureControl` | 1886–2203 | `4154d03b5aa088f652581bd8628f399074252fedf6a67c3d456ebf1076f2f799` |
| `kd_MultiSensorFeatureControl` | 867–921 | `0c895041b1bf10895ef79ca8de73638d034e6269e31c4f6b1306aa58bdd6264b` |
| `kd_MultiSensorGetInfo` | 785–831 | `75854f8cd4153f9fe9f2f8237415b3f5e6cdbb5109743fd18be4138c1e8cd93d` |
| `adopt_CAMERA_HW_GetInfo` | 1529–1581 | `3f738f5a8929130bebaa94844dd0fe7654e6484532b21204fde35f900f681f38` |
| `adopt_CAMERA_HW_GetInfo2` | 1592–1816 | `886372274033dc9ab45bdac300405dfe354d910e5a88537df34315c280cb8605` |
| `compat_get_acdk_sensor_featurecontrol_struct` | 2800–2817 | `b7eff0a2119cada64eea168627e51de18e79d7966b43946e30c8c89f15ada463` |
| `ISP_WriteReg` | 2440–2500 | `a726ed98b4f91e005da2fffcdec30741d5d8e784831db70c9f96bf079c8e9e5b` |
| `ISP_WriteRegToHw` | 1996–2023 | `833864449797ddddbc0260579d5074b4221943b2711bfc03b8e98ab721df85f7` |
| `ov5670-get_info` | 1697–1804 | `9cc3292634016211f666c74eb85a1f533f0a4e4b23a7adf37475262b2ff62b34` |
| `ov5670-get_resolution` | 1672–1695 | `7e30ea5bf323bb994b78fab169e1d461f7c9c8a3ede7ce44b1eb29c8811c546e` |
| `ov2680-get_info` | 1040–1141 | `7b88bf146c9cd031e518f87aff68db2dc8c8209c29684138327b7335ca5dc1e9` |
| `ov2680-get_resolution` | 1019–1038 | `b14e3ed58f22866182b70aa87da717e52b7d4e9e2b3fb92a86afb2a529968aba` |

Full source paths/hashes for those receipts are in `inputs/public-transport-pins.json` and `public-path-boundaries.json`. None is executable host code.

## Resource and failure evidence

Clang runs serially with one frontend, no LTO, classic serial Apple linker, warnings-as-errors and UBSan without recovery. Binary imports are limited to printf/puts/memory/abort, compiler stack protection and UBSan; dynamic libraries are host runtime/UBSan only. All new write sites call the explicit in-memory recorder callback. No full driver, mode/probe/open/read/OTP or hardware transport body is in a host compilation unit. Replaying accepted register bytes into the analysis map does not execute prior mode bodies.

Each compile/link/run and the whole Python runner are measured with time -l on Darwin; observed peak must remain <=1 GiB. This host rejects practical AS/RSS memory rlimits as accepted parent evidence records, so no Darwin hard cap is claimed. Supported non-Darwin children receive a hard 1 GiB AS limit. CPU 30s and zero core limits apply. `resource-summary.json` and `full-run.json` hold actual measurements; the latter is written by the outer runner after report generation.

Preserved failures include the initial import whitelist missing host stack-protector symbols, the OV2680 fixture's unused alias warning, and the initial query-observation bookkeeping assertion. `initial-binary-audit-failure.json`, failed compiler receipt, `failure-*.json` and `failed-query-fixture/` retain evidence. Fixes changed fixture/audit glue only, never production bytes.

## Smallest next boundary and blockers

`evidence/missing-source-abi-contract.json` is the concrete handoff. Obtain locally reviewable public source or an exact documented ABI for (1) the fitted userspace request/3A-to-feature caller, including exposure/frame-duration conversion and scheduling, and (2) the winsize/grab-to-ISP register-list builder, including coordinate origins, Bayer alignment, clipping/rounding and frame latching. Resolve feature payload extent and nested-pointer marshalling before any external call. Then implement that adapter as a pinned host-only witness. Without those inputs, further transform implementation would be invented behavior.

Real ISP/MIPI/buffer format and ION/VA ownership, 3A/gain/ISO/timestamps/results, JPEG, lens/calibration, identity/orientation and sustained stream combinations remain separate blockers. Sensor source facts and clock/register ratios are not hardware-measured FPS. Static metadata, templates, available keys/capabilities, HAL3/version/readiness and Android stream/active-array contracts remain unsupported. No camera enablement or physical GO follows.
