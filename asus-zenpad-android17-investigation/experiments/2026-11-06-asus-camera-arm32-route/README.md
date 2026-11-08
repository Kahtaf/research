# ASUS camera ARM32 route comparison

Question: does the actual OEM ARM32 camera path offer a shorter genuine HAL3
route to SDK37 than the previously studied ARM64 path?

Status: offline investigation complete. ARM32 is the configured stock service
width, but does not establish a shorter genuine HAL3 route. Both widths export
the same 21 metadata constructors, with no newly matching OEM sensor names.
ARM32 callers allocate 136 bytes for GraphicBuffer; genuine SDK37 headers compile
to 1,784 bytes. A constructor alias is unsafe. The expanded ARM32 closure covers
82 public OEM ELFs and 25 SDK37 providers, with 19 unresolved names and additional
runtime/namespace/layout gates. Actual camera operation and fitted sensors remain
unproved. The stock HAL1 result remains authoritative.

Important outputs:

- [Route comparison and exact implementation delta](report/ARM32-ROUTE.md).
- [Machine-readable summary](evidence/summary.json) and [verification receipt](evidence/verification.json).
- [C ABI compile/link witness](fixture/camera_abi_probe.c), [C++ layout witness](fixture/cpp-out/layout.cpp), and [32-bit ioctl layout compilation](evidence/compat-layout.txt).
- `evidence/` contains public-source/ELF receipts and exact pins; `scripts/`
  contains bounded reproduction. Remote scratch is exclusively
  `/srv/android/asus-camera-arm32-route`.

Continuation: retain the earlier ARM64 research baseline, without treating it as
a proved working architecture. First qualify the legacy object facade and true
sensor metadata contracts; choose width after those shared blockers are resolved.
Use the report's explicit provider packaging and native/compat ioctl requirements.
Parent owns all
device actions, camera activation, integration and physical tests. No private
payloads, camera/media/history access, device commands, active source/out edits,
cloud lifecycle, Ninja or product builds are allowed here. Read-only public
SYSTEM extraction is limited to specific files. Remote work is serial, one CPU,
1 GiB address space, through the authorized existing SSH wrapper.
