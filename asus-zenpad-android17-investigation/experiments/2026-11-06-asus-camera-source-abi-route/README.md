# ASUS P00A_2 camera source / ABI route

Question: what is the shortest honest route from this tablet's actual fitted
stock HAL1 cameras to SDK37, and what source/ABI work does it require?

**Status: research complete; camera implementation and physical qualification
remain open.** Both stock cameras actually reported HAL1. Static ELF tracing
found a real selectable OEM HAL3.2 factory/ops path worth qualifying first, but
fitted-sensor metadata, C++/ELF and kernel ABI blockers remain. A compiled sensor
FeatureId mismatch proves that simply enabling the drivers is insufficient.

## Important outputs

- [Camera route and exact integration alternatives](report/CAMERA-ROUTE.md)
- [Concrete ABI ledger and next source changes](report/ABI-LEDGER.md)
- [Source/export evidence](evidence/), including current SDK37 pins and public OEM disassembly
- [Pinned genuine AOSP Android9 compatibility donors](donors/pins.json)
- [SDK37 C ABI compile witness](fixture/camera_abi_probe.c) and its linked ARM64 `.so`
- [OEM/4.9 sensor command mapping](evidence/sensor-feature-enums.json), with two compiled enum witnesses
- [Offline verification result](evidence/verification.json): 133 consistency checks passed

The `.so` is an offline interface/link witness, **not a camera HAL**. It has no
camera-loading or hardware entry point. There are no successful stub camera
results. The upstream HAL1 restoration and proposed native HAL3 adapter were not
implemented or compiled. No camera or physical readiness is implied.

## Limits and ownership

No device/ADB/root/USB/camera/flash/reboot/integration actions, media/history,
private calibration/key/preservation payload access, cloud lifecycle operations,
active AOSP/kernel/out edits, Ninja, or full product build occurred. No SYSTEM/data
image was copied or rehashed. The original r5 build and sealed kit/staging/probe
artifacts were not managed. Parent alone owns physical tests and integration.
Expected user arrival time was never taken as evidence of presence or approval.

Remote scratch is isolated at `/srv/android/asus-camera-source-abi-route`.
Remote analysis/compilation sets one CPU affinity and a 1 GiB address-space limit;
compilation is serial. Selected public ELF inspection used existing audit files
or read-only debugfs on the existing public stock SYSTEM. The vendor closure
read 64 specific ELFs totaling 22,886,792 bytes; follow-up read six specific public
system ELFs totaling 1,484,632 bytes. Temporary extra ELF data was removed. Some
small selected ELF inputs and frozen SDK37 libraries remain in the owned remote
fixture for reproduction; no full image was extracted. No target ELF was executed.

## Reproduce static checks

From this directory:

```sh
python3 scripts/verify_evidence.py
```

All SSH uses `../2026-11-06-asus-product-input-build-kit/scripts/remote.py`, static
builder `IP_REDACTED`, existing key path only. No key contents are read by our
scripts. From this directory, bounded collection examples are:

```sh
python3 scripts/run_remote.py scripts/discover.py evidence/discovery.txt
python3 scripts/run_remote.py scripts/oem_elf.py evidence/oem-elf.txt
python3 scripts/run_remote.py scripts/oem_dispatch.py evidence/oem-dispatch.txt
python3 scripts/run_remote.py scripts/dependency_audit.py evidence/dependency-audit.json
python3 scripts/run_remote.py scripts/final_edges.py evidence/final-edges.txt
```

Full source collection uses `sdk_sources.py` and `source_edges.py`; each returns
JSON source contents and SHA256. `scripts/unpack_sources.py INPUT_JSON OUTPUT_PINS`
materializes them under `fixture/sdk37`. `fetch_donors.py` fetches the exact tag and
pins its resolved commits from the official source host (the saved pins should
be checked before any new donor import). `metadata_edges.py` records the extra
4.9 default sensor header; `analyze_headers.py` verifies the source-derived enum
mapping. These scripts inspect existing inputs; they do not manage the build.

The SDK37 ABI compile can be reproduced with `python3 scripts/run_compile.py`.
It uses the already-recorded audio fixture flags as its seed, performs a dependency
scan, freezes all transitive headers, then compiles/links in this spike's remote
fixture. Exact resolved commands and source/library hashes are also saved in
`evidence/{compile,input-pins}.json`. `compile_enums.py` reuses those frozen flags
to compile the two source-derived enum assertions and retrieves only small outputs.
Recollection from the active source tree is a *new snapshot* and must be compared
to the recorded pins; it does not silently replace the qualification baseline.

## Continue

Read both reports first. Next bounded work is an isolated OEM camera ABI fixture:
finish dynamic/system proprietary closure and C++ buffer ownership contracts,
then implement an explicit OEM sensor-command translation boundary in a separate
kernel fixture. Identify fitted sensors through parent-owned authorized evidence.
Qualify real OEM HAL3 metadata/pipeline support before choosing a larger adapter
or source-restoration effort. API1-only restoration is explicitly partial.
Keep the first RAM kernel probe independent of camera completion.
