# Qualified host resolvers: future parent/v5 integration

Tool portion is qualified. No actual product metadata group, capture, admission or observer header was produced. This is a new unit; earlier observer/mechanism sources, kits and contracts remain unchanged.

## Exact reusable tools

Builder prefix: `/srv/android/asus-sdk37-host-metadata-resolvers-20261106`. Canonical delivered document/source tree is `handoff-r2/`; original root `source/` is a preserved first-attempt version. Successful compiled TUs are `source-r4/resolve_fs_config.cpp` and `source-r4/resolve_contexts.c`, matching the delivered `source/` files. Do not use historical root source as the new producer.

- `bin-r4/resolve_fs_config`: Linux x86-64 ELF, SHA256 `46b22136be3c1fce5e60a709e0d675fc7b7010fcc3e9ac390ff28db5171141c2`.
- `bin-r4/resolve_contexts`: Linux x86-64 ELF, SHA256 `efefb92bdcf73bc5fa8f1c6b7008d85c405d1372ce7ecc3aa2487a9bdc3bc273`.
- `inputs-r4/bin/sefcontext_compile`: existing genuine SDK37 compiler, SHA256 `3fda3c25aed8b81ac04e4e37b5d1384d434f66fbd34304c7a1f1b86b1898fd5b`.
- `qualified-tools.json`: exact resolver ELF, script, public sources/headers and dynamic runtime dependency set. SHA256 `624ff875e00eea2489502489bfad4587efa398457d110bf404baac76e97aeff3`.

`inputs-r4/lib64` holds the copied genuine SDK37 libraries and complete resolved Linux loader/runtime closure. Use the qualified prefix or reproduce its exact pinned layout: the ELFs' interpreter/RPATH point there. These are Linux host ELFs, not tablet binaries. The local `artifacts/` copies are the actual small ELF bytes; large toolchain/dependency/fixture files remain on the VM.

Native query calls, for diagnosis only, are fixed-path APIs:

```sh
R=/srv/android/asus-sdk37-host-metadata-resolvers-20261106
"$R/inputs-r4/lib64/ld-linux-x86-64.so.2" --inhibit-cache \
  --library-path "$R/inputs-r4/lib64" "$R/bin-r4/resolve_fs_config" "$FROZEN_TARGET_OUT"
"$R/inputs-r4/lib64/ld-linux-x86-64.so.2" --inhibit-cache \
  --library-path "$R/inputs-r4/lib64" "$R/bin-r4/resolve_contexts" "$FROZEN_CONTEXT_STEM"
```

Raw fs_config exit 0 is not admission: missing/malformed/wrong search inputs may yield built-in fallback. Raw selabel may use a valid alternate text file when compiled contexts are corrupt. Use the guarded query interface below for receipt production. It uses those same native tools and makes no API substitutions.

## Required metadata capture and new v5 source keys

After an actual completed qualified build is admitted, the parent/v5 owner must bind these tool/source bytes to its coherent source/installed-content group. No such real inputs exist in this qualification.

Required new binding keys or equivalent explicit source-capture roles:

- Qualified tool-group digest, both resolver ELF/source hashes, complete actual dynamic closure, copied SDK37 libcutils/libselinux/PCRE2 hashes, compiler/linker/build receipt and API headers, the capability ABI/probe receipt and e2fsdroid `perms.c` source pin.
- Actual `native_target_out` passed to e2fsdroid/fs_config, plan/source binding, and the normalized native search root. Source strips one trailing slash then a trailing `/system`. Do not guess that all packaged fs_config files are consumed: the six native search slots govern resolution.
- Exact `system`, `vendor`, `oem`, `odm`, `product`, `system_ext` `etc/fs_config_files` search inputs under that native search root, with per-slot actual origin path, captured path/hash or independently attested absence. File queries do not consume `fs_config_dirs`; directory semantics are outside this four-file tool scope.
- The exact final context binary, compiler/PCRE architecture/version provenance, consumed options (`SELABEL_CTX_FILE`, `SELABEL_OPT_PATH`, `BASEONLY`, `S_IFREG`) and absence of alternate/sidecar context inputs in the guarded capture. Bind source `BUILD_HOST` behavior, not unrelated distro selabel behavior.
- Actual completed-build/host-validator receipt digests, coherent source binding, and captured installed-content receipt digest for the four public files. The query does not open image files or hash installed file contents.

Copy captured override bytes only into their **corresponding normalized search slot**, preserving native semantics. Never promote a packaged-but-unconsumed override or synthesize a file to suppress fallback. Actual absent files must remain absent and be declared absent explicitly. Before allowing an absent slot, the guarded query checks that the matching absolute host fallback path is absent too (metadata-only check); otherwise it refuses. Native fs_config can search those absolute paths after any failed capture open.

The input capture layout is fixed:

```text
<capture_root>/layout/system/etc/fs_config_files
<capture_root>/layout/vendor/etc/fs_config_files
<capture_root>/layout/oem/etc/fs_config_files
<capture_root>/layout/odm/etc/fs_config_files
<capture_root>/layout/product/etc/fs_config_files
<capture_root>/layout/system_ext/etc/fs_config_files
<capture_root>/contexts/file_contexts.bin
```

Provide the query manifest externally pinned by the parent. It has exact fields:

- `schema`: `asus-sdk37-metadata-query-inputs/v1`.
- `scope`: `PARENT_CAPTURE_QUERY` for later real captured inputs, never a product-admission claim. Synthetic QA uses `FIXTURE_ONLY`.
- `binding`: exactly `build_id`, `complete_sha256`, `source_binding_sha256`, `installed_content_receipt_sha256` for the parent scope. These must be genuine independent parent bindings, not invented success receipts. The query validates digest syntax but does not inspect/select the actual complete/raw artifact; v5 owns authenticating these references.
- `capture_root`: real canonical absolute directory; `native_target_out`: actual absolute native origin, recorded for binding, never opened by this query.
- `search_slots`: six rows in the fixed order above. Each row is exactly `{slot,state,sha256}`. `state:present` requires the exact binary-file digest; `state:absent` requires explicit `sha256:null`, actual capture absence and absolute-host-fallback absence. Empty files are present valid files; absence is never inferred or filled with empty data.
- `contexts`: exactly `{format,sha256}`. Use `format:compiled` and the final binary for production coherence. The directory must contain only `file_contexts.bin`, with no text alternative or sidecars. Explicit `format:text` is supported for tool diagnosis/qualification, not a substitute for the final compiled-context gate.
- `tool_group_sha256`: the exact qualified group digest above.

No filled production manifest, production metadata or admission template was emitted. The v5 owner must reconcile these new source roles with its strict parser after receiving this handoff; this unit does not edit v5, kits or the previous observer interface.

## Smallest guarded future command

Once the parent supplies those **actual admitted captures and externally pinned manifest**, execute one serial query into a fresh owned directory:

```sh
R=/srv/android/asus-sdk37-host-metadata-resolvers-20261106
python3 -B "$R/scripts/query.py" \
  --inputs "$PARENT_METADATA_QUERY_INPUTS" --pin "$PARENT_METADATA_QUERY_INPUTS_SHA256" \
  --output "$R/queries/v5-real-capture-01"
```

The interface fixes four public queries and accepts no arbitrary command or file-target list. It opens only ordinary real pinned metadata files, validates complete binary record framing, rejects unadmitted alternatives/sidecars and native diagnostics, captures both native stdout/stderr/exit values, and checks input identities after resolution. Result exit 0 means a source-bound query succeeded; exit 2 means refusal. No partial or failed native output becomes `result.json`. Diagnostic stdout/stderr may remain for a failed run.

The result's `files` values come solely from native SDK37 API output. Zero capability explicitly yields `capability_xattr_v2_hex:null` (absence); nonzero is the 20-byte revision-2 effective permitted mask, with zero inheritable words, confirmed against SDK37 e2fsdroid source and the actual capability ABI header. The actual e2fsdroid source skips capability-xattr creation for a zero mask; it does not delete a pre-existing capability xattr. Absence is the expected fresh-creation result and still requires the later real-image check. This is representation qualification; no privileged host xattr writes or capability execution occurred.

The parent then publishes genuine resolver execution receipts binding this result, exact raw stdout files, native exit 0, source/tool/dependency group, input manifest and independent coherent complete/source/content receipts. Only after that separate parent action may metadata enter the full-SYSTEM observer admission. This query result always says `production_admission:false` and `genuine_product_group_claimed:false`.

## Bounds and remaining gates

Each process has one CPU affinity, 1 GiB address-space cap, 60 CPU seconds and a 90-second wall alarm. Native calls have a 30-second timeout as well. Output files are capped at 16 MiB; metadata files at 1 MiB, contexts at 4 MiB. This owned unit has a 256 MiB unique-file storage cap, including preserved attempts; current use is recorded in evidence. No parallel compilers/tests, network fetch, privileged operation, product image selection or build/process inspection occurs.

Remaining gates are actual successful completed native/host validation, coherent real metadata/contexts/overrides/installed inputs, parent/v5 schema integration and admission, then the separately authorized actual SYSTEM header/guest-mount/final-host checks. No observer image, SYSTEM runtime, hardware, physical boot, flashing readiness or GO follows from reusable host tool qualification.
