# Camera API feasibility for Android17

Question: which real compatibility path can bring this tablet's stock cameras
into the genuine SDK37 framework without misreporting HAL versions?

Status: actual stock service metadata captured; implementation feasibility open.
At 20:04 UTC the authenticated exact stock device reported two cameras, back
orientation90 and front orientation270, both device API `0x100` (HAL1). No camera
open or frame capture was requested. Only selected static metadata was retained;
the full service dump and client/history information were not saved.

The existing hardware audit shows the SDK37 CameraService rejects HAL1. A legacy
provider wrapper alone therefore does not establish compatibility. It remains
unproved whether the stock module can provide a genuine alternate HAL3 path, a
real HAL3 adapter is viable, or rebuilding a bounded legacy compatibility path
against SDK37 is the smaller functional solution. No version/feature spoofing or
replacement of current system libraries with old Android libraries is acceptable.

Inputs: `evidence/stock-camera-static.json`, plus the public stock ELF/kernel/
SDK37 evidence in `../2026-11-06-asus-hardware-completeness-audit/`. Fitted sensor
models remain unknown; the OEM configuration list is not physical identification.
Parent alone owns any actual hardware observation and private calibration.

This does not block the separate RAM kernel probe. Continue with a bounded ABI
and compatibility-source study after the basic display/input/audio/sensor work.
Actual camera streams, calibration, modern-app compatibility and physical camera
function remain unproved.
