# Parent handoff — stock-only one-shot control

Status: **implemented and offline-tested; parent technical review pending; no physical GO**. This worker performed no ADB, USB, root, flashing, reboot, SSH, cloud or build operation. No independent reviewer was assigned. Every real review flag remains false. Synthetic affirmative review objects existed only in isolated, deleted test fixtures.

The question answered here is whether the fixed init-mediated controller has enforceable gates and truthful failure behavior. This is not Android 17 delivery. It provides no SDK37, root persistence, Play/Services, debloat or working-hardware claim. The original AOSP r5 source, output and running build were not contacted or changed.

## Exact scope and inherited evidence

Only `../2026-11-06-asus-android17-os-rescue/artifacts/candidate-final/UNTESTED-stock-control.img` is accepted: **8,654,848 bytes**, SHA256 `7d74dfcaf4b2793453906799d721bfd95a401c564f6698b1c646e18bee918ea5`. Its 16,740,352-byte padded p10 image is `6c6a3f534646ed30257c21c7d91be65ea1b8844ef6aa2d0bd3c11545f62db925`. Its wrapped kernel must equal stock, `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`. There is no image, kernel, partition, endpoint, retry or resume override. A new 4.9 probe/rescue image is outside this controller.

The exact stock recovery inverse is SHA256 `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`, 16,740,352 bytes. The parent backup-acceptance receipt actually hashes to the configured `73f979aa1a74766fdd485960c04e64da716aad37650dc45b2c4f858e9b19841f`; this was read and verified, not invented. No full SYSTEM/data copy or full SYSTEM rehash was done. The local rollback artifacts remain in their original spike, as do all nested repositories.

The historical README's BLOCKED conclusion applies to direct UID0 `shell` RESTART2 and its denied CAP_SYS_BOOT. This continuation uses the separately evidenced production adbd request `reboot recovery`, volatile `sys.powerctl=reboot,recovery`, and the stock init powerctl builtin. It does not change SELinux policy or add an entry bypass. The inherited p10 writer and its pinned root helper remain unchanged, including the helper's Enforcing-restoration checks; this is not a claim that their temporary-root implementation has become continuously Enforcing. Entry is permitted only after fresh stock Enforcing health checks.

The original 18 native syscall-boundary cases and 65,536-input LK predicate evidence remain in `../2026-11-06-asus-stock-programmatic-control/evidence/offline-boundary.json`. They were indexed, not rerun. The saved LK busy-poll, dropped-PMIC-write and early-boot failure cases still limit any physical one-shot claim. The seven stock init/adbd instruction-emulation cases were rerun using the existing environment and original binary files; new results are in this spike. Those tests stub OS/libc/property and hardware effects; they do not execute Android or prove PMIC behavior.

## Changes and qualification

`source/service/controller.py` retains profile `asus-stock-only-init-mediated-v2` with an additional contract revision. It imports the exact pinned existing writer from its original location. Its own source/tests and inherited source/evidence are pinned in each review contract. The same existing host lock prevents simultaneous legacy/new p10 writers; review consumption uses exclusive creation before any live trial. Each run has unique durable phase directories and a single entry-intent file. No saved pin can be supplied through the CLI.

After any possible entry dispatch, an explicit inverse requires an actual new stock boot ID, expected USB topology, a new transport ID, and healthy stock SDK24 identity, secure ADB and Enforcing. Even the exact audited `reboot failed: -1` response no longer permits a same-boot post-entry inverse. EOF/exit status do not prove reset. A transport-unknown entry permits bounded read-only observation only; it cannot trigger TCP reenable or restoration, even if a new stock boot is subsequently observed. At other transport-loss points, the controller issues no subsequent automatic device operation.

A completed pre-entry refusal can perform one guarded stock inverse only after the observer is stopped. The inherited writer can perform its own one stock inverse after a completed install failure; the outer controller never adds another inverse to that result. Unknown writes stop. Restore readback and cleanup are reported separately, and a later guard failure cannot manufacture success or erase an already verified p10 readback.

Full para hash, deployed init/adbd hashes, the exact root/system RC set, stock health and p10 readback are checked before install and entry, before an explicit inverse, and after a successful inverse. Para is p12 with the inherited fixed geometry. Cache is p24, ext4, with its fixed geometry and no `/cache/recovery/command`, including an empty file; symlinks are refused. These are read/guard operations, not metadata clearing. **There is no whole-cache byte-equality claim**: normal Android and shutdown may write cache. The tests' unchanged para/cache fixture result means the modeled controller has no such write; it is not physical calibration preservation evidence.

Existing TCP5555 can be reestablished only after a new healthy stock return through freshly authenticated USB. It uses only the already-authorized fixed endpoint and port. No key, firewall or authentication edits are provided. A new root session independently verifies stock identity through the pinned TCP endpoint.

The observer's report parser now treats `END_DIAGNOSTIC` as framing rather than the last section's contents. Missing/partial/invalid reports can coexist with a verified stock return and exact inverse, but cannot yield diagnostic success. A return before 120 seconds yields an incomplete diagnostic outcome. Even a 120–420-second return never proves that the image timer caused the reset.

**Validation:** 65 passing unittest tests, including 30 separately injected transport-loss boundaries; seven passing extracted init/adbd instruction-emulation cases; and a successful real local `PLAN_ONLY` run. Tests exercise the real controller, pinned writer state machine, observer/parser, pin/review validation, exclusive lock and single-use receipt. Typed fake storage/transport effects are used; no external process or network operation is allowed by the fault suite's Python audit hook. The generated root envelope and p10 destination are inspected; the actual Android7 shell, USB/ADB runtime, root exploit and kernel geometry enforcement are not executed. The initial two report-framing test failures and subsequent passing reports are retained.

## Commands safe to run now — local only

From `/OWNER_HOME/Documents/workspace/ideas`:

```sh
python3 -B 2026-11-06-asus-stock-roundtrip-continuation/tests/service/test_faults.py
2026-11-06-asus-stock-programmatic-control/.venv/bin/python -B 2026-11-06-asus-stock-roundtrip-continuation/tests/service/test_firmware.py
python3 -B 2026-11-06-asus-stock-roundtrip-continuation/source/service/controller.py plan
```

The last command reads bounded local input files and writes a new local run and unapproved review template. It never creates a host transport or contacts a device. All three actions (`plan`, `preflight`, `trial`) remain PLAN_ONLY without `--execute`. Do not rerun the old `extract_rc.py`: it can reconstruct a full SYSTEM image and is unnecessary here.

The completed plan is in `evidence/service/runs/20261106T193652Z-6bab3892d6af6400/`. Its `review-template.json` has all approval/attestation flags false and no reviewer. Parent must assess the concrete implementation, retained evidence, present device conditions and fallback readiness before making a separate technical review. There is no worker-approved review file or supplied execution hash.

## Future parent execution — not authorized by this handoff

The inherited user-away scope is **2026-11-06 17:03–23:03 UTC**. Code checks this immutable outer window and the parent's review expiry, including before entry, TCP reenable and explicit inverse. This handoff does not extend it. At or after expiry, stop; elapsed time never establishes presence. Parent must leave enough time for observation and guarded restoration. A nearby physical fallback is a parent readiness issue; the static and mocked results here do not supply it, and this worker has issued no physical GO.

After actual parent technical review, the parent can save the reviewed document as `evidence/service/parent-review.json` in this spike and independently record its SHA256. The following is the exact guarded trial invocation, with a mandatory externally supplied review digest; **it was not executed**:

```sh
PARENT_REVIEW=/OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-stock-roundtrip-continuation/evidence/service/parent-review.json
# Set PARENT_REVIEW_SHA256 only to the digest independently recorded by the parent reviewer.
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-stock-roundtrip-continuation/source/service/controller.py trial \
  --execute --unattended-stock-only --exclusive-device-owner \
  --review "$PARENT_REVIEW" --reviewed-sha256 "${PARENT_REVIEW_SHA256:?Parent technical review and independently recorded hash are required}"
```

Optional parent live preflight uses the identical flags and review arguments with action `preflight` instead of `trial`. It **is not a read-only host operation**: it invokes the inherited root helper and creates/removes temporary device staging, though it writes no OS block partition. Its fresh pin cannot authorize later entry. It does not consume a trial review; the trial repeats its guards and consumes the review before live contact.

There is deliberately no standalone restore, retry or resume CLI. Following an uncertain result, do not run another trial, delete consumption records, select a boot mode, infer reset from a timeout, or turn this handoff into a new-kernel attempt. Parent must assess saved evidence and actual current state under the original scope. The internal verified-return inverse is automatic only within that guarded, single run.

Exit 0 means a validated offline plan, a completed live preflight, or the specifically named verified trial success; inspect `outcome` to distinguish them. Exit 3 means actual stock return/restoration with incomplete diagnostic evidence. Exit 2 is refusal or an incomplete/uncertain operation. Examine top-level `state.json`, phase journals, `entry-intent.json`, host command/results, observer reports and `restore_result`; a terminal result alone is not permission to retry. No terminal result from this spike claims Android 17 or working hardware.
