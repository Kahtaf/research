# Google Play on the ASUS Android 17 port

Question: what exact ARM64 Android 17 Google package can be integrated without
assuming the tablet's Android 7 Google packages remain compatible?

Status: pinned inline source stager implemented and locally verified. All 36
selected proprietary Git blobs were reproduced by streaming 32 members of the
existing verified ZIP, without writing payload files. Exact metadata, dummy app
and overlay sources are cached. Builder staging and the Android image build
remain for the parent; no VM writes or device changes were performed.

Source: https://github.com/MindTheGapps/17.0.0-arm64/releases/tag/MindTheGapps-17.0.0-arm64-20261022_132445
Published 22 October 2026. Release points to vendor_gapps source commit
822ff6a805533792ae43a9c3f2a159222da22a6f. Expected package size 544284463 bytes,
SHA256 a6844eeb2613541558237e467b20feb01f8b45b2ebab0109834140ea59b6ca4d.

Stock evidence confirms Play Store, Play services and Google Services Framework
are retained/enabled on Android 7. This does not establish compatibility after
replacing the OS. The final Android17 image must include matching Google
components and privileged permissions before normal user setup.

Continuation: start with [google-astra-report.md](google-astra-report.md). After
the graphics owner hands back the builder, the parent transfers the small
`staged-inputs/google-inline-inputs.tar.gz` bundle and existing verified ZIP,
runs the Linux stager to create `vendor/gapps`, then inherits the generated
product wrapper before the full image build. Do not execute the recovery
installer against stock Android. Confirm the combined image fits the measured
3,753,902,080-byte system GPT partition. Source hashes are not proof of working
Google login/Play updates on the tablet.

## Concrete result

The archive explicitly declares arch=arm64, version=37, version_nice=17.0.0.
The ZIP digest matches GitHub release metadata. Upstream installer normally
omits VelvetTitan on devices other than tangorpro; following that existing
selection leaves 734,779,374 bytes of system payload. This preserves the normal
Google app set, including speech, accessibility, Family Link and setup.
Do not trigger upstream's low-space pruning silently: the user asked to keep
Google components. Combined base+Google filesystem fit remains to be measured.

Play services is supplied as signed com.google.android.gmssystem.prodvic.apex,
not a loose old GmsCore APK. Its actual EROFS payload uses 4096-byte blocks and
incompat feature bit 1 only; the exact pinned4.9 EROFS backport recognizes that
bit. Loop, dm-verity and EROFS are enabled. This clears an obvious static format
mismatch; actual mount/apexd activation, login, Store install/update and reboot
remain required tests. Evidence includes the exact superblock and pinned
kernel source/header/config hashes, rather than inferring from CONFIG_EROFS.

Upstream documents inline Android builds in vendor_gapps/README.md: source
must occupy vendor/gapps because generated common/arm64 paths refer to it;
inherit vendor/gapps/arm64/arm64-vendor.mk. Use commit
822ff6a805533792ae43a9c3f2a159222da22a6f and retain upstream module definitions,
permissions and overlays. Do not add just APKs with PRODUCT_COPY_FILES. The
parent will stage that source on the builder after the graphics owner returns,
then check actual partition fit with the complete product. The downloaded ZIP
is retained locally as verified reference/input; no installer was executed.

Important outputs: evidence/package-inventory.json, integration-budget.json,
google-apex-layout.json, google-erofs-compatibility.json and
kernel-erofs-support.json. The latter contains exact pinned source excerpts.

## Reproducible inline handoff

- `scripts/stage_inline.py`: stdlib-only metadata, streaming verification,
  atomic builder staging and read-only staged-tree verification.
- `evidence/inline-source-manifest.json`: verified ZIP identity/inventory,
  upstream input hashes, per-chunk offsets/Git SHA1/SHA256, exact output inventory.
- `evidence/upstream-source/`: pristine pinned source, including the dummy app
  and all four overlay trees. Existing cached source is checked, not trusted
  merely because it exists. `--fetch-metadata` can fetch missing small files
  from the pinned commit; the verified ZIP is never downloaded by the stager.
- `staged-inputs/inline-metadata/`: reviewable adapted small files, **not** a
  complete source checkout. Do not deploy these alone.
- `evidence/inline-build-findings.md` and `platform-inline-source.json`: actual
  namespace/dummy/JNI/setup/APEX findings and read-only platform source evidence.
- `scripts/test_stage_inline.py` and `evidence/stager-tests.txt`: small-fixture
  integrity, atomicity, overwrite-refusal, inventory and Mac-protection checks.
- `scripts/package_inline_inputs.py`: reproducibly makes the small upload
  bundle plus its SHA256 sidecar. The large ZIP remains a separate existing input.

Run `python3 scripts/stage_inline.py` for metadata-only work, or append `verify`
to recheck the actual payload in bounded-memory ZIP streams. No full extraction
or clone is needed on the Mac. The `stage` mode is deliberately Linux-only and
refuses an existing `vendor/gapps`; `check` verifies a previously staged tree.
