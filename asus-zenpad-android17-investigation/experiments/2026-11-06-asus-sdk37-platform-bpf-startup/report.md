# SDK37 platform BPF startup supplement

**The exact recovered patch12 is qualified for the observed Linux 4.9 startup failure and staged as offline parent input.** With every selected platform `.bpf` object present, the original genuine Rust ELF aborts on `bpfRingbufProg.bpf` with `EINVAL`/exit134. The genuine rebuilt postimage skips only that debug self-test below Linux5.8 and reaches the actual `SetProperty(bpf.progs_loaded=1)` call, which fails with exit125 because this fixture has no property service. No readiness property was injected.

The final handoff is `artifacts/supplement-qualified-r2/manifest.json`, with a compact archive beside it. The remote equivalent is `/srv/android/asus-sdk37-platform-bpf-startup-20261106/supplement-qualified-r2`. The parent integration changes are specified in `PARENT-KIT-DELTA.md` and `parent-kit-delta.json`.

## Exact input and build provenance

- Patch12: 1,353 bytes; SHA256 `2ffaf6c9349c06394d8d5e2e4e2bd70104725a2665f644dc0f1ae4f07988d502`.
- Actual `system/bpf/loader/bpfloader.rs` preimage: `1548dffa03b5091bbb9b7cfcce92495ee2167f417e90b431117cf31ea77b4bd2`.
- Fuzz0-applied and compiled postimage: `babbccf603e600a2b77f5c71cbf6b1b978f72c176fd33bfab610ff2ba8956250`.
- Actual source repository HEAD: `1787201ef62581ee5532fdb1e5b0cbc3fb137dab`. The active source still matched the preimage after testing.
- Genuine captured preimage ELF: `7ec39e0021e04868ba67717f524b840d84f8d641304c18c498a5467e2a782013`; it exactly matches the current Soong installable output. At that observation the product-installed `/system/bin/bpfloader` was absent.
- Newly compiled fixture ELF: `e0e4fd37a3c2e8bada79bed899924d34025da9f07c0809f7cc528fff7fb604d7`; unstripped ELF: `a3929c672cf1249be3f275f82c966acfd892842268b3ff10456899d53f454ca5`.

The old completed Rust build/run-r15/run-r16 evidence was preserved. Its source postimage and exact recovered patch agree with this work. The old build did not contain a complete dependency-hash snapshot, so one bounded Rust rebuild was necessary. It used the recovered actual SDK37 Ninja compiler/linker command, Rust1.93.1 and clang-r584948b, with source/output paths redirected into the owned prefix. Every mutable `out/` compiler/linker dependency was copied into the snapshot with hashes; the compiler executables/libraries were pinned and unchanged across the build. The snapshot holds approximately200MiB of build dependencies, not a SYSTEM/data copy.

The compile ran with CPU affinity0, `-Zthreads=1`, `codegen-units=1`, and linker `--threads=1`. File-access tracing found no active `out/` accesses or active-tree chdir. The complete command, response file, empty successful compiler log, exit0, toolchain/dependency hashes, ELF headers/dependencies and trace are bundled. The newly compiled ELF is separately hash-bound and tested; byte equality with the older fixture ELF is not claimed.

The exact patch only adds the file minimum-version field/default, assigns5.8 to the existing critical debug ring-buffer self-test, and checks the actual kernel-version function before loading. Other descriptors, program algorithms, critical-error handling and readiness code are unchanged. No version override was supplied. Supported-kernel5.8+ behavior was inspected in the exact diff, not runtime-tested on a second kernel.

## Actual selection and expanded fixture

Selection came from the product's `.installable_files`, the real product install edges, the SYSTEM image dependency/file-list rules, and actual module declarations. Filesystem presence alone was not used to choose objects. `evidence/selection-v2.json` and `selected-graph-edges-v2.json` are authoritative. They identify eleven platform `.bpf` files, seven Connectivity objects including the two `@funcs` variants, seven UprobeStats objects, and one vendor object.

All25 available selected object outputs were captured byte-for-byte, with ELF section/symbol/map/program metadata and source/build declarations. All eleven platform files are in the fixture. The real selected UprobeStats executable and its dependencies were also captured. The fixture executes the complete available NetBpfLoad, UprobeStats, Rust, vendor-loader and NetBpfLoad-done stages. The qualified core `netd.o` and complete NetBpfLoad executable come from immutable core handoff-r1; no core patch was revised. The actual captured clatd/dscpPolicy/offload/test objects have identical allocated and relocation sections to the earlier qualified objects; differing non-runtime object bytes are recorded.

One selected output remains unavailable, after following the full actual install chain:

```
out/target/product/p00a/system/vendor/etc/bpf/filterPowerSupplyEvents.o
out/target/product/p00a/obj/ETC/filterPowerSupplyEvents.o_filterPowerSupplyEvents.o_intermediates/filterPowerSupplyEvents.o
out/soong/.intermediates/hardware/interfaces/health/utils/libhealthloop/filterPowerSupplyEvents.o/android_vendor_common/obj/hardware/interfaces/health/utils/libhealthloop/filterPowerSupplyEvents.o
```

None of these outputs existed at capture. The vendor loader executes with an empty vendor-object directory; vendor-filter loading is therefore **not qualified**. The refined graph audit confirmed every captured object hash and availability result was unchanged, so the completed runtime jobs were reused. No available platform object remains uncaptured.

## Runtime results and remaining feature gates

Tests reuse the genuine qualified Linux4.9.337 AArch64 Image `f48955e15b0210d0b14c9d8036b6655e353a02c9e46ae5fc015b252b9bd8eac6`, config `8323724c579329c40f33aa15531320e2fdefc7e8d190703d56a555eac890ba01`, and SDK37/3701 through genuine Bionic property storage. The fixture only seeds the inherited SDK/build/legacy-policy properties; it does not seed readiness or kernel-version overrides. A fixture log socket records actual liblog messages without altering loader behavior. This is not Android init/logd/property-service integration.

- `run-preimage-r2`: real ring-buffer map creation fails `EINVAL`; the critical debug object causes Rust panic/exit134.
- `run-postimage-r2`: the exact ring-buffer minimum check is observed, the genuine chain reaches NetBpfLoad-done, and actual property-setting returns125. Sixty-eight real pins are enumerated, including map metadata and program-info syscall results.
- `run-mandatory-negative-r2`: an explicitly malformed `netd.o` is rejected with exit134 before `mainline_done`. The failure was not turned into success. This tests the real malformed-mandatory-object path, not every possible mandatory verifier failure.

Pre/post fixtures differ only in the Rust ELF and entropy seed. Each test uses one virtual CPU and host CPU affinity0, a hard host-process `RLIMIT_AS=1GiB`,384MiB guest RAM, and no external guest network. Peak host RSS was183,240/183,972/123,948KiB respectively. No kernel or config was rebuilt or changed.

All ten other platform descriptors retain their original noncritical handling. Their actual results are limitations, **not successful feature loads**:

| Selected object | Observed result on the unchanged4.9 fixture |
|---|---|
| `timeInState.bpf` | Missing kernel BTF; libbpf returns `ESRCH`. |
| `dmabufIter.bpf` | Missing kernel BTF; libbpf returns `ESRCH`. |
| `fuseMedia.bpf` | `/sys/fs/fuse/bpf_prog_type_fuse` absent. |
| `gpuMem.bpf`, `gpuWork.bpf` | Actual tracepoint-program loading returns `EINVAL`. |
| `bpfMemEvents.bpf`, `bpfMemEventsTest.bpf` | Actual ring-buffer-map creation returns `EINVAL`. |
| `kernelWakelockDuration.bpf`, `kernelWakelockDurationTest.bpf` | Actual wakeup-source tracepoint-program loading returns `EINVAL`. |
| `bpfLockContention.bpf` | libbpf object-open fails on missing extern BTF definition for `__bpf_trap`, before its existing6.1 program filters. |
| `bpfRingbufProg.bpf` | Only this debug self-test is skipped by patch12's5.8 minimum. |

UprobeStats also retains its real optional failures, including ring-buffer map creation failures in Binder/BitmapAllocation. Full raw logs, object bytes and metadata are retained. No mandatory unsupported API/hook blocked the tested available chain after patch12. This does not certify missing vendor output, optional metrics/accelerators or the full platform.

## Parent boundary and continuation

The exact new kit source, receipt, build and final-installed/image-ELF binding requirements are in `PARENT-KIT-DELTA.md`. The fixture executable must not be silently installed into the product: the parent's future authorized build must rebuild the postimage and bind its actual final ELF to source, compiler actions, dependencies, installed output and SYSTEM payload.

No new kernel config requirement is proposed. BTF/tracepoint/iterator errors above are observations, not permission to prescribe untested configuration changes. Existing cross-profile policy and permission-migration limitations remain inherited; this bounded startup supplement does not expand that work or impose a blanket certification gate on the first kernel RAM probe. Real property-service readiness, final APEX/service integration, and the missing vendor object remain separate gates. Full-OS readiness and physical GO remain false.

No physical/device/ADB/USB/root/flashing action, cloud lifecycle change, active source/output mutation, competing Ninja build or full product build was performed. The original PID78673/siso132874 jobs were live at initial inspection and absent at final inspection; this work neither changed their lifecycle nor inferred a successful build from PID absence.

Preserved attempts: the initial guest address-space limit prevented Scudo's normal8GiB virtual reservation, so no BPF conclusion is drawn from `run-preimage`; the successful tests retain the host1GiB cap without constraining guest virtual address reservations. A first install-graph parser attempt failed on a continued Ninja line. A stricter original-object whole-file comparison detected non-runtime ELF differences; section equivalence was then established before using the actual captured objects. Partial packaging attempts and all completed runtime jobs remain preserved. The final package includes corrected selection evidence and reuses the unchanged completed tests.
