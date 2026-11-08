# Genuine SDK37 host metadata resolver qualification: PASS

Both reusable host resolver ELFs are compiled against the **actual existing SDK37 host libraries and exported headers**. Positive and negative queries passed on owned synthetic metadata/context inputs. The reusable tool portion of the prior missing gate is now supplied; no genuine completed-product resolver group, metadata admission or observer input was fabricated.

Actual ELFs: [resolve_fs_config](artifacts/resolve_fs_config), [resolve_contexts](artifacts/resolve_contexts). Result/pins: [acceptance.json](acceptance.json). Exact future interface, new v5 source keys and remaining gates: [PARENT-CONTRACT.md](PARENT-CONTRACT.md).

Owned builder prefix: `/srv/android/asus-sdk37-host-metadata-resolvers-20261106`; canonical delivery is `handoff-r2/`, and successful compiled TUs are in `source-r4/`. A first handoff correctly refused collision with the preserved original root TU; its partial files remain and no existing source was overwritten. No earlier unit, kit, index or source/out file was modified. Local byte verification matched all 78 observer-preparation and 72 mechanism payloads. This unit builds no observer image and accesses no actual SYSTEM.

## Genuine inputs and direct compilation

Narrow inspection found the expected exported C symbols and SDK37 headers/libraries already available. No generated-input producer was missing for these TUs, and no Ninja/AOSP/kernel build was invoked. The only active-out files selected were explicit available host libraries/tools and their resolved dependencies, never real product artifacts. Their sources and Android.bp behavior flags were frozen read-only into owned copies.

Pins:

- `libcutils.so`: `f7bb5a007f35c54bf078c2c2e00db9b50ec89bf730a57ddb17c79fee2cd62806`.
- `libselinux.so`: `9f8583e03e81fae3152378aaadff5014cc0e8e5d6026d449ca37f8420491e2ab`.
- `libpcre2.so`: `a4a3df259f0d59cdb3091aa224e82d1a2c2164887aeadb5a0f969b77a2571158`.
- SDK37 `sefcontext_compile`: `3fda3c25aed8b81ac04e4e37b5d1384d434f66fbd34304c7a1f1b86b1898fd5b`.
- Actual SDK37 `fs_config.cpp`: `7b27879f07f84b694f512f3eb18c1a421558f12e0e516c303876a8615d1f7303`.
- Actual `label_file.c`: `e841b8f5cdc5fe688b363330d390cd410bbbd6b105db47bf8c5812bc21dbaaf8`.
- Actual e2fsdroid `perms.c`: `fcad0b5d7208ca4702ab5e79671c2b7982e2b634aa17f512531a523c023e3609`.

The callers were directly compiled serially with pinned GCC 13.3.0, owned copies of the real SDK37 headers, and those real shared libraries. There are no API mocks, behavior substitutes, library patches or distro resolver substitutions. The normal Linux compiler/libc runtime is pinned separately. Loader/runtime closure checks resolved every dependency into `inputs-r4/lib64`; native queries invoke the owned loader with cache inhibited and LD environment injection removed. Compiler commands, actual exits, dependency files, ELF dynamic sections, build IDs/comments and dynamic closure are retained in [build.json](evidence/build.json) and [capture.json](evidence/capture.json).

Qualified tool ELFs:

- fs_config caller, 16,352 bytes: `46b22136be3c1fce5e60a709e0d675fc7b7010fcc3e9ac390ff28db5171141c2`.
- selabel caller, 16,536 bytes: `efefb92bdcf73bc5fa8f1c6b7008d85c405d1372ce7ecc3aa2487a9bdc3bc273`.
- Qualified runtime/source group: `624ff875e00eea2489502489bfad4587efa398457d110bf404baac76e97aeff3`.

These are Linux x86-64 host ELFs. Their interpreter/RPATH bind the qualified builder layout; dependencies remain on the VM. They are not tablet executables. Existing SDK37 libraries are frozen existing binaries with primary-source/ABI/behavior correspondence; this direct caller build does not claim reproducible rebuilding or whole-source provenance of every library instruction.

147 source/header/tool/library copies have before/copy/after equality: 146 build-input snapshots plus the explicit SDK37 capability UAPI header. Reused attempt copies are hardlinked only between this unit's owned directories after matching original source bytes; no link was made to active source/out. Compiler header closure is taken from actual dependency files, not a broad include/out scan. The unique-file footprint was 85,747,324 bytes at capture, below the 256 MiB unit cap; final audit recorded 86,102,039 bytes before the small handoff copies; the delivery receipt checks the cap again.

## Caller API and source behavior

The SDK37 public private/fs_config header declares the legacy `void fs_config(...)` ABI and the modern boolean getter. The caller deliberately uses the legacy API used by the creation pipeline, with `dir=0` and four fixed public files. No guessed default result is manufactured by the caller. Actual library fallback results are reported as such.

`fs_config_open` strips a trailing slash and then `/system`, searches six slots in order (system, vendor, oem, odm, product, system_ext), and can try the corresponding absolute host path after a failed captured-file open. Matching includes logical partition aliases such as `system/vendor/...` against `vendor/...`. Malformed override records can log an error, continue searching, and return built-in metadata with exit 0. Missing override files can fall back silently. Those behaviors were exercised; a native zero exit does not prove the desired inputs were consumed.

The actual binary override ABI is 16-byte header, capabilities at offset 8, prefix at offset 16. The capability header/source ABI probe compiled and ran successfully: fs_config result struct 24 bytes; vfs capability data/revision-2 representation 20 bytes; effective revision magic `0x02000001`. [abi.json](evidence/abi.json) pins the real SDK37 UAPI header and successful compile/run.

The SDK37 libselinux flags include BUILD_HOST, DISABLE_SETRANS and NO_PERSISTENTLY_STORED_PATTERNS. Explicit-path HOST behavior does not consume distribution substitution files; BASEONLY skips local/homedirs supplements. It can select between text and `.bin` by timestamp and retry the alternate after parse failure. Both a compiled-only stem and a direct `.bin` argument worked with the actual SDK37 compiler output. No policy-enforcement or SELinux type-existence validation is inferred from successful label lookup.

One small caller correction is supplied in [resolve_contexts-atomic-output.patch](source/resolve_contexts-atomic-output.patch): collect all four labels before printing. A missing fourth match now returns 1 with empty stdout instead of leaving plausible partial metadata. Earlier caller sources remain intact. The fs_config caller TU is unchanged from observer preparation. SDK implementation behavior is unchanged.

## Synthetic functional qualification

All fixtures are nonsensitive binary fs_config records and text/compiled context files, not filesystem images. The four query paths are hardcoded. The positive custom result, directly from genuine SDK37 functions, was:

```text
/system/build.prop 1101 2101 0640 capabilities=0x0
/system/bin/init 1102 2102 0750 capabilities=0x400
/system/bin/run-as 1103 2103 0710 capabilities=0x80000000c0
/system/vendor/etc/selinux/vendor_file_contexts 1104 2104 0440 capabilities=0x0
```

Labels were exactly `u:object_r:fixture_build_prop:s0`, `fixture_init`, `fixture_runas`, and `fixture_vendor_contexts` with the same prefix/suffix. These are explicit fixture labels/values, never production expectations. System overrides supplied the first two records; vendor overrides supplied run-as and the vendor alias record, proving those files were actually consumed. A conflict in the system slot won over vendor, proving search priority. Root, `/system` and `/system/` TARGET_OUT spellings resolved identically.

The baseline genuine built-ins produced 0600/root:root build.prop, 0755/root:shell init, 0750/root:shell run-as with mask `0xc0`, and 0644/root:root vendor contexts. Wrong valid override input produced different native values with exit 0; the guard rejected its substitution under the pinned original inventory. Missing or malformed vendor overrides produced fallback with exit 0 (malformed length logged an error); the guard rejected both. Wrong root likewise returned built-ins natively and failed the capture pins.

Missing contexts, malformed regex, corrupt compiled-only contexts and a missing fourth label returned native exit 1 with no stdout. A corrupt binary accompanied by valid text returned exit 0 through genuine alternate fallback; the guard refused the extra alternative. HOST/BASEONLY ignored added local/substitution sidecars natively, while the guard refused those unadmitted files. A valid but wrong context label also returned native exit 0 and failed the fixed context pin. See [qa.json](evidence/qa.json), [extra-qa.json](evidence/extra-qa.json), and individual stdout/stderr/exit files in `evidence/qa-logs/`.

The guarded CLI passed a real positive invocation and refused a wrong external pin with exit 2 without creating an output directory. An explicitly admitted absent slot succeeded only after both captured absence and absolute-host-fallback absence were checked; absence is not silently replaced with empty data or default values.

Capability representation was checked for zero and nonzero/high-word masks. Zero yields explicit null/absence. Nonzero run-as mask serialized to `01000002c0000000000000008000000000000000`, including the upper permitted word and zero inheritable words. The actual e2fsdroid source returns without creating a capability xattr for zero; it does not remove a pre-existing xattr. This is expected fresh-creation representation, not a claim that host xattrs were set, removed or executed. No privileged file/xattr operation occurred.

## Guarded receipt interface and remaining gates

`scripts/query.py` checks an externally pinned manifest, exact qualified tool group, six explicit present/absent search slots, strict binary record framing and complete context inventory. It then runs only the two fixed native queries, retains stdout/stderr/exits, rejects diagnostics or partial output and checks input identities afterward. It does not reimplement fs_config or regex selection. Native fallback is distinguished from parent capture admission rather than disguised as a native error.

Each process runs on one CPU, 1 GiB address space, 60 CPU seconds and a 90-second wall alarm; native calls also have a 30-second timeout. Query output files are capped at 16 MiB, override metadata at 1 MiB and contexts at 4 MiB. Host compilation/tests are serial. Early compiler-header, path-normalization verifier and receipt-recording failures are preserved in owned attempt directories and historical scripts; the successful r4 compile/query evidence is authoritative. None involved AOSP/source/out mutation or library replacement.

The reusable tool gate is complete. Remaining actual-input gates are a qualified completed build/host validation, the coherent real override/context/source/installed-content capture, v5 integration of exact new tool/source binding keys, and parent admission before any production resolver group or full-SYSTEM observer use. [PARENT-CONTRACT.md](PARENT-CONTRACT.md) specifies the minimal guarded command and receipt/source roles; it is not a filled production manifest or an admission. No earlier contract was edited.

No AOSP/Ninja/kernel build, source touch, active source/out/kit/index write, build/process inspection or lifecycle operation, product output selection/capture, SYSTEM read/mount/copy/rehash, network fetch, device/ADB, factory/private key/calibration access or cloud resource change occurred. No new observer image, actual Android runtime, hardware, physical boot, flashing readiness or GO is established.
