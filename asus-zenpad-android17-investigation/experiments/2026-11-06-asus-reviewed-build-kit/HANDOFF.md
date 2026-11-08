# Parent handoff

The implementation is staged at `/srv/android/asus-reviewed-build-kit/r1`. Its default is PLAN_ONLY. This worker did not integrate, start r6, create an integration attempt, or operate a device. The parent owns every future active execution.

Review `REPORT.md`, `inputs/plan.json`, and the scripts before execution. The exact immutable kit manifest is:

```text
9b9eea2ae274a873d99459ea4faa352dba1dd6a9ba8b5986fae0304047ee941b  inputs/kit-pins.json
```

This pins 42 kit/input/test files. `inputs/plan.json` additionally pins 41 existing builder artifacts/source tools and selects only `/srv/android/asus-product-integration-staging/r1`. It never applies the patch to the already compiled `/srv/android/asus-build-continuation/kernel` fixture.

Define the authorized SSH wrapper on the Mac:

```sh
asus_builder() {
  ssh -i "$HOME/.ssh/asus_p00a_android17" \
    -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=15 \
    -o StrictHostKeyChecking=yes \
    -o HostKeyAlias=compute.8549823276971553556 \
    -o UserKnownHostsFile="$HOME/.ssh/google_compute_known_hosts" \
    android@IP_REDACTED "$@"
}
```

The read-only PLAN_ONLY command is:

```sh
asus_builder 'cd /srv/android/asus-reviewed-build-kit/r1 && printf "%s\n" "9b9eea2ae274a873d99459ea4faa352dba1dd6a9ba8b5986fae0304047ee941b  inputs/kit-pins.json" | sha256sum --check - && python3 -B scripts/integrate.py'
```

A live native build or held full-build lock returns exit 20. Do not loop, poll, schedule, or attach a waiter. Time passing is not authorization or physical presence.

After the parent has reviewed this kit and the actual original r5 result is terminal, the explicit one-shot integration/build command is:

```sh
asus_builder 'cd /srv/android/asus-reviewed-build-kit/r1 && printf "%s\n" "9b9eea2ae274a873d99459ea4faa352dba1dd6a9ba8b5986fae0304047ee941b  inputs/kit-pins.json" | sha256sum --check - && python3 -B scripts/integrate.py --mode PARENT_EXECUTE'
```

This is a foreground, parent-executed command. It reacquires the real existing full-product lock nonblockingly, repeats native-process and actual-input gates, preserves r5 files, integrates, and keeps that same lock through r6 launch, build, and host validation. The shell inherits the lock FD; it cannot be invoked independently without the supervisor and an unconsumed launch. No `installclean` runs. The two future `m` invocations use `-j1`.

The observed next unused revision was r6. Every `full-build-r6.*` file and any kit `attempt/` directory prevents reuse. Do not delete or rename these guards to retry. After a partial integration/build failure, preserve the attempt and inspect its `FAILED.json`, `before/`, `preservation.json`, available postimages, logs and outputs. There is no automatic rollback or retry.

If r5 genuinely fails, the command above stops. A successful r5 needs coherent start/complete/finish/exit markers and actual BOOT/SYSTEM hashes matching its image report. A failed r5 needs coherent failure markers and an explicit parent review bound to its exact log, terminal-marker and image hashes. To inspect that result without accepting it:

```sh
asus_builder 'cd /srv/android/asus-reviewed-build-kit/r1 && printf "%s\n" "9b9eea2ae274a873d99459ea4faa352dba1dd6a9ba8b5986fae0304047ee941b  inputs/kit-pins.json" | sha256sum --check - && python3 -B scripts/integrate.py --describe-prior'
```

For a failed terminal result, the returned `result.review_template` is deliberately unapproved. Only after reviewing the actual failure, the parent may create `parent-review/r5-failure.json` from that object, set `reviewed_by_parent` to true, and record a substantive `reason`. Record its actual SHA256. Append both `--prior-failure-review /srv/android/asus-reviewed-build-kit/r1/parent-review/r5-failure.json` and `--prior-failure-review-sha256 THE_ACTUAL_REVIEWED_SHA256` to both PLAN_ONLY and PARENT_EXECUTE. No such approval file exists now. Changed logs, markers, images, receipt bytes or a contradictory success marker invalidate the review. This allows a reviewed *new product revision*, never an automatic retry of r5.

For a separate, bounded read-only input audit, append `--audit-inputs` to the sealed PLAN_ONLY command. This rehashes the baseline and selected candidates; it does not establish terminal eligibility or create a readiness flag.

Future outputs for parent/source-adapter binding are in `attempt/validation/`:

- `complete.json`: exact final raw SYSTEM and untested BOOT hashes/paths, source image hashes, integration/source/parent-parity/kit receipt hashes, host tool hashes, and explicit false runtime/physical/flash-ready fields.
- `source-postimages.json`: actual integrated kernel postimages, 61,976 baseline files checked, matching generated config, Connectivity and wificond hashes.
- `packaging.json`: actual source BOOT/kernel/config binding, 92-byte enforcing header, real LK wrapper provenance, allowed DT changes and actual ramdisk/memory checks.
- `google-signed-bytes.json`, `root-payload.json`, and the preserved command journals/logs.
- `system-partition.raw`: exactly 3,753,902,080 bytes, every zero range and partition tail written. A later writer must materialize every byte; no discard/skip substitution is implied.
- `UNTESTED-sdk37-combined-boot.img`: produced only from a real completed source BOOT with executable AArch64 init and the selected physical kernel. Synthetic packaging mode is never used by the build kit.

These artifacts do not grant physical GO or claim runtime root, Google operation, full service-chain execution, combined-kernel boot, calibration/device safety, rescue readiness, or flash readiness. No final BOOT or SYSTEM artifact has been produced by this worker.
