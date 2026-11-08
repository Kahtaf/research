# Exact official runtime capture

Question: can the parent select and freeze one coherent official Android17 runtime input revision after an exact qualified terminal build, without changing source/out or silently substituting variants?

Status: implementation prepared for parent review and execution. Only synthetic offline captures are tested. **No real official-output selection/capture or availability check has run.** r7 was active when this task was assigned. No runtime, full OS, APEX/keystore/adbd, or physical readiness is asserted.

Owned local spike: this directory. Owned VM prefix: `/srv/android/asus-official-runtime-capture`; executable preparation: `preparation-v2`; fresh results: `snapshots/<name>`. The parent owns device, builds, integration and execution. No prior runtime fixture, capture directory, source/out file, build, active job or device is modified.

Important outputs:

- `source/capture.py`: default static plan, then separate select, verify and copy operations.
- `inputs/profile-r7.json`: exact kit r7 seal `9287a07d243a9d70abefa0102de160d88af712a574c7fab6032ce9b36920f617`, supervisor1560115, child1560446, original lock inode15018964. These came from the fixed sealed kit/launch metadata, not an active-progress check.
- `inputs/selector.json`: exact required installed outputs, complete selected metadata trees, ELF roots, native graph scope, property generators and signed runtime source edge. Runtime source remains the actual `android_common_hwasan_com.android.runtime` edge; this label makes no device sanitizer assertion. Genuine `out/soong/soong.variables` is captured separately.
- `manifest.schema.json`: compact manifest contract; runtime source/copy hash validation also runs in the CLI.
- `tool-pins.json`: preparation seal. Keep its SHA256 outside this directory (see HANDOFF).
- `tests/test_capture.py`, `evidence/linux-offline-tests.json`: synthetic fault and resource evidence. Initial local test logs are preserved separately.

## Parent continuation

First read REPORT/HANDOFF and independently establish a genuinely successful qualified terminal r7. Do not invoke select while the build is active. The default command only prints a plan; it does not inspect source/out, acquire a lock, or imply eligibility:

```sh
python3 -B /srv/android/asus-official-runtime-capture/preparation-v2/source/capture.py
```

After terminal qualification, choose unused names. These operations fail immediately on a live native job or held original lock; there is no wait, retry, restart, failed-build acceptance flag, readiness flag or automatic fallback:

```sh
python3 -B /srv/android/asus-official-runtime-capture/preparation-v2/source/capture.py select --name select-r7-001
sha256sum /srv/android/asus-official-runtime-capture/snapshots/select-r7-001/selection.json
```

Read `selection.json` and `COMPLETE.json`; review its exact kit, terminal/source/configuration pins, graph commands, missing optional paths, package/source equality, complete policy set, symlink metadata, architecture/DT_NEEDED candidates and size limits. The hash printed by select is also in COMPLETE. Pin the exact 64-character hash externally; use it in place of `SELECTION_SHA256` below. This is an exact content pin, not an affirmative approval flag.

```sh
python3 -B /srv/android/asus-official-runtime-capture/preparation-v2/source/capture.py verify --name verify-r7-001 --selection /srv/android/asus-official-runtime-capture/snapshots/select-r7-001/selection.json --selection-sha256 SELECTION_SHA256
python3 -B /srv/android/asus-official-runtime-capture/preparation-v2/source/capture.py copy --mode PARENT_EXECUTE --name capture-r7-001 --selection /srv/android/asus-official-runtime-capture/snapshots/select-r7-001/selection.json --selection-sha256 SELECTION_SHA256
```

The wrapper is `../2026-11-06-asus-product-input-build-kit/scripts/remote.py`; import its `run(script)` to execute these exact argument vectors through Python `subprocess.run(..., check=True)`. The wrapper has no CLI command forwarding interface. `source/upload.py` only installs preparation into its fresh prefix; rerunning it refuses an existing prefix.

Only a completed **select** directory can supply the pinned selector receipt to verify/copy. Each operation creates a fresh exclusive directory. Failures preserve STARTED, journal, partial copies, graph index and FAILED. A crash without COMPLETE is incomplete. Never resume, repair, reuse or overwrite any failed or successful directory. Fix a proven preparation limitation in a new reviewed preparation revision, or make a separately reviewed future profile/selector with explicit exact hashes. Nondefault contracts must be under preparation and supplied with `--profile-sha256` / `--selector-sha256`; there is no force option. A future profile must name its actual sealed kit, PIDs, lock inode, configuration and compatible terminal receipt schema. Do not change r7 to accept failed or missing terminal evidence.

## Selection and copy boundary

Required official files include the platform BoringSSL32/64 ELFs, runtime APEX, adbd CAPEX, actual installed system/system_ext/product build.props, aggregate apexkeys, genuine selected services, binary policy, split CIL/mappings/contexts and VINTF. Init, linkerconfig, SELinux, VINTF and public trust metadata trees are selected as groups. Missing optional directories are explicit; errors and required missing/partial files stop. Unrelated unbuilt artifacts outside the chosen generation/runtime dependency closure are not requirements.

No Ninja/AOSP command or selected build command is executed. A bounded read-only SQLite index records the actual native edge/rule/global-variable text, full graph hashes and line locations. Ordinary installed file bytes must equal their exact native install-edge source. Selected metadata generator dependencies are hash-bound, with small generated metadata also copied. The exact gen_build_prop/post_process_props tools, API fingerprint, actual product_config JSON, generated properties and source-generation code are required. Native ELF install/link/strip evidence is recorded without copying alternative ELFs as installed files. Unknown/ambiguous selected edges or unsupported Ninja syntax stop. Phony ordering/tool tokens are distinguished from filesystem inputs. Private-key/image dependency path strings are recorded as excluded and never opened.

All regular selected files have identity, size and SHA256. Captured payload files have before/copy/after hashes. The entire selected group, source integration, directory inventories, absent optional paths, terminal receipts, graph inventory/content and lock/native absence are checked again before COMPLETE. Existing empty generated context files are allowed and still require exact official source-edge equality; empty binaries/packages/properties are partial errors.

Paths are canonical and descriptor-anchored with no parent symlink traversal. Leaf symlinks are explicit metadata, never implicit file reads. Safe relative installed links resolve only within installed system paths; narrowly selected host-tool/prebuilt relative links stay inside AOSP. Absolute package references are recorded with `extracted:false`. No host `/apex` link is evidence of extracted contents. An optional i18n dependency selects exactly one actual installed `.apex`/`.capex` authority; ambiguity or absence stops. Architecture/DT_NEEDED candidates are not a claim of final Android linker namespace resolution. Package candidates retain unknown payload architecture until extraction.

Signed installed packages and their exact native selected source hashes remain unchanged. ZIP structure is checked without extraction or resigning; signature/trust verification is deferred, never claimed here. Policy header version30 is checked. The binary policy and the **whole** corresponding installed CIL/mapping/context group, source policy directories and generator provenance form one new snapshot; do not mix them with the prior22:19 policy or a late supplement.

Limits: 8,192 files; 256 MiB per ordinary file; 3 GiB selected total including hash-only provenance and up to2 GiB log; 512 MiB per graph, 2 GiB graphs total; 2 MiB per graph block; 3 GiB graph index; 20,000 entries per enumerated directory; 8,192 selected edges; 16 MiB graph evidence; 64 MiB per JSON receipt and journal. All are finite hard ceilings. The CLI and Linux QA use one CPU and a 1 GiB address-space limit. Large payloads and graph indices remain on the VM. Export only JSON receipts, selected source/tool files and QA evidence; do not export `files/`, graph indices, full images or ELFs.

## Future Sol firstboot worker

Give the worker the new `capture-r7-001` directory, its selection/COMPLETE SHA256 pins and this handoff. Verify COMPLETE action=copy and final_group_source_recheck=true; verify every copied hash against selection and copy receipts before use. Materialized files are below `files/<root>/<source-relative-path>`; metadata-only symlinks and hash-only provenance have no materialized file. Original mode is `identity[2]`; restore intended executable permissions only in a new owned runtime revision. Do not overlay any prior input revision or reuse its policy files.

Use the captured genuine official deapexer/apexd_host provenance and actual VM host tools for **future** extraction into fresh owned storage, with bounded extraction and private/image exclusions; do not fabricate `/apex` contents from host links. Reverify unchanged package hashes, inspect actual package manifests/architecture and qualify trust, activation and namespaces separately. Retain genuine crypto/APEX waits and service ownership of readiness properties. Do not set readiness values, substitute Conscrypt `*_apex31`, guess sanitizer settings/variants, boot guests as part of capture, or claim a full service chain/physical GO from this snapshot.

The completed prior runtime handoff proved24 expected observations and145 exported payloads with enforcing init and functional manager IPC. It still fails at the missing mandatory official self-test. This preparation does not alter or extend that runtime qualification.
