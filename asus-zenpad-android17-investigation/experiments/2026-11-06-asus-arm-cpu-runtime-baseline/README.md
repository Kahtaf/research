# Physical ARM CPU runtime baseline

Question: which CPU capabilities does the physical ASUS advertise to stock userspace, for comparison with future genuine crypto/runtime tests?

Status: parent read-only observation. Only CPU feature/implementer/part fields and AT_HWCAP/AT_HWCAP2/page-size values are retained; raw auxv and pointer values are discarded. Stock Android 7 is the observer environment, not proof of the future 4.9 kernel or SDK37 runtime.

Outputs: evidence/physical-cpu-baseline.json. Continuation: compare these with the actual CPU/kernel used for official BoringSSL/runtime validation. Preserve crypto detection and real self-tests. No performance, cipher correctness, kernel boot or physical GO follows.

ARM32 observation: the 1,076-byte static assembly helper in source/cap32.S ran as the existing non-root shell. It reads only its initial auxv and calls write(stdout)/exit; no pointers or raw auxv are emitted. Actual ELF32 EXEC ARM headers have no interpreter/dynamic segment or writable-executable load. Device receipt evidence/compat32-device-17b5e2be18c88792.json reports HWCAP0x37b0d6/HWCAP2=0x1f/pages4096. Its unique shell-owned temporary directory and executable were checked and removed; Enforcing stayed enabled. No partition write or reboot occurred. This does not qualify new4.9/BoringSSL or normal Android17 applications.

Compilation was a direct isolated assembly/link action on the existing builder (source/out untouched), using an existing Android clang/lld with 1CPU/1GiB/30CPU-second/45wall-second limits. Source, compiler/linker hashes, static ELF headers, invocation and the harmless unused-no-pie warning are retained in evidence/compat32-build.json. No native AOSP or kernel build ran. Large compiler binaries stayed on the VM.
