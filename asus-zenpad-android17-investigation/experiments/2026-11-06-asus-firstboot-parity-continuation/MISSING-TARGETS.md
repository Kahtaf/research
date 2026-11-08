# Missing genuine service prerequisites

Observed 2026-11-06T19:28:53.214727+00:00. Paths are relative to /srv/android/lineage24. Includes TOC validation inputs; these are not counts of distinct libraries. No build was launched.

## apexd (android_arm64_armv8-a)

Exact link target:

`out/soong/.intermediates/system/apex/apexd/apexd/android_arm64_armv8-a/unstripped/apexd`

Missing inputs (22):

- `out/soong/.intermediates/system/apex/apexd/apexd/android_arm64_armv8-a/obj/system/apex/apexd/apexd_main.o`
- `out/soong/.intermediates/system/apex/apexd/apex_aidl_interface-cpp/android_arm64_armv8-a_shared/before_final_validations/apex_aidl_interface-cpp.so.toc`
- `out/soong/.intermediates/system/libvintf/libvintf/android_arm64_armv8-a_shared/before_final_validations/libvintf.so.toc`
- `out/soong/.intermediates/system/apex/apexd/libapexd_checkpoint_vold/android_arm64_armv8-a_static/libapexd_checkpoint_vold.a`
- `out/soong/.intermediates/system/apex/apexd/libapexd_metrics_stats/android_arm64_armv8-a_static/libapexd_metrics_stats.a`
- `out/soong/.intermediates/system/core/libstats/bootstrap/libstatsbootstrap/android_arm64_armv8-a_static/libstatsbootstrap.a`
- `out/soong/.intermediates/frameworks/base/core/java/android.os.statsbootstrap_aidl-cpp/android_arm64_armv8-a_static/android.os.statsbootstrap_aidl-cpp.a`
- `out/soong/.intermediates/system/apex/apexd/libapexservice/android_arm64_armv8-a_static/libapexservice.a`
- `out/soong/.intermediates/system/apex/apexd/libapexd/android_arm64_armv8-a_static/libapexd.a`
- `out/soong/.intermediates/system/apex/proto/lib_apex_blocklist_proto/android_arm64_armv8-a_static/lib_apex_blocklist_proto.a`
- `out/soong/.intermediates/system/apex/proto/lib_apex_image_list_proto/android_arm64_armv8-a_static/lib_apex_image_list_proto.a`
- `out/soong/.intermediates/system/apex/proto/lib_apex_storage_metadata_proto/android_arm64_armv8-a_static/lib_apex_storage_metadata_proto.a`
- `out/soong/.intermediates/packages/modules/Virtualization/libs/libmicrodroid_payload_metadata/lib_microdroid_metadata_proto/android_arm64_armv8-a_static/lib_microdroid_metadata_proto.a`
- `out/soong/.intermediates/system/apex/apexd/libapex/android_arm64_armv8-a_static/libapex.a`
- `out/soong/.intermediates/system/apex/proto/lib_apex_session_state_proto/android_arm64_armv8-a_static/lib_apex_session_state_proto.a`
- `out/soong/.intermediates/system/apex/proto/lib_apex_manifest_proto/android_arm64_armv8-a_static/lib_apex_manifest_proto.a`
- `out/soong/.intermediates/system/security/ondevice-signing/libsigningutils/android_arm64_armv8-a_static/libsigningutils.a`
- `out/soong/.intermediates/system/extras/verity/libverity_tree/android_arm64_armv8-a_static/libverity_tree.a`
- `out/soong/.intermediates/system/vold/libvold_binder/android_arm64_armv8-a_static/libvold_binder.a`
- `out/soong/.intermediates/system/apex/apexd/sysprop/libcom.android.sysprop.apex/android_arm64_armv8-a_static/libcom.android.sysprop.apex.a`
- `out/soong/.intermediates/system/apex/apexd/apex_aidl_interface-cpp/android_arm64_armv8-a_shared/apex_aidl_interface-cpp.so`
- `out/soong/.intermediates/system/libvintf/libvintf/android_arm64_armv8-a_shared/libvintf.so`

## hwservicemanager (android_arm64_armv8-a)

Exact link target:

`out/soong/.intermediates/system/hwservicemanager/hwservicemanager/android_arm64_armv8-a/unstripped/hwservicemanager`

Missing inputs (7):

- `out/soong/.intermediates/system/hwservicemanager/hwservicemanager/android_arm64_armv8-a/obj/system/hwservicemanager/service.o`
- `out/soong/.intermediates/system/tools/hidl/utils/libhidl-gen-utils/android_arm64_armv8-a_shared/before_final_validations/libhidl-gen-utils.so.toc`
- `out/soong/.intermediates/system/libvintf/libvintf/android_arm64_armv8-a_shared/before_final_validations/libvintf.so.toc`
- `out/soong/.intermediates/system/hwservicemanager/libhwservicemanager/android_arm64_armv8-a_static/libhwservicemanager.a`
- `out/soong/.intermediates/system/hwservicemanager/libtokenmanager/android_arm64_armv8-a_static/libtokenmanager.a`
- `out/soong/.intermediates/system/tools/hidl/utils/libhidl-gen-utils/android_arm64_armv8-a_shared/libhidl-gen-utils.so`
- `out/soong/.intermediates/system/libvintf/libvintf/android_arm64_armv8-a_shared/libvintf.so`

## keystore2 (android_arm64_armv8-a)

Exact link target:

`out/soong/.intermediates/system/security/keystore2/keystore2/android_arm64_armv8-a/unstripped/keystore2`

Missing inputs (75):

- `out/soong/.intermediates/frameworks/base/libandroid_security_flags_rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_security_flags_rust.rlib`
- `out/soong/.intermediates/system/security/keystore2/libkeystore2/android_arm64_armv8-a_rlib_rlib-std/libkeystore2.rlib`
- `out/soong/.intermediates/system/security/keystore2/legacykeystore/liblegacykeystore-rust/android_arm64_armv8-a_rlib_rlib-std/liblegacykeystore-rust.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/rusqlite/librusqlite/android_arm64_armv8-a_rlib_rlib-std/librusqlite.rlib`
- `out/soong/.intermediates/system/logging/rust/libstructured_log/android_arm64_armv8-a_rlib_rlib-std/libstructured_log.rlib`
- `out/soong/.intermediates/system/logging/rust/liblog_event_list/android_arm64_armv8-a_rlib_rlib-std/liblog_event_list.rlib`
- `out/soong/.intermediates/system/hardware/interfaces/keystore2/aidl/android.system.keystore2-V6-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_system_keystore2_V6.rlib`
- `out/soong/.intermediates/hardware/interfaces/security/keymint/aidl/android.hardware.security.keymint-V5-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_hardware_security_keymint_V5.rlib`
- `out/soong/.intermediates/hardware/interfaces/security/rkp/aidl/android.hardware.security.rkp-V3-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_hardware_security_rkp_V3.rlib`
- `out/soong/.intermediates/hardware/interfaces/security/secureclock/aidl/android.hardware.security.secureclock-V1-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_hardware_security_secureclock_V1.rlib`
- `out/soong/.intermediates/hardware/interfaces/security/sharedsecret/aidl/android.hardware.security.sharedsecret-V1-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_hardware_security_sharedsecret_V1.rlib`
- `out/soong/.intermediates/frameworks/base/core/java/android.os.permissions_aidl-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_os_permissions_aidl.rlib`
- `out/soong/.intermediates/system/security/keystore2/aidl/android.security.apc-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_security_apc.rlib`
- `out/soong/.intermediates/system/security/keystore2/aidl/android.security.authorization-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_security_authorization.rlib`
- `out/soong/.intermediates/system/security/keystore2/aidl/android.security.compat-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_security_compat.rlib`
- `out/soong/.intermediates/system/security/keystore2/aidl/android.security.maintenance-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_security_maintenance.rlib`
- `out/soong/.intermediates/system/security/keystore2/aidl/android.security.metrics-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_security_metrics.rlib`
- `out/soong/.intermediates/frameworks/base/core/java/android.security.rkp_aidl-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_security_rkp_aidl.rlib`
- `out/soong/.intermediates/system/apex/apexd/apex_aidl_interface-rust/android_arm64_armv8-a_rlib_rlib-std/libapex_aidl_interface.rlib`
- `out/soong/.intermediates/system/security/keystore2/libaconfig_android_hardware_biometrics_rust/android_arm64_armv8-a_rlib_rlib-std/libaconfig_android_hardware_biometrics_rust.rlib`
- `out/soong/.intermediates/frameworks/base/libandroid_security_flags_rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_security_flags_rust.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/der/libder/android_arm64_armv8-a_rlib_rlib-std/libder.rlib`
- `out/soong/.intermediates/system/security/keystore2/aaid/libkeystore2_aaid-rust/android_arm64_armv8-a_rlib_rlib-std/libkeystore2_aaid-rust.rlib`
- `out/soong/.intermediates/system/security/keystore2/apc_compat/libkeystore2_apc_compat-rust/android_arm64_armv8-a_rlib_rlib-std/libkeystore2_apc_compat-rust.rlib`
- `out/soong/.intermediates/system/security/keystore2/src/crypto/libkeystore2_crypto_rust/android_arm64_armv8-a_rlib_rlib-std/libkeystore2_crypto_rust.rlib`
- `out/soong/.intermediates/system/security/keystore2/libkeystore2_flags_rust/android_arm64_armv8-a_rlib_rlib-std/libkeystore2_flags_rust.rlib`
- `out/soong/.intermediates/system/security/keystore2/src/hal_instance_names/libkeystore2_hal_names_rust/android_arm64_armv8-a_rlib_rlib-std/libkeystore2_hal_names_rust.rlib`
- `out/soong/.intermediates/system/security/keystore2/src/km_compat/libkeystore2_km_compat/android_arm64_armv8-a_rlib_rlib-std/libkeystore2_km_compat.rlib`
- `out/soong/.intermediates/system/security/keystore2/selinux/libkeystore2_selinux/android_arm64_armv8-a_rlib_rlib-std/libkeystore2_selinux.rlib`
- `out/soong/.intermediates/system/security/keystore2/message_macro/libmessage_macro/android_arm64_armv8-a_rlib_rlib-std/libmessage_macro.rlib`
- `out/soong/.intermediates/system/security/keystore2/postprocessor_client/libpostprocessor_client/android_arm64_armv8-a_rlib_rlib-std/libpostprocessor_client.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/rand/librand/android_arm64_armv8-a_rlib_rlib-std/librand.rlib`
- `out/soong/.intermediates/system/security/keystore2/rkpd_client/librkpd_client/android_arm64_armv8-a_rlib_rlib-std/librkpd_client.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/serde_cbor/libserde_cbor/android_arm64_armv8-a_rlib_rlib-std/libserde_cbor.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/tokio/libtokio/android_arm64_armv8-a_rlib_rlib-std/libtokio.rlib`
- `out/soong/.intermediates/system/security/keystore2/watchdog/libwatchdog_rs/android_arm64_armv8-a_rlib_rlib-std/libwatchdog_rs.rlib`
- `out/soong/.intermediates/frameworks/base/native/android/packagemanager_aidl-rust/android_arm64_armv8-a_rlib_rlib-std/libpackagemanager_aidl.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/libsqlite3-sys/liblibsqlite3_sys/android_arm64_armv8-a_rlib_rlib-std/liblibsqlite3_sys.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/rusqlite/librusqlite/android_arm64_armv8-a_rlib_rlib-std/librusqlite.rlib`
- `out/soong/.intermediates/system/logging/liblog/liblog_event_list_bindgen/android_arm64_armv8-a_rlib_rlib-std/liblog_event_list_bindgen.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/const-oid/libconst_oid/android_arm64_armv8-a_rlib_rlib-std/libconst_oid.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/flagset/libflagset/android_arm64_armv8-a_rlib_rlib-std/libflagset.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/zeroize/libzeroize/android_arm64_armv8-a_rlib_rlib-std/libzeroize.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/der_derive/libder_derive/linux_glibc_x86_64/libder_derive.so`
- `out/soong/.intermediates/system/security/keystore2/aaid/libkeystore2_aaid_bindgen/android_arm64_armv8-a_rlib_rlib-std/libkeystore2_aaid_bindgen.rlib`
- `out/soong/.intermediates/system/security/keystore2/aaid/libkeystore2_aaid/android_arm64_armv8-a_shared_cfi/libkeystore2_aaid.so`
- `out/soong/.intermediates/system/security/keystore2/apc_compat/libkeystore2_apc_compat_bindgen/android_arm64_armv8-a_rlib_rlib-std/libkeystore2_apc_compat_bindgen.rlib`
- `out/soong/.intermediates/system/security/keystore2/apc_compat/libkeystore2_apc_compat/android_arm64_armv8-a_shared_cfi/libkeystore2_apc_compat.so`
- `out/soong/.intermediates/system/security/keystore2/src/crypto/libkeystore2_crypto_bindgen/android_arm64_armv8-a_rlib_rlib-std/libkeystore2_crypto_bindgen.rlib`
- `out/soong/.intermediates/system/security/keystore2/src/hal_instance_names/libkeystore2_hal_names_cpp/android_arm64_armv8-a_static/libkeystore2_hal_names_cpp.a`
- `out/soong/.intermediates/system/security/keystore2/src/km_compat/libkm_compat_service/android_arm64_armv8-a_shared_cfi/libkm_compat_service.so`
- `out/soong/.intermediates/external/selinux/libselinux/libselinux_bindgen/android_arm64_armv8-a_rlib_rlib-std/libselinux_bindgen.rlib`
- `out/soong/.intermediates/system/security/keystore2/aidl/android.security.postprocessor-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_security_postprocessor.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/rand_chacha/librand_chacha/android_arm64_armv8-a_rlib_rlib-std/librand_chacha.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/rand_core/librand_core/android_arm64_armv8-a_rlib_rlib-std/librand_core.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/mio/libmio/android_arm64_armv8-a_rlib_rlib-std/libmio.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/pin-project-lite/libpin_project_lite/android_arm64_armv8-a_rlib_rlib-std/libpin_project_lite.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/signal-hook-registry/libsignal_hook_registry/android_arm64_armv8-a_rlib_rlib-std/libsignal_hook_registry.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/socket2/libsocket2/android_arm64_armv8-a_rlib_rlib-std/libsocket2.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/chrono/libchrono/android_arm64_armv8-a_rlib_rlib-std/libchrono.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/num-traits/libnum_traits/android_arm64_armv8-a_rlib_rlib-std/libnum_traits.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/mockall/libmockall/android_arm64_armv8-a_rlib_rlib-std/libmockall.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/downcast/libdowncast/android_arm64_armv8-a_rlib_rlib-std/libdowncast.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/fragile/libfragile/android_arm64_armv8-a_rlib_rlib-std/libfragile.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/predicates/libpredicates/android_arm64_armv8-a_rlib_rlib-std/libpredicates.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/predicates-tree/libpredicates_tree/android_arm64_armv8-a_rlib_rlib-std/libpredicates_tree.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/predicates-core/libpredicates_core/android_arm64_armv8-a_rlib_rlib-std/libpredicates_core.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/fallible-iterator/libfallible_iterator/android_arm64_armv8-a_rlib_rlib-std/libfallible_iterator.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/fallible-streaming-iterator/libfallible_streaming_iterator/android_arm64_armv8-a_rlib_rlib-std/libfallible_streaming_iterator.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/hashlink/libhashlink/android_arm64_armv8-a_rlib_rlib-std/libhashlink.rlib`
- `out/soong/.intermediates/external/rust/android-crates-io/crates/hashbrown/libhashbrown/android_arm64_armv8-a_rlib_rlib-std/libhashbrown.rlib`
- `out/soong/.intermediates/system/security/keystore2/aidl/android.security.legacykeystore-rust/android_arm64_armv8-a_rlib_rlib-std/libandroid_security_legacykeystore.rlib`
- `out/soong/.intermediates/system/security/keystore2/libkeystore2/android_arm64_armv8-a_rlib_rlib-std/libkeystore2.rlib`
- `out/soong/.intermediates/system/security/keystore2/keystore2/android_arm64_armv8-a/keystore2.soong_deps`
- `out/soong/.intermediates/system/security/keystore2/keystore2/android_arm64_armv8-a/keystore2.clippy`

## servicemanager (android_arm64_armv8-a)

Exact link target:

`out/soong/.intermediates/frameworks/native/cmds/servicemanager/servicemanager/android_arm64_armv8-a/unstripped/servicemanager`

Missing inputs (5):

- `out/soong/.intermediates/frameworks/native/cmds/servicemanager/servicemanager/android_arm64_armv8-a/obj/frameworks/native/cmds/servicemanager/Access.o`
- `out/soong/.intermediates/frameworks/native/cmds/servicemanager/servicemanager/android_arm64_armv8-a/obj/frameworks/native/cmds/servicemanager/ServiceManager.o`
- `out/soong/.intermediates/frameworks/native/cmds/servicemanager/servicemanager/android_arm64_armv8-a/obj/frameworks/native/cmds/servicemanager/main.o`
- `out/soong/.intermediates/system/libvintf/libvintf/android_arm64_armv8-a_shared/before_final_validations/libvintf.so.toc`
- `out/soong/.intermediates/system/libvintf/libvintf/android_arm64_armv8-a_shared/libvintf.so`

## android.hardware.keymaster@4.0-service (android_vendor_arm64_armv8-a_cfi)

Exact link target:

`out/soong/.intermediates/hardware/interfaces/keymaster/4.0/default/android.hardware.keymaster@4.0-service/android_vendor_arm64_armv8-a_cfi/unstripped/android.hardware.keymaster@4.0-service`

Missing inputs (3):

- `out/soong/.intermediates/hardware/interfaces/keymaster/4.0/default/android.hardware.keymaster@4.0-service/android_vendor_arm64_armv8-a_cfi/obj/hardware/interfaces/keymaster/4.0/default/service.o`
- `out/soong/.intermediates/system/keymaster/libkeymaster4/android_vendor_arm64_armv8-a_shared_cfi/before_final_validations/libkeymaster4.so.toc`
- `out/soong/.intermediates/system/keymaster/libkeymaster4/android_vendor_arm64_armv8-a_shared_cfi/libkeymaster4.so`
