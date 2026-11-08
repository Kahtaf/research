# Required parent producer contracts

No genuine instance of these new parent contracts was supplied or created in this preparation. JSON examples with invented production success are deliberately absent. The executed parser in `scripts/admission.py` is the normative field/type validator. All references below are exactly `{path: absolute ordinary file, sha256: lowercase 64-hex digest}`; duplicate JSON keys, unknown fields in the defined schemas, missing fields, symlinks and mixed groups are rejected. Receipts are bounded to 1 MiB; captured source/stdout files to 4 MiB.

## Trust and coherent group

The external trust root is the **parent's independently reviewed and published admission SHA256**, supplied as `--admission-pin`. Computing a hash of an unreviewed bundle does not admit it. The parser checks the attested group and its immutable artifacts; it cannot authenticate who wrote an arbitrary JSON file. Parent must attest real terminal evidence, immutable output identity, independent installed-content origins, and real source-resolution execution. Candidate image extraction alone is never an expectation producer.

Parent admission exact fields:

- `schema`: `asus-fs-parent-admission/v1`.
- `scope`: `GENUINE_COMPLETED_PRODUCT`; `decision`: `ACCEPT_COHERENT_PRODUCT_INPUTS`.
- `build_id`: one stable identifier, shared by all new receipts.
- `kernel_sha256`, `config_sha256`: exact c59e/0426746d pins from the accepted mechanism.
- Pinned references `complete`, `terminal`, `source_binding`, `public_content`, `resolved_metadata`.

`complete` is the actual successful `validate_completed_product.py` `complete.json`, preserving its existing fields. Required fields include true `elf_init_policy_neverallows_vintf_apex_host_checks_passed`, `source_system_sha256`, and `raw_system.{path,bytes,sha256,all_zero_ranges_written}`. Raw size is 3,753,902,080; materialization flag true. The raw file must be an immutable, unwritable ordinary sibling of that `complete.json`. No `--raw` option can replace it. A fixture completion or failed r8 is ineligible.

`terminal` requires schema `asus-native-host-terminal/v1`, genuine scope, shared `build_id`, `sdk:37`, actual integer-zero `build_exit_code` and `host_validation_exit_code`, `complete_sha256`, `source_binding_sha256`, and nonempty `native_phase_receipts` pinned references. Parent must produce it from the real terminal native phases and host validator, not create it from this fixture's exits. This new binding receipt is presently missing; the old r8 WebView failure cannot satisfy it.

## Public source binding

`source_binding` exact fields: `schema:asus-fs-source-binding/v1`, genuine `scope`, `build_id`, `sdk:37`, `capture_root`, `source_roles`, explicit `fs_config_overrides` reference list (including explicit empty inventory when verified), `raw_identity`, `system_image`.

All public sources are frozen copies beneath `capture_root`. Each source role is `{path,sha256,source_path}`; `source_path` records its real origin but only `path` is opened. Required roles:

- `plan`: the admitted later kit's actual plan. Its `aosp`, `device`, `product_out` resolve the other real source paths.
- `boardconfig`, `build_image`, `mkuserimg`, `mke2fs_config`, `fs_config_cpp`, `platform_file_contexts`, `product_file_contexts`.
- `system_rule`: exact generated SYSTEM Ninja stanza, with its actual graph origin under the plan's AOSP out root. Capture a bounded stanza, not a multi-gigabyte graph export.
- `system_image_info`: the actual completed `obj/PACKAGING/system_intermediates/system_image_info.txt` produced by that SYSTEM rule.

The three creation Python/config hashes must match the qualified selection; changing them requires review/new qualification. The parser checks ext4, full partition size, mkuserimg selection, sparse flag, actual root/context paths, and rejects shared-block/journal changes. The final raw/sparse header must independently match the qualified feature profile. Neither a BoardConfig guess nor a fabricated SYSTEM property file satisfies this contract.

`product_file_contexts` is the coherent final compiled `obj/ETC/file_contexts.bin_intermediates/file_contexts.bin`. Capture all actually consumed binary fs_config overrides (system/vendor/product/system_ext/odm as applicable) and freeze them in a layout that the real `fs_config` implementation searches through the supplied TARGET_OUT. Capture none only after verifying no overrides were consumed. The metadata receipt pins this inventory's canonical JSON digest. No source/out reads occur in this preparation; these copies belong to the future parent capture.

`raw_identity` is `{dev,ino,bytes,mode,mtime_ns,ctime_ns}` from the final admitted raw artifact after the parent makes it unwritable. `system_image` is `{path,sha256,identity}` for the genuine completed raw/sparse product image; its digest must equal `complete.source_system_sha256`. The image digests stay external and fixed; this interface does not recompute them. Both identities are checked before and after use.

## Independent content and metadata expectations

Only these four public paths may appear, in canonical order:

```text
/system/build.prop
/system/bin/init
/system/bin/run-as
/system/vendor/etc/selinux/vendor_file_contexts
```

Freeze those actual installed output bytes under `capture_root/installed/<path-without-leading-slash>` from the same host-validated group. They must be regular files reached without symlinks. Each file is limited to 16 MiB, total 32 MiB. Do not populate this tree by extracting the candidate image. Parent must attest the installed-output capture's relationship to its terminal product/source group.

`public_content` exact fields: `schema:asus-public-content/v1`, genuine scope, `build_id`, `complete_sha256`, `source_binding_sha256`, `producer:coherent-installed-public-output-capture`, and exactly four `files`, each `{path,bytes,sha256}`. Bytes and SHA256 come from those frozen installed bytes.

`resolved_metadata` exact fields: `schema:asus-resolved-public-metadata/v1`, the same scope/build/complete/source fields, `producer:fs_config+selabel_lookup`, `fs_config_cpp_sha256`, `product_file_contexts_sha256`, `fs_config_overrides_sha256`, `resolver_tools:{fs_config,selabel_lookup}` (actual tool digests), exactly one `resolution_receipts` pinned reference, and four `files` records `{path,uid,gid,mode,capability_mask,selinux_label}`. All numeric fields are actual integers, never booleans or omitted defaults. Mode is permission bits. Label includes the real context without NUL; the generator adds the on-disk NUL. Capability mask is the resolved 64-bit mask; zero explicitly means the capability xattr must be absent. Nonzero becomes the genuine revision-2 effective capability xattr with zero inheritable words.

`resolution_receipts[0]` exact fields: `schema:asus-public-metadata-resolution/v1`, same scope/build/complete/source fields, the three source/inventory hashes above, identical `resolver_tools` and `files`, actual integer-zero `fs_config_exit_code`, `selabel_exit_code`, and `stdout:{fs_config,selabel_lookup}` pinned references. Values must exactly match the metadata and these canonical four-line outputs:

```text
/<fixed-relative-path> <uid-decimal> <gid-decimal> <four-digit-octal-mode> capabilities=<lowercase-0x-mask>
/<fixed-relative-path> <actual-SELinux-context>
```

No shell command or target list is accepted from a receipt. `source/resolve_fs_config.cpp` and `source/resolve_contexts.c` implement the fixed host queries for later compilation against **admitted SDK37** libcutils/libselinux. The former calls the real fs_config API using the coherent frozen TARGET_OUT and override layout; the latter performs regular-file selabel lookups using the captured final context stem, base-only. Place the admitted compiled contexts at `<stem>.bin`, pin all consumed context files, and exclude unpinned sidecars. Preserve actual argv, stdout, exit, compiler/linker/tool/dependency hashes and source bindings in the resolution producer receipt.

Those host resolver build/execution receipts and coherent SDK37 host libraries/headers were not supplied to this task. The helper source is prepared but has not been compiled or executed against a genuine product. Parent owns producing that missing contract; no current fallback, guessed run-as label, debugfs-derived expectation, or synthesized native success is provided. The final run-as values must come from these actual resolutions, including overrides; the synthetic run-as label `runas_exec` is not an admitted production expectation.

`capture_expectations.py` consumes pinned genuine complete/source/resolution receipts, streams only the four frozen installed files, verifies metadata against resolution values/stdout, and publishes `capture_root/expectation-receipts/{content,metadata}.json`. It never opens the candidate image and emits no observer header. The parent must still review and publish the final admission referencing these exact new receipts. This publisher refused the fixture completion during QA.

## Synthetic separation

Fixture documents use scope `FIXTURE_ONLY`, decision `FIXTURE_TEST_ONLY`, a separate fixture terminal schema and formatter/fsck status fields, and an explicitly fixture-only completion without a fabricated native host-success flag. Their producer names and resolution schema differ from production. Production rejects all such inputs before reading image artifacts, including attempted scope retagging; known old/new fixture namespaces cannot be production raw/source captures. The fixture caller is confined to `tests/`; the production CLI has no fixture-mode switch.
