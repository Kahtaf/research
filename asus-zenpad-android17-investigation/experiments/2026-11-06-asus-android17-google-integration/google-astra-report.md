# Google inline integration handoff

**Ready for parent staging and build.** The existing release ZIP reconstructs
all 36 selected upstream proprietary blobs exactly: 32 streamed members,
734,740,442 bytes, every size and Git blob SHA1 matched. Per-output SHA256s and
the strict input/output inventory are in `evidence/inline-source-manifest.json`.
No full payload was extracted on the Mac; no VM writes/builds or device actions.

Release: `MindTheGapps-17.0.0-arm64-20261022_132445.zip`, 544,284,463 bytes,
SHA256 `a6844eeb2613541558237e467b20feb01f8b45b2ebab0109834140ea59b6ca4d`.
Source: [vendor_gapps at 822ff6a](https://github.com/MindTheGapps/vendor_gapps/tree/822ff6a805533792ae43a9c3f2a159222da22a6f).
All 27 selected metadata files match that commit's Git blob hashes, including
the exact dummy app and overlay sources. There are 64 planned output files,
plus the embedded staging manifest. Nine small-fixture tests passed;
`evidence/stager-tests.txt` records them. These are not Android build results.

Parent transfers `staged-inputs/google-inline-inputs.tar.gz` (verify its adjacent
`.sha256` file) and the **existing** ZIP into
`/srv/android/asus-device-product/google-inline/`. After graphics work ends,
run these commands on the builder; they have not been run by this agent:

```sh
cd /srv/android/asus-device-product/google-inline
tar -xzf google-inline-inputs.tar.gz
python3 scripts/stage_inline.py stage \
  --zip /srv/android/asus-device-product/google-inline/MindTheGapps-17.0.0-arm64-20261022_132445.zip \
  --manifest /srv/android/asus-device-product/google-inline/evidence/inline-source-manifest.json \
  --android-root /srv/android/lineage24
python3 scripts/stage_inline.py check --android-root /srv/android/lineage24
```

The stager hashes the ZIP, reconstructs its chunks directly into a private
directory, compares all output hashes to the reviewed manifest, checks the
written files, then publishes `vendor/gapps`. It requires approximately 829 MiB
free for staging, refuses an existing destination and cleans failed temporary
stages. It never clones, builds, changes the product, or extracts VelvetTitan.
For an existing stage, use `check`; do not delete a checkout blindly.

Add this product snippet to the full product through the parent's integration:

```make
# Inline Google source must be staged at vendor/gapps.
$(call inherit-product, vendor/gapps/asus-p00a-google.mk)
```

The wrapper inherits the upstream arm64/common products and rejects unsupported
profiles. The generated Android.bp adds `compile_multilib: "64"` to the
arm64-only `libjni_latinimegoogle`; current Soong otherwise creates an arm
variant on this dual-architecture product. VelvetTitan's unused module/genrule
and product conditional are removed along with its four source chunks.
All other normal upstream Google components remain. Signed APK/APEX bytes and
permission XMLs are unchanged; overlays compile from exact upstream source.

Namespace exports work through Android's inherited-product `LOCAL_PATH`.
The real upstream `PrebuiltGmsCoreVic` dummy is included for the APEX dependency;
do not install it separately. Preserve both Google and Lineage setup wizards:
current Lineage code detects GMS and disables its HOME entry for the handoff.
Current Soong copies this APEX and records it PRESIGNED. Full source rationale,
including the dummy's default certificate-metadata caveat, is in
`evidence/inline-build-findings.md`; source hashes/revisions are in
`evidence/platform-inline-source.json`.

Normal standalone tablet payload remains **734,779,374 bytes**. The inline
proprietary inputs total **734,740,442 bytes**: the 38,932-byte difference is
38,240 bytes of standalone overlays rebuilt from source and 692 bytes of
recovery addon.d fragments not installed by upstream inline makefiles.
The staged source files total 734,768,663 bytes before the manifest. This is
not final image size: compiled overlays, image metadata and other ROM content
must fit the **3,753,902,080-byte** physical system partition. No low-space
pruning was added. Builder build-space needs exceed the staging-space check.

Remaining gates: real Soong/Kati build; preprocessed APK validation; APEX APK
inventory validation; JNI/overlay compilation; installed signed-byte checks;
target-file signing metadata; complete filesystem fit. Reuse the existing
EROFS/kernel evidence (4096-byte blocks, incompat bit 1 recognized by pinned
4.9). Actual APEX mount/activation, privileged permissions, first-run handoff,
login, Play install/update and reboot remain unproved. Parent retains all VM,
full-candidate, physical-test and data-preservation decisions.
