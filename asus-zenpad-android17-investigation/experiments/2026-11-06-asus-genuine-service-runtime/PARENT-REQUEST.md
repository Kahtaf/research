# Smallest next official build action

Observed 2026-11-06 after the genuine service build completed. No build is launched by this worker.

Under the parent's original build lock, build the existing selected product targets:

- `out/target/product/p00a/system/bin/boringssl_self_test32`
- `out/target/product/p00a/system/bin/boringssl_self_test64`
- `out/target/product/p00a/system/apex/com.android.runtime.apex`
- `out/target/product/p00a/system/build.prop`
- `out/target/product/p00a/system/system_ext/build.prop`
- `out/target/product/p00a/system/product/build.prop`
- `out/target/product/p00a/obj/PACKAGING/apexkeys_intermediates/apexkeys.txt`

First mandatory guest shutdown is `reboot,boringssl-self-check-failed`. The official platform self-test variants are absent, including unstripped ELFs. Available `*_apex31` Conscrypt variants are different graph outputs and were not substituted.

The runtime APEX install edge consumes `out/soong/.intermediates/bionic/apex/com.android.runtime/android_common_hwasan_com.android.runtime/com.android.runtime.apex`. Its package and bootstrap contents are missing. Genuine apexd scans the actual adbd CAPEX but activates zero bootstrap packages; init cannot execute `/apex/com.android.runtime/bin/linkerconfig`.

Generated build.prop rules require the real `out/soong/api_fingerprint.txt`, generated product_config JSON and genuine gen_build_prop/post_process_props host tools. Preserve exact source generation. Full direct edge/dependency receipts will accompany HANDOFF; pseudo dependencies/variables in raw Ninja are not filesystem paths.

The worker is separately addressing missing service/hwservice contexts from genuine selected generator rules in its own fixture. Full framework images, ART/UI/GMS packages and physical commissioning remain out of scope.

## Final update

Do not launch a competing targeted build. The parent reports its r6 failed before native compilation and owns any subsequent r7 build. After that separately owned build completes, provide a coherent official output bundle for this fixture.

Owned generation now reproduces and validates nine service/hwservice context files and the genuine `system_manifest.xml`, `system_ext_manifest.xml`, and `vendor_manifest.xml` modules. The final guest's real hwservicemanager sets its own ready=true/disabled=false and answers HIDL PING. Those earlier metadata failures are resolved inside the fixture; normal official outputs remain preferable for the next product capture.

Official manifest installation paths, if assembling the next bundle:

- `out/target/product/p00a/system/etc/vintf/manifest.xml`
- `out/target/product/p00a/system/system_ext/etc/vintf/manifest.xml`
- `out/target/product/p00a/system/vendor/etc/vintf/manifest.xml`

Include a coherent compiled policy/CIL/mapping/context set and its source provenance when replacing the current pinned 22:19 policy. The late supplemental policy is not the origin of the final fixture's policy: exact recompilation used the original capture-r1.
