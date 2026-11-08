# ARM32 PropertyMap importer repair

Question: can the genuine frozen ARM32 importer acquire the private adapter dependency and nine private imports without the completed review's patchelf corruption?

Status: **P1 repaired for static packaging only.** The corrected real witness passes the bounded integrity comparison. This spike is independent of first flash and the active Android native build. Nothing was enabled, packaged into a product, installed, loaded, or run on Android. Source and adapter originals remain immutable.

Important outputs:

- [Corrected genuine ARM32 witness](artifacts/libcam_utils.property-map-CORRECTED-WITNESS.so).
- [Reusable narrow rewrite](scripts/stage_importer.py), [integrity checks](scripts/integrity.py), and [bounded verification](scripts/verify.py). The small ARM32/APS2 reader in `scripts/elf32.py` is reused from the completed review, with byte-input support and a guard against Python `-O`.
- [Rewrite receipt](evidence/rewrite.json), [corrected comparison](evidence/corrected-comparison.json), [known-bad comparison](evidence/known-bad-comparison.json), [verification](evidence/verification.json), and [actual remote command/budget receipt](evidence/add-needed.json).
- [Original file pins](evidence/original-input-pins.json): all 185 files in the two completed source/review spikes remained unchanged, including the retained bad witness and its evidence.

## Result and provenance

The original [report](../2026-11-06-asus-camera-property-map/report/PROPERTY-MAP.md) and [binding document](../2026-11-06-asus-camera-property-map/src/BINDING.md) remain historical evidence. Their claim that the retained combined-rename witness preserves all non-PropertyMap contracts is false, as established by [the completed P1 review](../2026-11-06-asus-camera-property-map-review/REVIEW.md). This spike supersedes that witness-integrity claim only; it does not change the adapter qualification or close any runtime gate.

| Artifact | SHA-256 |
|---|---|
| Genuine frozen original importer | `be8cb386e5f5ea7045b24017870d85b67774518f6e9ae9efd3ed1c00f5dcdcec` |
| Retained known-bad witness, unchanged | `625bfeb69cdc3118661588264e030d2ec07be96e9f3cf967a66f79eba0e743fa` |
| New add-needed-only intermediate | `dd4cb852bc0d245d9a1a3a580cc5978e443293c7f5e8efdedc0c5e62c92e5a43` |
| **Corrected witness** | `40a9407f70f797552b4c5c5a4b034c04589fb8fedc65538ccf64da50831e59b4` |
| Existing ARM32 adapter, unchanged | `d371807e43c770306100670d2cd2dad1e6a00262b1f2483f266cbd72ecef4405` |
| Pinned `/usr/bin/patchelf` | `35fc95654387035338a74bb8cf62fde3712ec83dd8ca30a768deb714d07f063a` |

The existing SSH transport was imported directly from `../2026-11-06-asus-product-input-build-kit/scripts/remote.py`, without copying credentials. The sole remote operation read the completed frozen public importer and pinned `/usr/bin/patchelf`, verified both hashes, and executed:

```sh
/usr/bin/patchelf \
  --output /srv/android/asus-camera-property-map-repair-20261107-static/importer-needed-only.so \
  --add-needed libasus_camera_legacy_property_map.so \
  /srv/android/asus-camera-arm32-route/public/vendor_lib_libcam_utils.so
```

There was no rename option in that operation. It used a new exclusive scratch prefix, CPU 0 only, 1 GiB address space, 40 CPU seconds, an 8 MiB per-file limit, a 20-second tool timeout, and a 110-second outer SSH timeout (stricter than the requested approximately 20-minute bound). The recorded operation elapsed 0.0184 seconds. The output artifact is 150,753 bytes; artifact plus the serialized remote receipt is less than 153 KiB, below 32 MiB. The remote script is intentionally one-shot and refuses an existing prefix; verification below requires no SSH.

The local rename writes exactly nine complete, equal-length `.dynstr` strings, changing `11PropertyMap` to `11AsusPropMap`. Their dynamic-symbol indices remain **81–89**, below GNU hash's first symbol **142**. They are each undefined, unversioned (raw version zero), global FUNC, default visibility, zero size/value. The script rejects wrong names/count/order, definitions, versions, bindings, visibility, private names already present, unexpected hash scope, incomplete/out-of-bounds/overlapping ranges, and any reused string range, including suffix references from other symbols, dynamic strings, or version auxiliary records. It pins the original and adapter. The separate add-needed result must first pass the full comparison without any rename mapping.

The rename changes **63 individual bytes** inside those nine strings; everything outside the nine ranges is byte-identical to the add-needed intermediate. All `.dynsym` bytes and the entire GNU hash table/defined suffix remain untouched by the rename. Add-needed relocates metadata and adjusts numeric section-header indices; it preserves each symbol's resolved section identity and order. The corrected output is still an ARM32 offline witness, not an installable camera artifact.

## Exact bounded verification

| Check | Retained bad witness | Corrected witness |
|---|---:|---:|
| Dynamic symbols | 419 | 419 |
| Ordinary REL relocations | 279 | 279 |
| APS2-packed REL relocations | 1,801 | 1,801 |
| Unrelated relocation identity mismatches | **63** | **0** |
| Wrong symbol-to-section associations | **274** | **0** |
| Symbol-index contract mismatches | 274 | **0** |
| GNU hash lookups succeeding | 277 | 277 |
| Version sections byte-identical | yes | yes |
| Ordered existing dependencies preserved | yes | yes |

All **2,080** relocation records are compared by relocation address, ARM relocation type, the actual implicit addend read through the file-backed/zero-fill PT_LOAD mapping, and resolved symbol name/value/size/binding/type/visibility. Section identity is checked separately for every symbol and also included in the complete comparison records. The bad witness has 58 ABS32 and five GLOB_DAT identity changes. Its separate corrupt section metadata affects more relocation records, which is reported separately rather than conflated with the 63 identity changes.

The corrected witness has exactly nine intended changed import identities, each with one ordinary JUMP_SLOT relocation; all 2,071 other relocation identities are unchanged. Relocation totals by type are RELATIVE 774, ABS32 947, GLOB_DAT 80, JUMP_SLOT 279. Their target words/addends are unchanged. Section allocation addresses and bytes outside the permitted relocated metadata are unchanged, including APS2, ordinary PLT relocations, GNU hash, code, object storage, GOT, initialization arrays and unwind tables. The three GNU version sections retain their exact bytes. All 419 symbols preserve indices, values, sizes, binding/type, visibility and resolved section identity.

The reader checks segment/section bounds, allocated-section LOAD mappings, alignment, dynamic pointers and associated sizes, symbol/string/version table links, 445 dynamic string references (444 in the original), and all 277 GNU hash lookups. The dependency list is exactly the original 18 entries in their existing order with `libasus_camera_legacy_property_map.so` prepended. The existing adapter hash and exact nine private exports are checked. No libutils/libinput replacement or original PropertyMap alias is introduced.

Only two focused in-memory refusal cases were run: a target import with a nonzero version, and another symbol reusing the suffix of a target's string. Both were refused before writing output. No model behavior checks, adapter cross-builds, fuzz campaign, new provider capture or independent review were run.

From the ideas workspace, reproduce the corrected bytes locally using the retained actual intermediate and existing adapter. Output and receipt must be new paths:

```sh
python3 -B 2026-11-07-asus-camera-property-map-repair/scripts/stage_importer.py \
  --original 2026-11-06-asus-camera-property-map-review/evidence/importer-original.so \
  --adapter 2026-11-06-asus-camera-property-map/artifacts/arm/libasus_camera_legacy_property_map.so \
  --needed-only 2026-11-07-asus-camera-property-map-repair/artifacts/importer-needed-only.so \
  --output 2026-11-07-asus-camera-property-map-repair/artifacts/reproduced.so \
  --receipt 2026-11-07-asus-camera-property-map-repair/evidence/reproduced.json
```

The executed original command used `artifacts/libcam_utils.property-map-CORRECTED-WITNESS.so` and `evidence/rewrite.json` as those final two arguments. On a separately supplied Linux host with the pinned binary, `--patchelf /usr/bin/patchelf` may replace `--needed-only ...`; the reusable script performs add-needed alone with a finite timeout and validates it before renaming. This is not a request to use an active build host or repeat the remote run.

Reproduce the complete bounded verification (expected known-bad failure is asserted, so overall exit zero means the evidence matches):

```sh
python3 -B 2026-11-07-asus-camera-property-map-repair/scripts/verify.py
```

That command freshly compares both real witnesses, reconstructs the corrected bytes in memory, runs only the two refusal cases, and rechecks the 185 original hashes. Its executed exit status was zero. `evidence/known-bad-comparison.json` records `FAIL` with the complete 63/274 mismatch lists; `evidence/corrected-comparison.json` records `PASS` with zero mismatches.

## Continuation

P1 closure is **STATIC PACKAGING ONLY**. Missing recursive providers `libvndksupport.so`, `libbase.so`, and `ld-android.so`; Android namespace/runtime loading and provider binding; OEM ARM64 constructor/vtable/object-storage evidence; camera HAL3/metadata/ISP compatibility; kernel compat ioctls; and physical operation remain unresolved. Runtime string-based `dlopen`/`dlsym` use is not qualified by renaming undefined ELF imports.

Keep the witness offline. Any later runtime or camera work is a separate task with its actual inputs and constraints. This repair adds no integration, enablement, approval framework, mandatory review round, loadability claim or camera-success claim. The active Android build and first-flash path remain independent. No device/ADB/root, private calibration/key access, excluded PCM-copy patch, active source/output/cache/lock/process inspection, native compiler/Soong/Ninja, package installation/download, GPIO/charging/radio, or cloud lifecycle work occurred.
