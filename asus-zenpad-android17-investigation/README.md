# Reviving an ASUS ZenPad: Android 17 and Linux 4.9 investigation

**Status: parked on 2026-11-08.** We built experimental Android 17 / SDK37 system images and proved that a ported Linux 4.9 kernel executes on an ASUS ZenPad 8.0 Z380M/P00A_2. We did **not** establish stable physical kernel operation or install Android 17 into the tablet's normal OS partitions. The tablet returned to stock Android 7 after the final recovery-only trial.

The aim was to make a slow, low-memory MT8163 tablet useful again. The investigation began with stock-firmware and hardware research, expanded into an Android port, and ended at an unresolved physical runtime boundary. The owner chose to park Android17 and investigate a lighter Linux userspace using the working stock kernel. That replacement has not been implemented.

This folder preserves the useful knowledge, source changes and failed experiments without firmware images, upstream repositories, private device logs or factory data. Historical reports retain their original proof limits and may describe earlier, superseded beliefs. The documents below state the final assessment.

## Start here

- [Findings and resolved blockers](FINDINGS.md): what worked, why earlier attempts failed, and what remains unknown.
- [Failed experiments](FAILED-EXPERIMENTS.md): hypotheses, observations and the conclusions they do—and do not—support.
- [Process and lessons](LESSONS.md): how evidence improved, where the investigation drifted, and how to avoid repeating it.
- [Working notes](notes.md): reconstructed timeline plus the actual archival/cleanup work.
- [State and resume guide](STATE-AND-RESUME.md): external requirements and safe resumption boundaries.
- [Experiment ledger](EXPERIMENT-LEDGER.md): index of 391 separate local spikes. Folder ordering is not a precise within-day execution timeline.
- `remote/platform-diffs/`: actual final Git working-tree diffs from the Android source checkout.
- `remote/provenance/` and `SOURCE-PRESERVATION.json`: resolved upstream identities and the preservation scope.
- `manifest.json` and `publication-mapping.json`: original/export hash bindings, publication transformations and selection reasons.

## What was proved

1. Stock Android, on-demand privileged access and guarded recovery-partition writes were usable. USB data was intermittent; Wi-Fi and microSD were explored as alternate transports.
2. A ported 4.9 kernel reached physical entry, kernel initialization and a small ARM64 PID1. Fresh per-run retained evidence eventually separated real execution from broken reporting.
3. Android17 product builds and scoped host validation eventually passed. A legacy experimental VINTF declaration passed the selected tool; this is not Android certification or general kernel compatibility.
4. Isolated ARM64 fixtures ran genuine early Android services: bootstrap/full APEX activation, BoringSSL tests, Keymaster/Keystore IPC, ART/odsign, BPF loading and zygotes at different qualified stages. These are guest results, not physical tablet qualification.

## The physical blocker

The clean reduced-platform image reported normal-priority PID1 and `compute-begin` for a 2,000,000-iteration arithmetic workload. No matching compute completion or timer sequence was retained. Two kernel thermal deferred-probe messages followed. The later global delay-budget diagnostic produced the same partial helper sequence, with no retained exhaustion/panic record. Both exposures returned to a new stock Android boot verified over USB.

Cached CPU0 addresses moved with the changed code layout inside `__delay`. That is a useful lead. Firmware latch timing is unproved, however; the address is not an established last instruction or a call chain. Missing output does not establish permanent nonexecution. The five-gate plan ended as follows:

1. Reporter calibration: completed for the adopted entry/text route.
2. Actual Linux4.9 entry and PID1: proved.
3. Stable normal-priority RAM computation and timer wakeups: **open**.
4. Storage plus independently qualified rescue: **open**.
5. Physical Android17 first flash: **not started**.

See [the two final trials](FAILED-EXPERIMENTS.md#the-final-two-trials). No causal kernel fix was established. More logging or counter variants were not automatically authorized after the final unknown result.

## Important resolutions worth retaining

- A WebView APK was still an LFS pointer; the pinned Lineage LFS endpoint supplied the exact payload, which passed the real manifest check.
- A Make boolean written as the nonempty string `false` became true; clearing the product setting restored the intended debuggable userdebug properties.
- Duplicate ownership of `heapprofd_client_api.so` broke genuine linkerconfig generation; a scoped namespace/source-ownership fix removed the duplication.
- Real 4.9 BPF failures required distinct fixes: missing fixture map-info support, a loop-free vendor filter, and guarding the unsupported program-name attribute. They were not interchangeable failures.
- Stock USB reporting needed the existing legacy gadget backend; failure of a configfs reporter on stock did not diagnose the port kernel.
- Retained-entry reporting initially rejected real OEM geometry. Calibrating against stock exposed the Linux-record offset assumption, enabling actual 4.9 execution evidence.

## What remains unqualified

Physical sustained execution, display/graphics, Wi-Fi, charging/power behavior, usable sound, camera compatibility, end-to-end rescue, full Google working set and daily usability remain unqualified. Camera research established several ABI/metadata blockers. Audio/sensor work produced source/build evidence, not functioning hardware claims. Replacing only SYSTEM/BOOT is not a complete stock recovery contract after userdata provisioning.

## Archive boundaries

Only research reports, generated metadata/configs, authored code and diffs are published. Full fetched-source copies and modified postimage checkpoints remain outside this public folder; source origins, hashes and available deltas are retained. Some historical links refer to excluded local or VM paths. Archived scripts are non-executable reference material, contain redactions, and must not be run blindly. Historical source hashes are distinct from hashes of exported/redacted text.

Stock rollback images and existing private calibration backups remain on the owner's Mac, outside Git. Calibration preservation completeness is still unqualified. Generated Android17 images/build caches are intentionally not a Git backup; restoring them requires rebuilding or re-fetching external inputs. Consult [cloud retirement](CLOUD-RETIREMENT.md) for the actual infrastructure outcome.

Third-party headers and patch licenses remain applicable. This collection asserts no blanket license over upstream code.
