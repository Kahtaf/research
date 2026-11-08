#!/usr/bin/env python3
"""Offline source/config contract audit. This is not an Android build or boot."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'evidence/source'
STAGED = ROOT / 'stagedsource/device/asus/p00a/firstboot'
checks = []


def read(path):
    return (SRC / path).read_text()


def check(name, condition, basis):
    checks.append({'name': name, 'passed': bool(condition), 'basis': basis})
    if not condition:
        raise AssertionError(name)


manifest = json.loads((ROOT / 'evidence/source-sha256.json').read_text())
check('Captured source hashes match', all(
    hashlib.sha256((SRC / name).read_bytes()).hexdigest() == entry['sha256']
    for name, entry in manifest.items() if 'sha256' in entry
), 'All successfully captured files; missing-path probes are recorded separately.')

concurrent = json.loads((ROOT / 'evidence/concurrent-inputs-sha256.json').read_text())
for name, entry in concurrent.items():
    data = (ROOT / 'evidence/concurrent-inputs' / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == entry['sha256']
    if name != 'device.mk':
        assert not re.search(r'keymint|keymaster|keystore|gatekeeper|authsecret', data.decode(), re.I)

chain = [('full_base.mk', 'generic_no_telephony.mk'),
         ('generic_no_telephony.mk', 'handheld_system.mk'),
         ('handheld_system.mk', 'media_system.mk'),
         ('media_system.mk', 'base_system.mk'),
         ('generic_no_telephony.mk', 'handheld_system_ext.mk'),
         ('handheld_system_ext.mk', 'media_system_ext.mk'),
         ('media_system_ext.mk', 'base_system_ext.mk')]
check('Product inheritance reaches keystore and legacy service manager',
      all(b in read('build/make/target/product/' + a) for a, b in chain)
      and 'keystore2 \\' in read('build/make/target/product/base_system.mk')
      and 'gatekeeperd \\' in read('build/make/target/product/base_system.mk'),
      'Captured full_base -> generic_no_telephony -> handheld -> media -> base files.')

base_ext = read('build/make/target/product/base_system_ext.mk')
main_mk = read('build/make/core/main.mk')
check('Shipping API 23 selects inherited hwservicemanager',
      re.search(r'PRODUCT_PACKAGES_SHIPPING_API_LEVEL_34\s*\+=\s*\\\s*hwservicemanager', base_ext)
      and 'math_gt_or_eq,34,$(PRODUCT_SHIPPING_API_LEVEL)' in main_mk and 34 >= 23,
      'base_system_ext.mk and main.mk shipping-API comparison; not a new Kati evaluation.')
hidl_vars = json.loads((ROOT / 'evidence/hidl-manifest-buildvars.json').read_text())
check('Inherited HIDL manager also has its framework manifest input',
      'system/hwservicemanager/hwservicemanager.xml' in hidl_vars['SystemExtManifestFiles']
      and '$(filter hwservicemanager,$(PRODUCT_PACKAGES_SHIPPING_API_LEVEL_34))' in read('build/make/core/soong_config.mk')
      and '<name>android.hidl.manager</name>' in read('system/hwservicemanager/hwservicemanager.xml'),
      'Existing product Soong variables plus soong_config.mk; final merged manifest/max-level requires build inspection.')
state = json.loads((ROOT / 'evidence/build-state.json').read_text())
vars_ = state['existing_output_only']['out/soong/soong.lineage_p00a.variables']
check('Existing builder variables are SDK 37 / ship 23',
      vars_['Platform_sdk_version'] == 37 and vars_['Shipping_api_level'] == '23',
      'Read-only existing minimal-product Soong variables; full-product variables remain to be built.')

bp = read('hardware/interfaces/keymaster/4.0/default/Android.bp')
cpp = read('hardware/interfaces/keymaster/4.0/default/service.cpp')
rc = read('hardware/interfaces/keymaster/4.0/default/ACCOUNT_REDACTED')
check('Selected platform package is a real software Keymaster',
      'name: "android.hardware.keymaster@4.0-service"' in bp
      and 'CreateKeymasterDevice(SecurityLevel::SOFTWARE)' in cpp
      and 'registerAsService()' in cpp and 'joinRpcThreadpool()' in cpp,
      'Unmodified upstream default service and build module.')
check('No implicit hardware-keystore feature or duplicate manifest in selected module',
      'required:' not in bp and 'vintf_fragments:' not in bp
      and 'init_rc: ["ACCOUNT_REDACTED"]' in bp,
      'Keymaster 4.0 Android.bp (4.1 and C++ KeyMint targets have different dependencies).')
check('Upstream service starts before post-fs-data',
      'class early_hal' in rc
      and 'interface android.hardware.keymaster@4.0::IKeymasterDevice default' in rc,
      'Unmodified upstream init service; no additional rc installed.')
fc = read('system/sepolicy/vendor/file_contexts')
label_match = any(re.fullmatch(line.split()[0], '/system/vendor/bin/hw/android.hardware.keymaster@4.0-service')
                  and line.split()[1] == 'u:object_r:hal_keymaster_default_exec:s0'
                  for line in fc.splitlines() if line.strip() and not line.startswith('#'))
check('Existing SELinux executable label matches nested vendor layout', label_match
      and 'init_daemon_domain(hal_keymaster_default)' in read('system/sepolicy/vendor/hal_keymaster_default.te'),
      'Platform vendor file_contexts and default keymaster domain; policy compilation still required.')

xml = ET.parse(STAGED / 'manifest-keymaster.xml').getroot()
hal = xml.find('hal')
check('Staged VINTF matches real HIDL registration',
      xml.attrib == {'version': '1.0', 'type': 'device'} and len(xml.findall('hal')) == 1
      and hal.attrib['format'] == 'hidl'
      and hal.findtext('name') == 'android.hardware.keymaster'
      and hal.findtext('transport') == 'hwbinder'
      and hal.findtext('fqname') == '@4.0::IKeymasterDevice/default',
      'Parsed XML against platform package rc and service; assembled VINTF is a parent build check.')

compat = read('system/security/keystore2/src/km_compat/km_compat.cpp')
globals_ = read('system/security/keystore2/src/globals.rs')
check('Keystore supports insecure default legacy HAL without inventing a TEE',
      'result[SecurityLevel::TRUSTED_ENVIRONMENT] = result[SecurityLevel::SOFTWARE]' in compat
      and 'securityLevel_ = convert(result.securityLevel)' in compat
      and '_aidl_return->securityLevel = securityLevel_' in compat
      and 'keystore2_km_compat::add_keymint_device_service()' in globals_,
      'Existing adapter routing slot and getHardwareInfo conversion are distinct.')
check('Software key characteristics retain software enforcement',
      'securityLevel == KeyMintSecurityLevel::SOFTWARE\n                                                         ? legacyKc.softwareEnforced' in compat
      and 'hw_info.securityLevel' in read('system/security/keystore2/src/raw_device.rs')
      and 'if (GetSecurityLevel() != KM_SECURITY_LEVEL_SOFTWARE)' in read('system/keymaster/contexts/pure_soft_keymaster_context.cpp'),
      'km_compat characteristic conversion, raw_device security level, PureSoftKeymasterContext.')
boot_keys = read('system/security/keystore2/src/boot_level_keys.rs')
check('Legacy boot key strategy performs real cryptography',
      'DenyLaterStrategy::MaxUsesPerBoot' in boot_keys and 'KeyParameterValue::MaxUsesPerBoot(1)' in boot_keys
      and 'KeyPurpose::SIGN' in boot_keys and 'b"Create boot level key"' in boot_keys,
      'The pre-4.1 path uses HMAC/MAX_USES_PER_BOOT; runtime key generation/signing is still required.')
maintenance = read('system/security/keystore2/src/maintenance.rs')
check('Module hash version gate legitimately accepts legacy Keymaster',
      'pub const KEYMINT_V4: i32 = 400' in maintenance
      and 'if hw_info.versionNumber < min_version' in maintenance
      and 'Some(KEYMINT_V4)' in maintenance
      and '_aidl_return->versionNumber = result.majorVersion * 10 + result.minorVersion' in compat,
      'KM4.0 reports normalized version 40, below 400; no new success path is introduced.')
check('Keystore still measures active APEX modules and sets its own completion property',
      'apexd.getActivePackages()' in maintenance
      and 'digest::Sha256::hash(&encoding)' in maintenance
      and 'Self::set_module_info(modules).unwrap_or_else' in maintenance
      and 'system_properties::write("keystore.module_hash.sent", "true")' in maintenance,
      'Unmodified platform maintenance.rs.')

init = read('system/core/rootdir/init.rc')
gate = init.index('wait_for_prop apexd.status activated')
check('Ordered init waits and final APEX configuration remain intact',
      gate < init.index('wait_for_prop keystore.module_hash.sent true')
      < init.index('perform_apex_config', gate),
      'Captured platform init.rc; no platform patch is staged.')
check('Default APEX namespace gates adbd startup',
      'StartDelayedServices()' in read('system/core/init/builtins.cpp')
      and 'DelayService(*this)' in read('system/core/init/service.cpp')
      and 'updatable' in read('system/core/rootdir/init.usb.rc')
      and '/apex/com.android.adbd/bin/adbd' in read('packages/modules/adb/apex/adbd.rc'),
      'perform_apex_config, delayed updatable services, ADB APEX override; USB runtime is untested.')

product = (STAGED / 'firstboot-services.mk').read_text()
fixture = 'DEVICE_MANIFEST_FILE := original.xml\n' + product + '\n' + (ROOT / 'configsnippets/BoardConfig.mk.inc').read_text() + '''
.PHONY: audit
audit:
\t@printf '%s\\n' '$(PRODUCT_PACKAGES)' '$(PRODUCT_SYSTEM_PROPERTIES)' '$(DEVICE_MANIFEST_FILE)'
'''
out = subprocess.check_output(['make', '--no-print-directory', '-f', '-', 'audit'], input=fixture, text=True).splitlines()
check('GNU Make evaluates minimal integration snippets',
      out == ['android.hardware.keymaster@4.0-service', 'apexd.config.use_fiemap=false',
              'original.xml device/asus/p00a/firstboot/manifest-keymaster.xml'],
      'Actual local Make evaluation of additions; not full Android product inheritance/Kati.')
check('Configured post-data APEX mode is supported on both sides',
      'if (!base::GetBoolProperty(kApexdUseFiemapProp, true))' in read('system/core/init/apex_init_util.cpp')
      and 'if (android::base::GetBoolProperty("apexd.config.use_fiemap", true))' in read('system/apex/apexd/apexd_main.cpp')
      and 'false, /* mount_before_data */' in read('system/apex/apexd/apexd.h')
      and 'false, /* uses_pinned_apex */' in read('system/apex/apexd/apexd.h'),
      'Init chooses two namespaces; apexd leaves pinned and mount-before-data modes false.')
check('Missing APEX session metadata is tolerated on fresh activation',
      "if (walk_status.error().code() != ENOENT)" in read('system/apex/apexd/apexd_session.cpp')
      and 'No sessions to revert/activate.' in read('system/apex/apexd/apexd.cpp'),
      'GetSessions returns empty; ProcessSessions returns; this does not validate staged updates.')
check('Unencrypted user-zero path exists without kernel fscrypt',
      'property_get("ro.crypto.type", value, "none")' in read('system/extras/libfscrypt/fscrypt.cpp')
      and 'if (IsFbeEnabled())' in read('system/core/init/builtins.cpp')
      and 'bool fscrypt_init_user0()' in read('system/vold/FsCrypt.cpp'),
      'Non-FBE mkdir and vold user storage paths; no ro.crypto override is staged.')
scratch = (ROOT / 'configsnippets/fstab.mt8163.external-scratch.in').read_text()
rows = [l.split() for l in scratch.splitlines() if l.strip() and not l.startswith('#')]
check('Scratch template has no stock data or metadata mount',
      len(rows) == 3 and all(len(r) == 5 for r in rows)
      and [r[0] for r in rows if r[1] == '/data'] == ['@EXTERNAL_SCRATCH_DATA_BLOCK@']
      and all(r[1] not in ['/cache', '/metadata'] for r in rows)
      and not any('userdata' in r[0] for r in rows)
      and rows[1][4] == 'wait,latemount',
      'Non-installable template: external path/identity is explicitly unresolved.')
loop = read('system/apex/apexd/apexd_loop.cpp')
check('Plain tmpfs scratch is not assumed to support APEX mounting',
      'O_RDONLY | O_CLOEXEC | O_DIRECT' in loop and 'TMPFS_MAGIC' not in loop
      and all(s in loop for s in ['EROFS_SUPER_MAGIC_V1', 'SQUASHFS_MAGIC', 'OVERLAYFS_SUPER_MAGIC']),
      'Loop-backed APEX open fallback whitelist excludes tmpfs.')
check('AuthSecret and credentialless Gatekeeper exclusions have source basis',
      'if (mAuthSecretService == null)' in read('frameworks/base/services/core/java/com/android/server/locksettings/LockSettingsService.java')
      and 'However, skip GK when the LSKF is empty.' in read('frameworks/base/services/core/java/com/android/server/locksettings/SyntheticPasswordManager.java'),
      'No AuthSecret HAL or credential-accepting stub is added; lockscreen setup is a separate test.')
staged_text = '\n'.join(p.read_text() for p in (ROOT / 'stagedsource').rglob('*') if p.is_file())
check('Integration adds no readiness spoof, fake service, crypto override or hardware feature',
      not any(x in staged_text for x in ['setprop ', 'ro.crypto.', 'ro.apex.updatable=false',
                                         'android.hardware.hardware_keystore', 'cc_binary', 'rust_binary']),
      'Only existing package selection, supported configuration property, and VINTF fragment.')

result = {
    'passed': len(checks), 'checks': checks,
    'limitations': ['No VM write or build', 'No Kati/Soong/full product evaluation',
                    'No C++/Rust or SELinux/VINTF compilation', 'No Android init parser execution',
                    'No boot, data mount, APEX activation, crypto-operation or USB runtime test'],
    'staged_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for dirname in ['stagedsource', 'configsnippets']
                      for p in sorted((ROOT / dirname).rglob('*')) if p.is_file()},
}
(ROOT / 'evidence/validation.json').write_text(json.dumps(result, indent=2) + '\n')
print(f'{len(checks)} offline source/config checks passed; no compilation or runtime claim.')
