# Camera-private legacy PropertyMap boundary

Question: can the real ASUS MT8163 camera PropertyMap String8/KeyedVector ABI be provided privately using frozen SDK37 providers?

Status: offline source boundary implemented and qualified for review. Unmodified old donor and private adapter have matching 20/40-byte layouts; ARM32 and ARM64 adapters link against genuine captured SDK37 providers with `--no-undefined`. Production adapter host behavior, ownership, and canary tests pass. A real ARM32 importer rewrite witness proves all nine names can bind privately. No Android target execution or camera compatibility is claimed. Runtime closure and OEM ARM64 object evidence remain open.

Important outputs:

- [Full report and fresh-review handoff](report/PROPERTY-MAP.md).
- [Production adapter](src/legacy_property_map.cpp), [private header](src/legacy_property_map.h), [noninstallable build snippet](src/Android.bp.snippet), and [binding contract](src/BINDING.md).
- [Verification](evidence/verification.json), [provider frontier](evidence/provider-closure.json), [actual commands](evidence/reproduce-commands.sh), [behavior receipt](evidence/host-final.txt), and [original/new pins](evidence/source-pins.json).
- `donor/` contains pinned old primary AOSP source and NOTICE; `backend/` contains pinned primary source for host tests. `artifacts/` contains compiler/linker/layout output and the offline ARM32 binding witness. `report/boundary.html` visualizes the bounded result.

Continuation: use the report's fresh-review gates. Obtain missing frozen providers/loader and OEM ARM64 constructor/storage evidence before any runtime/width decision. Execute the pure behavior fixture against genuine Android providers in a separately authorized environment before integration. Remote scratch is exclusively `/srv/android/asus-camera-property-map-20261106`; all local writes are confined to this new spike. No children, device/private-data work, active source/output changes, full build, cloud lifecycle, process signals, mutable R9 inspection, integration/approval flags, or physical GO.
