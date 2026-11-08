# Graphics implementation report — 6 November 2026

**PASS: strict r7 completed with exit 0 at 14:29:23 UTC.** All 34 proprietary
ELF checks passed, both memory-helper architectures built, the composer and
allocator services plus allocator/mapper implementations built, and linkerconfig
built for the platform and runtime APEX. All 19 linkerconfig host tests passed,
including four tests for the compatibility gates. No build remains live.

Supervisor PID was 813622; build shell PID was 813623. Authoritative remote log:
`/srv/android/asus-device-product/logs/graphics-build-r7.log`; exit/timestamps:
`graphics-build-r7-job.json` in the same directory. Local copies are under
`evidence/graphics-astra/`. r5's host-test include failure and r6's APEX-stub
selection failure are preserved alongside the successful r7 log.

All 49 checkpoint files verified locally. All 34 installed blobs exactly match
the prepared inputs, and all 34 strict-check stamps postdate this build's start.
`evidence/graphics-astra/graphics-r7-local-verification.json` records these checks.
Checkpoint: `artifacts/graphics-result-r7.tar.gz`, SHA-256:
`c9a3691ecd5eccc32cad5fcbfbb586e231821a4c7bd4e7223f05cf687e3a4945`.
The runtime APEX linkerconfig is also saved separately as
`artifacts/graphics-r7-runtime-linkerconfig`, with its hash/source path in
`evidence/graphics-astra/runtime-linkerconfig-r7.json`.

The shared cause was the pre-Treble core ABI. Actual core ARM libc exports the
rejected EABI/private symbols; core libsync exports `sw_sync_*`; core Binder
contains the real PermissionCache implementation omitted from vendor Binder.
`abi-evidence.json` records provider paths, hashes and symbols. Moving modules
to core alone was insufficient: Soong still selected libc's APEX `current` stub.
r7 explicitly selects `libc#impl`, `libm#impl`, `libdl#impl` and `libsync#impl`
where needed, with no implicit STL/system dependencies on these prebuilts.
The saved `soong-core-impl-rule-r7.txt` proves the actual checker used full libc.
Strict ELF checks and undefined-symbol rejection remain enabled.

The 20 proprietary modules now install under system. Eighteen of the 34 ELFs
received only DT_NEEDED additions for logging, CallStack or the real memory
helper; originals remain preserved. Existing sync dependencies remain explicit.
Platform core libstdc++ replaces the extra stock copy; platform libion uses its
real legacy implementation. The memory helper is core; the lights service stays
vendor. No permission or hardware-value shim was introduced.

`compatibility/graphics-r6/linkerconfig.patch` gates compatibility on the P00A
build opt-in, actual first API 1–25, and absent vendor/product VNDK versions.
The profile uses core-first paths for ordinary vendor processes and forwards
system SP-HAL loads to the core namespace, sharing Binder/C++ state. Namespace
isolation stays enabled; APEX and recovery namespace handling is unchanged.
This is a product-wide pre-Treble ABI profile. Two vendor EGL symlinks preserve
modern driver discovery while keeping a single system-installed Mali copy.

Unproven: physical Android 17 boot/display, Mali and ION kernel ioctls, C++ object
layouts, framebuffer scanout, fences, power/resume, SELinux/HAL policy, and full
image/APEX packaging. No flashing, device modification, clean rebuild, new cloud
resource, VM stop, full-candidate edit or global STATUS edit was performed.

## Parent integration

1. Use `artifacts/vendor-graphics-ready-r7/vendor/asus/p00a` or
   `artifacts/vendor-graphics-ready-r7.tar.gz`, and verify `ready-manifest.json`. All 38 prepared files verified
   locally. This exact tree is already deployed on the VM. Preserve its explicit
   `#impl` dependencies; older r5/r6 metadata selects the wrong libc ABI.
2. Retain shipping API 23 and add these full-product settings/packages:

   ```make
   $(call soong_config_set_bool,libion,legacy_impl,true)
   $(call soong_config_set_bool,p00a,legacy_graphics,true)
   $(call inherit-product, vendor/asus/p00a/p00a-graphics-vendor.mk)
   PRODUCT_PACKAGES += libp00a_legacy_memory \
       android.hardware.graphics.composer@2.1-service \
       android.hardware.graphics.allocator@2.0-service \
       android.hardware.graphics.allocator@2.0-impl \
       android.hardware.graphics.mapper@2.0-impl
   ```

   Keep vendor/product VNDK versions unset for this profile.
3. Carry the staged hardware Android.bp change: remove `vendor: true` only from
   `libp00a_legacy_memory`. Keep `legacy_memory.cpp` and the vendor lights service.
4. Apply the cumulative `compatibility/graphics-r6/linkerconfig.patch` after the
   earlier empty-list compatibility patch; verify the adjacent source manifest.
   It is already applied on the VM. A tree at r5 needs only `from-r5.patch`.
   Include the rebuilt runtime APEX in the full product; the standalone module
   milestone does not establish complete APEX packaging.
5. Retain the HIDL init/VINTF entries, framebuffer-fallback composer,
   `ro.hardware.gralloc=mt8163`, and `ro.hardware.egl=mali`. Keep the generated
   EGL aliases and system gralloc paths. Exclude stale vendor copies of the
   proprietary closure/memory helper from image staging; do not add stock HWC.

The next action is parent-owned full-candidate integration and its image build.
The VM is idle and ready for that source change. Do not rerun the immutable r7
supervisor or overwrite its logs; use a new revision for subsequent work.
