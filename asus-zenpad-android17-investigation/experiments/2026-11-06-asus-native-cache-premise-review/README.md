# Selected native-cache acceptance premise — independent review

Question: can completed R8 native executions legitimately satisfy selected compiler/linker provenance without rows in the current `.ninja_log`, and what is the smallest sound next native action?

Status: review complete. **Recommend accepting the selected R8 execution lineage under ordinary controlled incremental-build trust. Do not require an output timestamp newer than a new attempt, or membership in its current `.ninja_log`.** This is a methodology finding, not parent acceptance of an R9 cache, kit, or launch. No build or validation engine was run here. No active R9, process-state, worker-progress, or device reads were made. All remote source/out/log/cache operations were read-only. The separately parent-accepted WebView input is a given.

Important outputs: [relational-lineage.json](evidence/relational-lineage.json) contains the exact joins; [frozen-exact-commands.json](evidence/frozen-exact-commands.json) retains complete successful native commands, their original verbose line numbers/whitespace, frozen metrics, and old Ninja rows; [selected-cache.json](evidence/selected-cache.json), [selected-deps.json](evidence/selected-deps.json), [archive-native-record.json](evidence/archive-native-record.json), and [selected-soong-modules.json](evidence/selected-soong-modules.json) contain bounded metadata extracts. [selected-elf-identity.json](evidence/selected-elf-identity.json) records ELF identities. Public implementation sources and their URL/SHA256 index are under [public-source](evidence/public-source/index.json). [QA.json](evidence/QA.json) records the checked relations and local evidence pins.

Continuation: give these findings to the parent. Reuse authenticated R8 evidence as R8 evidence. Let the next parent-controlled required native target closure decide whether actions remain up to date; retain all final product checks. Do not execute archived commands, manufacture log rows, touch sources, clean, force rebuild, or treat this review as build/flash/runtime authorization. Read-only extraction scripts are evidence fixtures, not a continuation kit.

The decisive findings are:

1. The baseline's requirement that every selected output occur in the *current* log is incompatible with the actual Siso logging implementation. `compiler_channel.commands_for()` additionally discards a frozen command unless its frozen row equals the current row; `verify_product_r3.execution_record()` then demands current-log presence and, for bpfloader/vold/sensors, fresh attempt timestamps. Those are extra validator policies, not Siso cache rules. Replacing that join with authenticated selected native lineage preserves evidence rather than relaxing compiler correctness.
2. Frozen R8 first-phase success is real: receipt `0e06bbee948f7413eaa0b54f6be95d8374750c0ece2646526864733ea6204660`, exit 0. It requested both `bpfloader` and `vold`, and recorded local compiler/linker execution, exact output paths, command hashes, timings, and old Ninja rows. The second phase exit 1 is the parent-reviewed WebView failure; it does not erase first-phase success or establish whole-product success.
3. All seven selected current output bytes match their native HashFS content digests; all seven native command hashes equal the hashes in immutable first-phase metrics. Exact compiler/linker command plus retained response-file content independently reproduces the native SHA256 command hash for PublicVolume compilation, bpfloader compilation/linking, and vold linking. The stripped variants also match. The selected libvold archive has a matching native digest and a frozen execution/metric record.
4. These relations support standard incremental trust, not unconditional historical input-byte proof. The selected local native records have no action digest/input-tree attestation. Neither metrics counts, edge hashes, command hashes, nor later source/toolchain hashes reconstruct all historical inputs. That stronger proof is unavailable in the reviewed capture. It is also not a prerequisite of a normal incremental Android build using a controlled source tree and the real engine's dependency validation.

The actual Siso implementation is pinned by `prebuilts/siso/siso.ensure` and `.versions` to Chromium build commit `342ffcda73fb0acb5666792b95c00efc32b47318`; frozen metadata identifies v1.5.8. The currently read executable SHA256 is `f29c34711c7d18ce28126dcf6e6e0054517f82bb43807ee285ab0085513826b7`. The version-to-commit mapping is a checked-in prebuilt declaration, not an independently reproduced binary provenance proof.

[`build_ninja.go` lines 50–64, 91–99](https://chromium.googlesource.com/build/+/342ffcda73fb0acb5666792b95c00efc32b47318/siso/build/ninjabuild/build_ninja.go) initializes the compatibility log for the manifest's builddir. [`ninja_log.go` lines 25–47](https://chromium.googlesource.com/build/+/342ffcda73fb0acb5666792b95c00efc32b47318/siso/toolsupport/ninjautil/ninja_log.go) opens it with `O_TRUNC` and writes FNV64 hashes of command arguments. [`run_step.go` lines 82–104](https://chromium.googlesource.com/build/+/342ffcda73fb0acb5666792b95c00efc32b47318/siso/build/run_step.go) records metrics/log rows for non-skipped steps, including failures. Thus a later phase can legitimately omit successful cached steps from the current log. A failed phase's row alone is not proof of success; here the selected actions have a successful enclosing phase and non-error metrics.

[`builder.go` lines 935–953](https://chromium.googlesource.com/build/+/342ffcda73fb0acb5666792b95c00efc32b47318/siso/build/builder.go) passes step end time as the log's third field, with an explicit pending compatibility issue. It need not equal the output's filesystem mtime. Do not compare those fields for exact equality or reinterpret the FNV64 value as Siso's native SHA256 command hash.

[`mtimecheck.go` lines 55–179](https://chromium.googlesource.com/build/+/342ffcda73fb0acb5666792b95c00efc32b47318/siso/build/mtimecheck.go) uses outputs, trigger/dependency inputs, mtimes, command hashes, edge hashes, and local availability. [`graph.go` lines 188–211](https://chromium.googlesource.com/build/+/342ffcda73fb0acb5666792b95c00efc32b47318/siso/toolsupport/ninjautil/graph.go) hashes the expanded command, then byte `0x1f` plus nonempty response-file contents. [`step_manifest.go`](https://chromium.googlesource.com/build/+/342ffcda73fb0acb5666792b95c00efc32b47318/siso/build/step_manifest.go) hashes ordered input/output paths and sandbox mode separately; that is not a hash of dependency contents. This review did not imitate or run the complete native dirty-check algorithm.

Dependency availability is specific to the action:

- PublicVolume: `.siso_deps` is legacy Ninja dependency format v4. Its selected entry lists 1,032 dependency paths including `system/vold/model/PublicVolume.cpp`; recorded output mtime and actual object mtime both equal `1794007844976817385`. The list has no per-input digest, and it is a current retained record, not a frozen first-phase dependency snapshot.
- bpfloader Rust: the retained `.../unstripped/bpfloader.d` names `system/bpf/loader/bpfloader.rs`; the graph rule uses a depfile, not `deps=gcc`. The `.soong_deps` source list also survives. A path entry without a `.siso_deps` dependency record is expected here.
- vold linking: the graph has static trigger inputs and `${in} ${libFlags}` response content, with no compiler-style dependency log requirement. The selected graph directly relates PublicVolume.o to libvold.a and libvold.a to the real vold linker output. The retained linker response file is available. A link step need not have a compiler depfile.

[`step_def.go` lines 443–547](https://chromium.googlesource.com/build/+/342ffcda73fb0acb5666792b95c00efc32b47318/siso/build/ninjabuild/step_def.go) selects the appropriate dependency mechanism. [`deps_log.go` lines 65–91, 201–215](https://chromium.googlesource.com/build/+/342ffcda73fb0acb5666792b95c00efc32b47318/siso/build/ninjabuild/deps_log.go) validates a dependency record using output mtime, or a stored output digest when available. The current legacy record has no digest. The unrelated `out/.ninja_deps` is only a 16-byte header; the relevant populated file is `out/.siso_deps`.

The selected state fields come from [`hashfs/proto/state.proto`](https://chromium.googlesource.com/build/+/342ffcda73fb0acb5666792b95c00efc32b47318/siso/hashfs/proto/state.proto): file identity/mtime, name, content digest and size, command hash, edge hash, action digest, updated time, and local flag. For these selected generated files `local=1` and `action` is absent. A digest of an output identifies output bytes; it does not identify every input consumed. Metrics `inputs` is a count, not an input manifest. There is no basis for treating these local records as a retained REAPI action/CAS input-tree proof.

What was recorded before execution, and what was only captured afterward:

- **Before native execution:** sealed kit scripts/inputs and selected external pins; reviewed platform source pre/postimage pins; actual `attempt/postimages.json` checks of the integrated selected platform sources and other selected sources; `integration.json` binds that postimage receipt, selected source receipts, kernel/config identities, and exactly two R8 source writes. The supervisor applies/checks sources before invoking the build script. The selected bpfloader and PublicVolume postimage pins already existed before this compile, rather than being invented from today's hashes.
- **Before native execution, limited scope:** selected Soong implementation and selected Android.bp files are external-pinned. Kernel/source/supplement archives and receipts are sealed inputs. This is not an archive of all AOSP compiler dependencies or all active compiler executables/libraries.
- **After each phase:** `capture_build_evidence.py` freezes verbose output, `.ninja_log`, metrics, metadata, localexec/output logs, and failure commands if present. Its receipt binds the already existing started/integration receipts. It does not freeze `.siso_fs_state`, `.siso_deps`, generated graphs, every output digest, or an input tree. The first-phase metrics contain command hashes, action identities, timing, counts, and error state, not output content digests.
- **At this review:** selected current HashFS/dependency records, content hashes, ELF identities, retained response/depfiles, and selected generated graph snippets. Main and selected shard stat observations were stable across their bounded reads; this is not an atomic whole-tree snapshot. Current graph/tool hashes do not become preexecution hashes by being written into this review.
- **Mutation history:** R8's `integration.source_writes` records the WPA diagnostic-boundary fix and exact zRAM file-context addition. Preserved ancestor receipts and selected source guards establish the intended controlled cohort. This is not a comprehensive OS mutation journal proving absence of every possible write. Use the actual custody model: trusted native state, ordinary source editing metadata, preserved outputs, reviewed mutations, and the real engine's dependency decisions. The user-supplied later cleanup fact changes no source/out/cache bytes and is not independently inspected here. No R9 mutation scope or acceptance is inferred.

Selected source pins, also found in preexecution `postimages.json` and today's matching native source entries:

- `system/bpf/loader/bpfloader.rs`: `babbccf603e600a2b77f5c71cbf6b1b978f72c176fd33bfab610ff2ba8956250`.
- `system/vold/model/PublicVolume.cpp`: `c5147ca901fb1c4678b34c6727e63eb325e1ad21de2cdcbcb19b8cf9af1d49c9`.

The native source entries/current source hashes agree, but only the preexecution receipt plus controlled custody supports an inference about historical source identity. Today's tool hashes match today's native input entries: `clang-r584948b/bin/clang++` = `15261046b6ea9504da0ae57b9d65ebc869ab1942aecb1af2819762b9b5251957`; Rust `1.93.1/bin/rustc` = `ae9a00cb9f8af573e88027ee8c598842b5df68c029948e954cde7fae89db7b7d`. These are not a before-execution seal of the complete compiler, wrapper, linker, sysroot, shared libraries, and implicit inputs.

The minimal acceptance predicate has two separate scopes:

`R8_EXECUTION_LINEAGE(output)` holds when the frozen receipt matches the parent-reviewed phase receipt; the started/integration bindings and captured file hashes match; a selected non-error execution metric and exact successful command identify that output; its frozen Ninja row corroborates the same phase; native state identifies the same output and metric SHA256 command hash; observed output bytes/size match its native content digest; selected graph/depfile records show the intended source/module relation; reviewed selected source pins and the controlled source/native-cache custody model hold. Record exact evidence locations and assumptions. This is satisfied for the selected compiler/linker records documented here under that standard trust model. It says neither "every past input byte independently attested" nor "current entire product up to date".

`FINAL_CURRENT_ACCEPTANCE` additionally needs successful real native validation of the required targets under the admitted current product/source configuration, with any dependency changes handled by the engine, and every retained compiler/linker/ELF ABI, sensor/WPA/source, selected 26 BPF, Google/APEX, kernel, image/container/installed-payload, policy/config, and product check. A skipped unchanged action may use `R8_EXECUTION_LINEAGE`; a rebuilt action must use its real new native execution/evidence. No fabricated log row, timestamp renewal, or blanket cache exception belongs in either predicate.

An exact proposed record shape (a specification, not an installed validator or parent acceptance) is:

```json
{
  "schema": "selected-native-lineage/v1",
  "output": "exact native output path",
  "trust_model": "controlled-tree/native-incremental",
  "frozen_phase": {
    "receipt_path": "exact frozen receipt path",
    "receipt_sha256": "sha256",
    "attempt_started_sha256": "sha256",
    "integration_sha256": "sha256",
    "phase_exit": 0,
    "verbose": {"archive_sha256": "sha256", "line": 0, "exact_command": "including trailing whitespace"},
    "metrics": {"file_sha256": "sha256", "line": 0, "step_id": "id", "output": "same path", "cmdhash_hex": "sha256", "err": false},
    "ninja": {"file_sha256": "sha256", "line": 0, "raw_v5_row": "original row"}
  },
  "native_state_observation": {
    "path": "out/.siso_fs_state",
    "entry_name": "absolute native path",
    "mtime_ns": 0,
    "updated_time_ns": 0,
    "digest": {"hash": "sha256", "size_bytes": 0},
    "cmd_hash_hex": "sha256",
    "edge_hash_hex": "sha256",
    "action": null,
    "local": true
  },
  "current_artifact": {"sha256": "equals native digest", "bytes": 0},
  "dependency_evidence": {"kind": "gcc-depslog | depfile | graph-and-rsp", "location": "exact record", "historical_input_tree_attested": false},
  "source_identity": {"path": "selected source", "reviewed_postimage_sha256": "sha256", "preexecution_receipt_sha256": "sha256", "observed_sha256": "sha256"},
  "graph_observation": {"path": "selected graph shard", "offset": 0, "selected_text_sha256": "sha256", "preexecution_full_graph_pin": null},
  "current_native_target_validation": null,
  "acceptance_scope": "R8 execution lineage only; final current product checks pending"
}
```

The irreducible stronger gap is an independently retained execution-time mapping from each action to all consumed input bytes/toolchain/graph/environment, with trustworthy custody through the attempt. Later hashes cannot supply it. An ordinary native target check validates the current build; it cannot retroactively create that historical attestation. A genuine isolated selected compiler reproduction can establish a new current-source compilation result if independently needed, but it is not historical repair and does not replace product linking/packaging checks.

The smallest next action is therefore **reuse this R8 lineage and continue the parent's already required incremental product build/check with the exact admitted WebView input**, letting actual Siso validate the selected installed targets as part of the required `systemimage` closure. No extra recompile is justified solely by missing current rows or old mtimes. If a product invocation cannot establish that selected closure, the bounded fallback is a parent-controlled ordinary selected `bpfloader vold` native target/evidence phase, allowing a legitimate no-op. That action renews current native validation without forced freshness. Nothing in this review executes or approves either action.

This advances the real Android17 build by removing a false evidence-channel blocker while preserving actual native cache validation and all final product requirements. Full R8 product success remains false; host acceptance and device/flash/runtime GO remain pending.

Exact selected artifacts are relative to `/srv/android/lineage24/`. Their current bytes match native stored digests; the metric line is within frozen first-phase `siso_metrics.json`:

| Exact output | SHA256 | Frozen metric line |
|---|---|---|
| `out/soong/.intermediates/system/bpf/loader/bpfloader/android_arm64_armv8-a/unstripped/bpfloader` | `1d4c5429a7edadf848e8ff1128a73054411ea67a23422927a9bb215e0eb0c880` | 23 |
| `out/soong/.intermediates/system/bpf/loader/bpfloader/android_arm64_armv8-a/bpfloader` | `b6a9888e623a44cea98ead533c304225d6ef2e63237ee1769857087cfb1f2737` | 628 |
| `out/soong/.intermediates/system/vold/libvold/android_arm64_armv8-a_static/obj/system/vold/model/PublicVolume.o` | `88ef0d802e89e3c90946beb171dab0e79faa4713d291f58648c0e4a4b31253ba` | 13 |
| `out/soong/.intermediates/system/vold/vold/android_arm64_armv8-a/unstripped/vold` | `18daecc22adf923e2ac1c9a4401357238c314704360b89df301e00bf5e8baee2` | 840 |
| `out/soong/.intermediates/system/vold/vold/android_arm64_armv8-a/vold` | `74b1e39da028cb71505681ba648bc1f51b640d6cd47f018d5a26c202aca662b7` | 843 |
| `out/target/product/p00a/system/bin/bpfloader` | `b6a9888e623a44cea98ead533c304225d6ef2e63237ee1769857087cfb1f2737` | 666 |
| `out/target/product/p00a/system/bin/vold` | `74b1e39da028cb71505681ba648bc1f51b640d6cd47f018d5a26c202aca662b7` | 844 |

The three critical successful command records and original Ninja rows are below. Full command strings are in `evidence/frozen-exact-commands.json`; no ellipsis or reconstructed command is substituted there. The vold linker command has one trailing space, which is significant to Siso’s command hash.

- `out/soong/.intermediates/system/bpf/loader/bpfloader/android_arm64_armv8-a/unstripped/bpfloader`: verbose line 1720 (`[62/34686]`), step `d0c5c9eb-2d52-4409-b86f-3bd5ad7c104a`, native command SHA256 `9e54e72854dcf61a4b87081d1bd1c1e4fd84bd41850a65b9d267383e82a8d0bd`. Original Ninja line 24:

```text
25401	30570	1794007852067286981	out/soong/.intermediates/system/bpf/loader/bpfloader/android_arm64_armv8-a/unstripped/bpfloader	67826fc8b082dd13
```

- `out/soong/.intermediates/system/vold/libvold/android_arm64_armv8-a_static/obj/system/vold/model/PublicVolume.o`: verbose line 1684 (`[52/34686]`), step `6795b57d-7bef-41db-a79b-9cc552caefc1`, native command SHA256 `3bb6a30e4d40c69b1a75616ffb0430e80646dd90a350e876a22a40700cbc284c`. Original Ninja line 14:

```text
20272	23497	1794007844994910744	out/soong/.intermediates/system/vold/libvold/android_arm64_armv8-a_static/obj/system/vold/model/PublicVolume.o	1ab3fb4f98888761
```

- `out/soong/.intermediates/system/vold/vold/android_arm64_armv8-a/unstripped/vold`: verbose line 4492 (`[879/34686]`), step `b1b27675-6287-4b9b-908c-ea4a9f1040df`, native command SHA256 `473cc53a9cb5053b9d557484d7d80b52455bd5a487f7313220725c0952f30e38`. Original Ninja line 841:

```text
76670	89474	1794007910971403106	out/soong/.intermediates/system/vold/vold/android_arm64_armv8-a/unstripped/vold	85aa1dc74b19b2ce
```

Additional binding pins:

- `/srv/android/asus-reviewed-build-kit/r8/attempt/started.json`: `6433c36ca34cfb8c19027aa8ff83560513d390786d640e085364144ae381b0f5`.
- `/srv/android/asus-reviewed-build-kit/r8/attempt/integration.json`: `eb3bea76da122ed3218821acdd5c72a1e20f5cf5cf1c9c485587399ebc095b03`.
- `/srv/android/asus-reviewed-build-kit/r8/attempt/postimages.json`: `b547f9edec69378c95af0f7c50b1547f2bf3eb1bff66e93d199a7975d72632ed`.
- `/srv/android/asus-reviewed-build-kit/r8/attempt/preservation.json`: `b563ef8c5daac9258a8e4caf06db7e5143aa1bde1ffe3273088d17043d69e9a2`.
- `/srv/android/asus-reviewed-build-kit/r8/attempt/product-config-paths.json`: `2aa822ee8ffd85e4b0dfd8e2b6f59923273da87ba470017ea93ff8d61de7c8b7`.
- First-phase metrics: `3fd0fe506dbdc152e276074cb4bdb503fe8959ce5064ff8997ed7d8aaef76e1d`; verbose archive: `8c64913c7d18bfceedc4847515d545c44f294e2e3521342312959523ad6bab90`; old Ninja log: `dd00f04ea0ad4170cbda2d4e784733baa7908bcb9cdd6d643fee01888fadf329`.

Resource/ownership note: SSH operations ran Python with one CPU affinity, 1 GiB address-space limit, 45 seconds CPU and 55 seconds wall per bounded read. No remote fixture or output was created. Only selected metadata/source extracts and selected small artifacts were hashed. HashFS and dependency databases were streamed with selected records retained; no global graph index was built and no all-14 graph rehash/copy occurred. Selected module excerpts were found by bounded seeks into their alphabetically sorted shards. Local outputs remain wholly under this dated review directory.
