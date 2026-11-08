# Camera-private legacy PropertyMap: source boundary qualified offline

A minimal private adapter is staged in [src/](../src/legacy_property_map.cpp). Its nine methods preserve the matching old AOSP String8/KeyedVector representation and behavior. It compiles and links for **ARM32 and ARM64** against the captured genuine SDK37 libutils providers with `--no-undefined`. The original donor also compiles unchanged for both widths and produces the same 20/40-byte object layout and vector virtual slot order.

This is **not a runtime loadability or camera compatibility pass**. Behavior executed on Linux x86_64 using the production adapter and pinned upstream String8/VectorImpl/SharedBuffer source. Neither Android binary was executed. The frozen runtime graph lacks three providers; only the ARM32 importer has an offline rewrite witness. No active integration, approval flags, physical GO, metadata, device, frame, camera, calibration, or other subsystem work occurred.

## Inputs and source identity

The two original spikes are preserved. [local-inputs-pre.json](../evidence/local-inputs-pre.json) and [local-inputs-post.json](../evidence/local-inputs-post.json) contain the complete selected local before/after hashes; [verification.json](../evidence/verification.json) checks them. The remote compile input maps [input-pins.json](../evidence/input-pins.json) and [input-pins-post.json](../evidence/input-pins-post.json) agree on all **934** selected inputs. These include the actual transitive headers, CRT objects, and directly linked providers. The additional **794** old-donor transitive input pins are in [supplement-input-pins.json](../evidence/supplement-input-pins.json). These are selected-file checks, not active source/output scans or full tree/image hashes.

The public matching donor is [AOSP system/core commit a6116961338548409b14076eefbef211afc8c3fe](https://android.googlesource.com/platform/system/core/+/a6116961338548409b14076eefbef211afc8c3fe), tag `android-6.0.1_r1`. This establishes a matching public implementation, **not the unknown OEM build's source commit**. Original source, copyright notices, Apache 2.0 terms, and NOTICE are retained under `donor/`; [donor-pins.json](../evidence/donor-pins.json) and [support-pins.json](../evidence/support-pins.json) record exact URLs, commits, sizes, and hashes.

| Source | SHA-256 |
|---|---|
| Old `include/utils/PropertyMap.h` | `199d6f35a7f6b70b9b6258c1a78d7671b9253a53171f2a624943851344c427c5` |
| Old `libutils/PropertyMap.cpp` | `b2f0d9e949a1fe4a8670df34fdcc46b9204607f5b9fdb41f43c16c73f9029a4d` |
| Frozen current `include/input/PropertyMap.h` (prior receipt) | `877d73d0ca6ad446a55355a69c33df2e14316296f566e8f7fe02024a02d34208` |
| New `src/legacy_property_map.h` | `21753f70dca1b189a9faf68469ed1a2705e2415532ed6c5013640d79dc0cdc82` |
| New `src/legacy_property_map.cpp` | `6b4bab418a5511ca11e7308ef623a6e13963fba1a2fb28fe2ccdc41cb5bd41c6` |
| New `src/exports.map` | `fb5ea92095ac6e574668b7d4e9e58115aa6e711c8b2fe2156636c746c813a6e6` |
| New `src/import-renames.txt` | `d38c654c04a1243394d42b15d17590463b3835e52c26ad061c63ac65c9888403` |
| New `src/Android.bp.snippet` | `c0b80092097ab50778eecbf30a67f4f09e5328cad63b1326ac086693b2626f2a` |

The adapter changes only the class name to `AsusPropMap`, `String8::string()` spelling to `c_str()`, log tag/includes, and the API surface to the nine actual requirements. The method bodies otherwise match the donor byte-for-byte after those substitutions; `scripts/analyze.py` asserts this. It adds no backend pointer, registry, fake field, unordered_map, or allocation policy. The current Karnak unordered-map shim is not used. System libutils and libinput are not replaced.

The host backend is primary [AOSP system/core a3b721a32242006b59cb12bd62c9133632af3a2d, libutils/binder](https://android.googlesource.com/platform/system/core/+/a3b721a32242006b59cb12bd62c9133632af3a2d/libutils/binder/). Its VectorImpl header matches the frozen SDK37 header SHA-256 exactly (`2c0d7bff0eb9e8aee019ec5c2a939951200104068ece641485014f0c5f4c2bf2`). Its String8 header differs from the frozen header only in inline comparison pointer fast paths; **the adapter and tests compile with the frozen header**. This source identity does not assert that the whole SDK37 libutils binary was built from that AOSP commit. Actual provider disassembly supplies the binary layout/ownership evidence.

ARM64's frozen C-only UAPI subset lacked headers required by its C++ includes. Seven headers actually used were fetched from primary [Bionic 731631f300090436d7f5df80d50b6275c8c60a93](https://android.googlesource.com/platform/bionic/+/731631f300090436d7f5df80d50b6275c8c60a93): arm64 `fcntl.h`, `sigcontext.h`, `sve_context.h`, `signal.h`, `siginfo.h`, `errno.h`, and generic `signal.h`. Sixteen small selected headers were fetched in total; all are pinned in [uapi-pins.json](../evidence/uapi-pins.json), with the actual used subset in compile pins. No active headers were read or edited. Thus ARM64 uses a documented frozen-header union plus this primary-source supplement, rather than a claim that every include came from the original snapshot.

## The nine contracts come from real ELF

[OEM method inventory](../evidence/oem-methods.json) extracts the required names from the existing actual ELF inventories, checked again directly against the frozen ARM32 binary in [frozen-types.txt](../evidence/frozen-types.txt). ARM64's real-ELF inventory has the same nine names. Return types and `int32_t` semantics come from the pinned donor; C++ mangling alone does not encode these return types.

| Required contract | Exact original name |
|---|---|
| Constructor C1 | `_ZN7android11PropertyMapC1Ev` |
| Destructor D1 | `_ZN7android11PropertyMapD1Ev` |
| `void clear()` | `_ZN7android11PropertyMap5clearEv` |
| `void addProperty(String8 const&, String8 const&)` | `_ZN7android11PropertyMap11addPropertyERKNS_7String8ES3_` |
| `bool hasProperty(String8 const&) const` | `_ZNK7android11PropertyMap11hasPropertyERKNS_7String8E` |
| `bool tryGetProperty(String8 const&, String8&) const` | `_ZNK7android11PropertyMap14tryGetPropertyERKNS_7String8ERS1_` |
| `bool tryGetProperty(String8 const&, bool&) const` | `_ZNK7android11PropertyMap14tryGetPropertyERKNS_7String8ERb` |
| `bool tryGetProperty(String8 const&, int32_t&) const` | `_ZNK7android11PropertyMap14tryGetPropertyERKNS_7String8ERi` |
| `bool tryGetProperty(String8 const&, float&) const` | `_ZNK7android11PropertyMap14tryGetPropertyERKNS_7String8ERf` |

No `load`, Parser, `addAll`, C2, or D2 export was invented as an OEM requirement. The donor's complete API is preserved as source evidence; the production adapter exports only the listed nine private-name counterparts.

## Representation, vtable, and ownership

The [original ARM32 method disassembly](../evidence/oem-arm32-property-map-disassembly.txt) confirms constructor code at `0xb64c` calls `SortedVectorImpl(8,0)` then installs the vector vtable at offset zero. Destructor `0xb668` reinstalls that table, calls `finish_vector`, and then SortedVectorImpl destruction. Clear directly calls VectorImpl clear. Add constructs two String8 values and calls SortedVectorImpl add; lookup uses indexOf, then copies the stored value. Some OEM function labels alias String16 or PropertyMap destructor addresses because identical code was folded; they do not imply String16 key storage or a PropertyMap virtual base.

The unchanged donor and new adapter were separately compiled for both actual Android widths. Full layouts and virtual tables are in `artifacts/{arm,arm64}/{donor-layouts,layouts}.txt`.

| Field or type | ARM32 bytes/offset | ARM64 bytes/offset |
|---|---:|---:|
| PropertyMap / AsusPropMap size | 20 | 40 |
| Object alignment | 4 | 8 |
| Sole `mProperties`, its `mVector`, VectorImpl base/vptr | 0 | 0 |
| `mStorage` | 4 | 8 |
| `mCount` (`size_t`) | 8 | 16 |
| `mFlags` (`uint32_t`) | 12 | 24 |
| `mItemSize` (`size_t`) | 16 | 32 |
| `String8` size, sole `mString` offset | 4 / 0 | 8 / 0 |
| key/value pair size, value offset | 8 / 4 | 16 / 8 |
| SharedBuffer prefix before data | 16 | 24 |

PropertyMap itself has no virtual methods. Its member's VectorImpl vptr occupies the first word. The old and new SortedVector tables each contain two Itanium header words and nine callable slots: complete destructor, deleting destructor, construct, destroy, copy, splat, move-forward, move-backward, compare. After the address point their byte offsets are `0,4,8,12,16,20,24,28,32` on ARM32, and `0,8,16,24,32,40,48,56,64` on ARM64. Flags are zero because the pair needs String8 construction/destruction/copy, even though String8 has the trivial-move trait. Compare orders the key using String8/strcmp. Moves transfer ownership without incrementing the source again.

The actual OEM ARM32 table is a **44-byte** exported object at `0x18870`, address point `0x18878`, symbol `_ZTVN7android12SortedVectorINS_16key_value_pair_tINS_7String8ES2_EEEE`. [Raw slots and callback symbols](../evidence/oem-vtable.json) show null offset/RTTI headers, destructor addresses `0xb669`/`0xbc11`, callbacks `0xbc39`, `0xbc65`, `0xbc91`, `0xbcc5`, shared move code `0xbcfd`, compare `0xbd1d`. The deleting destructor body also calls finish_vector and SortedVector destruction before its tail transfer. These slots agree with both compiled tables. This is a member-vtable match, not a fake PropertyMap vtable.

Genuine SDK37 providers, preserved before/after:

- ARM32 libutils: `7441b9292d84e08e18a58eda1a0f50789818e47f2b22bd0065900d6065f95924`.
- ARM64 libutils: `d2f70c971b5b3b5b8a17ff899deadab16fc9d0fd68511354ce16ac489160ce3c`.
- OEM ARM32 libutils used only as evidence: `dfd73325265c169d016e053dc7d2256e33ebf474e232b8abfdc578891ec4e9cb`.

[Provider ARM32 disassembly](../evidence/provider-arm-selected-disassembly.txt), [ARM64 disassembly](../evidence/provider-arm64-selected-disassembly.txt), and `sorted-provider-ctors-dtors.txt` prove the compiled header is compatible with actual field accesses. SDK37 SortedVector construction at ARM32 `0x11fac` writes itemSize at 16 and flags at 12, and ARM64 `0x1db08` writes itemSize at 32 and flags at 24. Exported C2 signatures are `_ZN7android16SortedVectorImplC2Ejj` / `_ZN7android16SortedVectorImplC2Emj`; D2 is `_ZN7android16SortedVectorImplD2Ev` in both.

String8 copy preserves its single data pointer and acquires the SharedBuffer at data minus 16/24; assignment acquires the new buffer before releasing the old one. Destruction releases that buffer and frees only the last owned allocation. The current source uses an atomic 32-bit refcount, size_t size, and two reserved/client words in the same 16/24-byte prefix as the old source. Allocation and free remain in the current provider. Vector growth allocates SharedBuffer storage, dispatches copies/moves through the exact slots, and finish_vector releases storage and invokes pair destruction on the last owner before freeing it. The adapter neither allocates these buffers itself nor mixes allocators or writes their reserved data. Private String8 copies outlive caller temporaries and map clearing, as exercised by the host test.

The donor's compiled ARM64 layout and the actual ARM64 provider primitives are qualified. **An actual OEM ARM64 PropertyMap constructor/table was not newly captured**: the frozen ARM64 inventory supplies method imports, but not old ARM64 libutils or a retained libcam_utils binary. Its OEM object-size match therefore remains a fresh-review gate; do not infer it solely from the ARM32 OEM trace.

## Binding that cannot intercept the modern object

The adapter deliberately defines `android::AsusPropMap`, not `android::PropertyMap`. All nine mangled names replace `11PropertyMap` with `11AsusPropMap`. They are disjoint from the modern class even for the otherwise identical constructor/destructor/clear manglings. No original PropertyMap alias is exported. Hidden visibility, the exact nine-entry export map, and `-Bsymbolic` keep template/vtable definitions local. Modern calls consequently cannot resolve to this old-layout object in any namespace.

[Binding contract](../src/BINDING.md) and [executed binding receipt](../evidence/binding.json) specify the intended camera namespace. An isolated **ARM32** copy of the genuine importer was rewritten using pinned patchelf 0.18.0, all nine symbol renames, and an explicit DT_NEEDED for `libasus_camera_legacy_property_map.so`. Its pre/post original hash is `be8cb386e5f5ea7045b24017870d85b67774518f6e9ae9efd3ed1c00f5dcdcec`; the new witness hash is `625bfeb69cdc3118661588264e030d2ec07be96e9f3cf967a66f79eba0e743fa`. Patchelf itself hashes to `35fc95654387035338a74bb8cf62fde3712ec83dd8ca30a768deb714d07f063a`.

The witness retains the original exports and every non-PropertyMap symbol contract, existing dependencies, and `.text`, `.rodata`, and `.data` bytes. Only a new copy was changed. The rewritten importer has zero original PropertyMap imports and all nine private imports, each exported by the adapter. It is explicitly named `libcam_utils.property-map-WITNESS.so`, not an integration artifact. No other OEM missing ABI was repaired. The original entire camera closure remains unqualified.

The future namespace must load this uniquely named DT_NEEDED library from permitted camera paths and bind its primitive imports to genuine SDK37 providers, with no old system runtime library introduced. Do not rely on a preload, global alias, load-order trick, or an unrenamed shim. The [Android.bp snippet](../src/Android.bp.snippet) is noninstallable and has not been evaluated by Soong/Ninja. A deployable namespace stanza is withheld because the frozen graph is incomplete, rather than inventing platform/provider access rules.

## Compiler/linker and precise provider frontier

[commands.json](../evidence/commands.json), [old-donor commands](../evidence/abi-supplement-commands.json), and [reproduce-commands.sh](../evidence/reproduce-commands.sh) contain **actual full arguments**, working directories, exit codes, and output. Compiler identity is Clang r584948b, Android build 14863223, version 22.0.1, LLVM `2d65e4108033380e6fe8e08b1f1826cd2bfb0c99`. The ARM32 target is `armv7a-linux-androideabi37`, Cortex-A53/ARMv8-A/softfp; ARM64 is `aarch64-linux-android37`. Newly compiled ARM32 code is ARM state; its final disassembly uses ELF mapping symbols, while OEM Thumb and provider Thumb receipts explicitly use the Thumb triple. The PLT interworking ABI is preserved.

Both shared libraries link `-nostdlib -shared -fuse-ld=lld`, real width-matched CRT begin/end, `--no-undefined`, `-Bsymbolic`, the export map, and frozen `-lutils -llog -lc++ -lc -lm -ldl`. The test program also compiles to an Android object for both widths. Neither a test executable nor an adapter was run on Android.

[provider-closure.json](../evidence/provider-closure.json) maps **every strong adapter import** to its exact captured direct export, raw symbol/version spelling, provider hash, and DT_NEEDED graph. All direct imports resolve at link time. This is narrower than recursively closing or executing all supplier DSOs:

- Adapter → libutils, liblog, libc++, libc, libm, libdl.
- libutils → libcutils, liblog, **libvndksupport**, libc++, libc, libm, libdl.
- libcutils → liblog, **libbase**, libc++, libc, libm, libdl.
- liblog/libc++ → libc, libm, libdl; libm → libc; libc/libdl → **ld-android**.

The bold libraries/loader are absent from these frozen sets in both widths. Their dependencies, versions, and actual namespace access are not qualified. `--no-undefined` does not assert recursive shared-library closure. No active outputs were inspected to fill the gap. This is an explicit runtime blocker, not evidence that these platform sources are absent.

## Behavior executed against the production implementation

[behavior.cpp](../tests/behavior.cpp), [final host receipt](../evidence/host-final.txt), and [full host commands](../evidence/host-commands.json) execute `src/legacy_property_map.cpp` with real current upstream VectorImpl, String8, and SharedBuffer sources and the frozen headers. The host harness only transports log macros to stderr and aborts on fatal conditions; allocation, reference counting, vector callbacks, parsing, and map behavior are real code. Unused UTF conversion code is discarded by function/data section GC; there is no Unicode or map success stub.

Linux g++ 13.3.0 runs with UBSan and `-fno-sanitize-recover=all`. Assertions cover absent string/bool/int/float lookups leaving outputs unchanged, add, overwrite, nonzero/zero boolean conversion, signed and leading-whitespace decimal conversion, rejection of empty/trailing whitespace/junk/`true`/hex integer input, float conversion, NaN/Inf/range-to-Inf, 128 keys inserted in reverse order and looked up, repeated clear, temporary key/value ownership, retained output after clear/destruction, and 1,000 reconstruct/destroy cycles with surrounding canaries.

The run reports **64,518 checks** (many are repeated canary bytes, not distinct cases), with **3,414 tracked allocations / 3,413 frees / one intentionally retained process-lifetime AOSP empty-string allocation** after test values and map storage are destroyed. The harness checks that live allocations return exactly to the warmed-up baseline. UBSan reports no error. This is host evidence, not execution of the captured Android libutils binary.

The donor semantics deliberately remain intact: add replaces; absent/failed lookup leaves outputs alone; bool parses through int32_t; integer parsing is base-10 strtol narrowed to int without an errno/range guard; float uses strtof and accepts libc-supported forms if the end pointer reaches NUL. Integer overflow can therefore differ with 32/64-bit `long`. Float Inf/NaN are accepted. Embedded-NUL and locale/range behavior follow the donor/libc contract and are not newly hardened. No stricter "helpful" parsing was substituted. File parsing/load is outside the nine imported methods and is not exposed or claimed tested.

A Linux `-m32` execution build was attempted but cannot compile because host multilib C/C++ headers are absent. The failed receipt is preserved in [host-commands-including-m32-attempt.json](../evidence/host-commands-including-m32-attempt.json). QEMU user emulators and Valgrind were absent. No packages were installed. Android32/64 behavior execution and target sanitizer coverage remain open.

## Fresh-review handoff

1. Review the nine-symbol donor extraction, field tables, actual SDK37 provider disassembly, old ARM32 vtable, and hidden/private export proof. Run `scripts/analyze.py` and `scripts/verify.py` locally. No physical action is part of these checks.
2. Obtain separately frozen missing provider/loader artifacts and the actual OEM ARM64 constructor/vtable/object-storage evidence if ARM64 is considered. Audit symbol versions, recursive closure, and the final camera namespace before changing the noninstallable status.
3. In a separately authorized isolated Android runtime, run the same behavior fixture against **the captured genuine SDK37 providers**, with canaries and memory instrumentation, in each candidate width. Exercise the rewritten importer's binding without calling its unrelated camera or private-data functionality. Do not load the complete OEM importer merely to run PropertyMap tests: its unrelated closure is unresolved.
4. Only after review, design a new implementation spike for any active integration. This report grants no approval flags or physical GO. Other camera ABI, metadata, HAL device/frame behavior, fitted sensors, and every excluded hardware/subsystem concern remain outside this work.

Remote scratch is exclusively `/srv/android/asus-camera-property-map-20261106`, approximately 5 MB, below the 512 MiB allocation limit. Work was serial and affined to one CPU with 1 GiB address-space, per-process CPU limits, and finite per-command wall time. [Budget receipt](../evidence/remote-budget.json) records the measured scratch size. No children, device/ADB/root/camera/USB commands, private files/calibration/keys, cloud lifecycle, process signals, mutable R9 directories, active build/source/out/cache/kit/probe writes or polling, native Ninja/Siso, full source-tree/image copies, or full tree/image rehashes were used. The authorized existing SSH transport was read and reused without modifying it or copying credentials.
