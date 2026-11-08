from pathlib import Path
import json,shutil,hashlib,difflib,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];C=R/'candidate';D=C/'device/asus/p00a';V=D/'vintf-legacy';K=V/'p-4.9';K.mkdir(parents=True,exist_ok=True)
U=R/'upstream/s/p/android-4.9'
files=['android-base.config','android-base-arm.config','android-base-arm64.config','android-base-conditional.xml']
for f in files:shutil.copy2(U/(f+'.decoded'),K/f)
# Preserve the complete historical HAL catalog, including original optional annotations.
shutil.copy2(R/'upstream/interfaces/compatibility_matrices/compatibility_matrix.3.xml.decoded',V/'compatibility_matrix.p00a-p.xml')
manifest=(R/'inputs/sources/device/asus/p00a/manifest.xml').read_text()
assert '<manifest version="1.0" type="device">' in manifest
manifest=manifest.replace('<manifest version="1.0" type="device">','<manifest version="1.0" type="device" target-level="3">\n    <kernel target-level="3" />',1)
(D/'manifest.xml').write_text(manifest)
mk=(R/'inputs/sources/device/asus/p00a/device.mk').read_text()
assert 'p00a_experimental_legacy_fcm3.xml' not in mk
(D/'device.mk').write_text(mk+'\n# Experimental retrofit contract; preserves the SDK37 framework matrices.\nPRODUCT_PACKAGES += p00a_experimental_legacy_fcm3.xml\n')
(V/'Android.bp').write_text('''// Experimental P00A retrofit profile; not an Android 17 launch/CTS claim.
package {
    default_applicable_licenses: ["Android-Apache-2.0"],
}

kernel_config {
    name: "p00a_kernel_config_p_4_9",
    srcs: [
        "p-4.9/android-base.config",
        "p-4.9/android-base-arm.config",
        "p-4.9/android-base-arm64.config",
    ],
    meta: "p-4.9/android-base-conditional.xml",
}

vintf_compatibility_matrix {
    name: "p00a_experimental_legacy_fcm3.xml",
    stem: "compatibility_matrix.p00a-legacy.xml",
    srcs: ["compatibility_matrix.p00a-p.xml"],
    kernel_configs: ["p00a_kernel_config_p_4_9"],
}
''')
provenance=json.loads((R/'evidence/upstream-provenance.json').read_text())
(V/'PROVENANCE.json').write_text(json.dumps({'purpose':'Experimental retrofit FCM3/P kernel contract for original API23 device on SDK37; not OEM launch history or official CTS support','kernel_configs_commit':provenance['roots']['s']['commit'],'kernel_source_directory':'p/android-4.9','hardware_interfaces_commit':provenance['roots']['interfaces']['commit'],'hal_matrix_path':'compatibility_matrices/compatibility_matrix.3.xml','sha256':{f:hashlib.sha256((K/f).read_bytes()).hexdigest() for f in files},'historical_hal_catalog_sha256':hashlib.sha256((V/'compatibility_matrix.p00a-p.xml').read_bytes()).hexdigest(),'unmodified_files':files+['compatibility_matrix.p00a-p.xml'],'keep_existing_sdk37_matrices':True},indent=2)+'\n')
patch=''
for p in sorted(D.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(C);old=R/'inputs/sources'/rel
 before=old.read_text().splitlines(True) if old.exists() else []
 patch+=''.join(difflib.unified_diff(before,p.read_text().splitlines(True),fromfile='a/'+str(rel) if old.exists() else '/dev/null',tofile='b/'+str(rel)))
(C/'integration.patch').write_text(patch)
# Explicitly record the complete inherited historical presence obligations; SDK37 does not enforce optional=false itself.
hals=E.parse(V/'compatibility_matrix.p00a-p.xml').getroot().findall('hal')
(R/'evidence/historical-hal-contracts.json').write_text(json.dumps({'total_catalog_entries':len(hals),'required_in_historical_source':[E.tostring(x,encoding='unicode') for x in hals if x.get('optional')=='false'],'catalog_copied_byte_for_byte':True},indent=2)+'\n')
print('Staged',len(list(D.rglob('*'))),'paths; P matrix HAL entries:',len(hals))
