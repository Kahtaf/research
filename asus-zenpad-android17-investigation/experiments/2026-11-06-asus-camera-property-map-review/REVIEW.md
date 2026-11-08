# Independent bounded PropertyMap review — 2026-11-06

**One P1 finding: the retained ARM32 importer rewrite changes unrelated relocation targets.** The production PropertyMap adapter passes the reproduced host behavior checks; the report's complete binding-witness claim does not pass. No originals were fixed.

## P1 — preserve packed relocation identities during the importer rewrite

Location: original [`scripts/stage_importer.py:16`](../2026-11-06-asus-camera-property-map/scripts/stage_importer.py), its comparison at lines 18–25, and [`report/PROPERTY-MAP.md:89`](../2026-11-06-asus-camera-property-map/report/PROPERTY-MAP.md).

The pinned patchelf 0.18.0 invocation reorders defined `.dynsym` entries and rebuilds GNU hash/ordinary PLT relocations, but leaves the Android APS2-packed `.rel.dyn` stream unchanged. Numeric symbol indices in that packed stream consequently select different symbols. Independent decoding finds **63 changed relocation identities: 58 R_ARM_ABS32 and five R_ARM_GLOB_DAT**, out of 2,080 total relocations. These are unrelated to the nine private PropertyMap imports.

Concrete example: the zero-addend R_ARM_ABS32 at virtual address `0x1e2b0` still references dynamic symbol index 179. Before rewriting, that entry is `Vector<sp<BaseImageBufferHeap::HeapInfo>>::do_move_forward`, value `0x113ef`. Afterwards it is `Vector<int>::do_destroy`, value `0xcde5`. This changes a callback pointer in `.data.rel.ro`. At `0x1e944`, index 180 changes in the opposite direction. Unchanged section bytes cannot establish unchanged contents after relocation.

The same witness has **274 wrong symbol-to-section associations** after section-header reordering. For example, `__divsi3` and `NSCam::Utils::Property::set` now identify `.gnu.version_d` as their section instead of `.text`. The witness passes segment bounds and load-mapping checks, but does not preserve valid symbol section metadata. This is additional evidence against the same rewrite's integrity; it does not require Android execution to establish.

The original comparison sorts symbol descriptions and retains only `index == 'UND'`; it discards symbol indices, values, and defined section identity. It never decodes APS2 relocations. Accordingly, the existing `analyze.py` and `verify.py` both pass despite the corrupted witness.

**Smallest fix:** remove the `--rename-dynamic-symbols` operation for these nine equal-length, unversioned undefined names. Rename only their verified `.dynstr` bytes without reordering symbols or touching the hashed defined-symbol suffix; add DT_NEEDED as a separate operation whose output is checked. A review-only isolation experiment with the same patchelf binary and `--add-needed` alone produced **zero** changed relocation identities and **zero** wrong symbol sections. That isolates the problematic combined rename path. The proposed byte rename was not applied to the originals or packaged as an integration artifact.

Require the rewritten witness's validator to compare every relocation's address, type, addend and resolved symbol identity, decoding Android packed relocations as well as ordinary relocations; preserve symbol values, binding, visibility, versions and section identity; validate GNU hash lookups, dynamic pointers, string references, segment mapping and ordered existing dependencies. Update the report/verification result to retract the witness pass until those checks succeed. No replacement libutils/libinput is needed for this fix.

Reproduce locally:

```sh
python3 -B 2026-11-06-asus-camera-property-map-review/scripts/elf_review.py
```

This is a finding reproducer: exit zero means the expected 63 relocation and 274 section mismatches were reproduced. It prints `FAIL binding preservation` and writes the complete mismatch list to [`evidence/elf-review.json`](evidence/elf-review.json).

A fresh bounded remote run of the original pinned command reproduced the retained witness **byte-for-byte**, recorded in [`witness-reproduction.json`](evidence/witness-reproduction.json). The add-needed-only isolation is in [`needed-isolation.json`](evidence/needed-isolation.json).

Exact SHA-256 pins:

- Original importer: `be8cb386e5f5ea7045b24017870d85b67774518f6e9ae9efd3ed1c00f5dcdcec`.
- Defective retained and freshly reproduced witness: `625bfeb69cdc3118661588264e030d2ec07be96e9f3cf967a66f79eba0e743fa`.
- patchelf: `35fc95654387035338a74bb8cf62fde3712ec83dd8ca30a768deb714d07f063a`.
- Reviewed report: `f093fe7925fc0dd729be0b67d4568b4e963eef420a59ea1c853dc8ddd648d57d`.
- Rewrite script: `94c61c5838e5079ca285dd0698d9ab9fa7e834011002ef08b28f5bdf65ec981a`.

## Source-unit checks that passed

No additional production adapter defect was found in this bounded review.

The nine actual OEM method names match both frozen real-ELF inventories; the actual ARM32 binary has the same imports. The methods preserve the pinned AOSP donor bodies after the documented class-name and String8 spelling substitutions. The donor is system/core `a6116961338548409b14076eefbef211afc8c3fe`, not a claim about the unknown OEM source commit. All 154 artifact-manifest entries and all six production source pins match. [`review-input-pins.json`](evidence/review-input-pins.json) records all 155 files reviewed, including donor, backend, evidence, tests and artifacts.

The compiled old donor and adapter layouts agree at 20 bytes/alignment 4 for ARM32 and 40 bytes/alignment 8 for ARM64. The sole vector member starts at zero. String8 is one pointer; the key/value pair is two pointers; SharedBuffer prefixes are 16/24 bytes. The nine callable vector slots, construct/destroy/copy/splat/move/compare behavior and zero flags agree with the old ARM32 table and retained current-provider field-access disassembly. The OEM ARM32 constructor at `0xb64c` passes item size 8 and flags 0; destruction finishes the vector before base destruction. PropertyMap has no virtual methods of its own.

Allocation and release remain in the provider primitives. The adapter does not add storage or an allocator. String8 copies retain provider-owned buffers, vector callbacks respect the String8 move trait, and destruction releases the last owned vector/string allocations. SharedBuffer layout evidence supports compatibility; it does not identify the entire SDK37 binary with the host backend's public source commit.

Private `AsusPropMap` names are disjoint from modern PropertyMap names, equal in length, and exactly the nine exported entries. Hidden visibility, the export script and `-Bsymbolic` contain the adapter's template/vtable definitions. No original PropertyMap aliases or replacement system libutils/libinput appear. The noninstallable Soong snippet was not evaluated by a build engine.

The original full compile/link receipts show successful ARM32 and ARM64 builds with real width-matched CRT objects, genuine selected SDK37 DSOs and `--no-undefined`, not generated import stubs. This review did **not** rerun the Android cross-build. It checked the retained command flags/statuses and pinned ELF artifacts, reproduced the local analyzers, and freshly checked 14 selected frozen provider files, four CRT objects and both adapter ELFs. All 21 strong imports in each width have exactly one matching direct provider after checking symbol version and visibility. ARM32 `__aeabi_memmove@LIBC_N` matches `@@LIBC_N`; the additional `@LIBC_PRIVATE` export is not a compatible alternative. `strcmp` is an IFUNC in the captured provider; no resolver was executed. See [`provider-recheck.json`](evidence/provider-recheck.json) for exact provider/CRT hashes and version-matched resolutions.

Adapter SHA-256: ARM32 `d371807e43c770306100670d2cd2dad1e6a00262b1f2483f266cbd72ecef4405`; ARM64 `b5b8b38f304b51e4b79d8f46ef0eb082d80cc6b4cbeee10a53f099c80bb8d6e3`. Genuine libutils SHA-256: ARM32 `7441b9292d84e08e18a58eda1a0f50789818e47f2b22bd0065900d6065f95924`; ARM64 `d2f70c971b5b3b5b8a17ff899deadab16fc9d0fd68511354ce16ac489160ce3c`.

## Executed behavior and parsing limits

[`host-review-commands.json`](evidence/host-review-commands.json) records fresh Linux g++ 13.3.0 builds and execution of the unchanged production adapter with the pinned upstream String8/VectorImpl/SharedBuffer backend, frozen headers, logging transport and UBSan. Original fixture: **64,518 checks**, allocations **3,414 / 3,413 frees / one warmed process-lifetime empty String8 allocation**. This reproduces the reported canaries, growth, lifetime and ownership baseline.

[`tests/adversarial.cpp`](tests/adversarial.cpp) adds **46 checks** covering integer narrowing/overflow, retained errno, embedded-NUL values and keys, no-conversion NUL behavior, C-locale hex floats, signed zero/underflow, malformed values preserving output, shared-vector copy/assignment/self-assignment/detach, mixed-order growth and aliased key/output. Allocations are **1,075 / 1,074 frees / the same one live baseline allocation**. No UBSan error occurred.

These results preserve the donor's permissive parsing rather than establishing a stricter contract. On LP64 glibc, `2147483648` becomes INT32_MIN; `4294967296` becomes integer zero/bool false; positive long overflow becomes -1 after narrowing. ARM32 long saturation can give different results. An explicit-length value beginning with NUL is accepted as numeric zero despite consuming no characters; `12\0x` parses as 12 while string lookup retains all bytes. Keys compare through strcmp, so suffixes after NUL do not distinguish keys. Float hex forms, NaN/Inf and overflow/underflow are libc dependent. Only the C locale was executed. No multilib or Android behavior run, forced allocation failure, exhaustive locale coverage or concurrency qualification is claimed. None is required to describe the demonstrated host source-unit tests accurately.

## Binding and remaining runtime gates

The witness's nine renamed undefined entries each have the intended ordinary PLT binding, its GNU hash successfully looks up all 277 hashed symbols, version tables retain their bytes, and old DT_NEEDED entries retain their relative order after the new dependency is prepended. These successful narrow checks do not repair the 63 unrelated packed relocation changes.

The real importer imports `dlopen` and `dlsym`. Renaming undefined entries does not prove that runtime string-based lookups, other importers, or another namespace participant never request old/private names. Adding a DT_NEEDED also changes the loader's search graph. Exact primitive-provider binding, absence of competing private exports, and the single compatible String8/VectorImpl provider in the intended namespace remain unproved runtime constraints. No dlsym/preload/interposition experiment or Android load was performed.

The report correctly distinguishes direct link resolution from recursive runtime closure. **libvndksupport.so, libbase.so and ld-android.so remain absent** from the selected frozen provider graph in both widths. Their versions, further dependencies and namespace access remain open. Successful `--no-undefined` linking does not close them.

The OEM ARM64 inventory establishes nine imports, while compiled ARM64 donor/adapter layouts and current provider evidence establish a source candidate. **No actual OEM ARM64 constructor/vtable/object-storage evidence or importer rewrite is present.** No ARM64 integration conclusion follows from ARM32 evidence.

Android execution against the genuine captured providers, a corrected independently checked importer rewrite, missing recursive providers/loader and any proposed namespace configuration remain separate continuation gates. This review makes no full camera readiness, integration, target hardware, physical or flash GO claim.

## Reproduction and boundaries

Run the exact local analyzer/verifier with redirected writes, preserving originals:

```sh
python3 -B 2026-11-06-asus-camera-property-map-review/scripts/reproduce_local.py
python3 -B 2026-11-06-asus-camera-property-map-review/scripts/elf_review.py
```

The original analyzers' five generated JSON outputs equal the retained originals. They are evidence of their bounded checks, not independent validation of the rewrite. The 225 selected prior local pins, 934 recorded pre/post compile-input pins and 794 old-donor transitive pins agree as checked by the original verifier. The review freshly rehashed the explicitly selected provider/CRT files above, rather than rerunning a 934-file remote rehash or accessing mutable build trees.

Remote scripts use only `/srv/android/asus-camera-property-map-review-20261106` for writes, selected frozen inputs and existing `/usr/bin` tools. The only additional frozen host include closure was String16 and its selected utils includes; exact pins are in [`remote-headers.txt`](evidence/remote-headers.txt). The retained backend compiles against the frozen String8/VectorImpl headers, not the backend copies of those headers.

The final scratch measurement is **1,403,617 bytes**, below 32 MiB. Runs are affined to one CPU, limited to 1 GiB address space and 40 CPU seconds per process, with finite subprocess wall limits and a 110-second outer SSH bound. No packages were installed. No children, real Android execution/provider capture, active source/out/cache/R9-kit/process inspection, native engine/build, full source/image copy/rehash, device/ADB/root/USB/camera/private/calibration work, cloud lifecycle or signals occurred. Existing SSH transport was reused without copying credentials. All 155 original reviewed files remained unchanged, as recorded in [`originals-unchanged.json`](evidence/originals-unchanged.json).
