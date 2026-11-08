"""Reject source configuration paths before any native build; no Soong fallback."""
from pathlib import Path, PurePosixPath
import shlex
import sys
from integrate import need, read, sha, safe, write, manifest

POLICY_VARS = (
    'BOARD_SEPOLICY_DIRS', 'BOARD_VENDOR_SEPOLICY_DIRS', 'BOARD_ODM_SEPOLICY_DIRS',
    'SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS', 'SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS',
    'PRODUCT_PUBLIC_SEPOLICY_DIRS', 'PRODUCT_PRIVATE_SEPOLICY_DIRS',
    'BOARD_SYSTEM_EXT_SEPOLICY_PREBUILT_DIRS', 'BOARD_PRODUCT_SEPOLICY_PREBUILT_DIRS',
    'SEPOLICY_FREEZE_TEST_EXTRA_DIRS', 'SEPOLICY_FREEZE_TEST_EXTRA_PREBUILT_DIRS')
MANIFEST_VARS = ('DEVICE_MANIFEST_FILE', 'DEVICE_FRAMEWORK_MANIFEST_FILE', 'PRODUCT_MANIFEST_FILES',
                 'SYSTEM_EXT_MANIFEST_FILES', 'SYSTEM_EXT_HWSERVICE_FILES', 'ODM_MANIFEST_FILES')

def verify(path, plan):
    values = {}
    for line in path.read_text().splitlines():
        key, sep, raw = line.partition('=')
        need(sep and key not in values, 'CONFIG_PATH_ERROR: malformed/duplicate dumpvars key: ' + key)
        values[key] = ' '.join(shlex.split(raw)).split()
    need(set(POLICY_VARS + MANIFEST_VARS) <= set(values), 'CONFIG_PATH_ERROR: missing requested path variable')
    aosp = Path(plan['aosp']).resolve()
    for key in POLICY_VARS + MANIFEST_VARS:
        entries = values[key]
        need(len(entries) == len(set(entries)), 'CONFIG_PATH_ERROR: duplicate path in ' + key)
        for rel in entries:
            p = PurePosixPath(rel)
            need(rel and not p.is_absolute() and '..' not in p.parts and str(p) == rel and '$' not in rel and '*' not in rel,
                 'CONFIG_PATH_ERROR: path must be canonical source-relative: ' + key + '=' + rel)
            target = safe(aosp, rel)
            need(target.resolve().is_relative_to(aosp), 'CONFIG_PATH_ERROR: source path escape: ' + rel)
            need(target.is_dir() if key in POLICY_VARS else target.is_file(),
                 'CONFIG_PATH_ERROR: missing policy directory/manifest: ' + key + '=' + rel)
    vendor = values['BOARD_VENDOR_SEPOLICY_DIRS'] + values['BOARD_SEPOLICY_DIRS']
    need(len(vendor) == len(set(vendor)), 'CONFIG_PATH_ERROR: duplicate effective vendor policy directory')
    sensor = 'device/asus/p00a/sensors'
    need(vendor.count(sensor + '/sepolicy') == 1, 'CONFIG_PATH_ERROR: missing/duplicate exact sensor policy directory')
    need(values['DEVICE_MANIFEST_FILE'].count(sensor + '/manifest.xml') == 1,
         'CONFIG_PATH_ERROR: missing/duplicate exact sensor DEVICE_MANIFEST_FILE')
    expected = read(plan['staged_receipt'])['product_after']
    policy = manifest(aosp / sensor / 'sepolicy')
    need(policy == {p.removeprefix('sensors/sepolicy/'): row for p,row in expected.items() if p.startswith('sensors/sepolicy/')},
         'CONFIG_PATH_ERROR: sensor policy bytes differ from reviewed source')
    sensor_manifest = aosp / sensor / 'manifest.xml'
    need(sha(sensor_manifest) == expected['sensors/manifest.xml']['sha256'], 'CONFIG_PATH_ERROR: sensor manifest bytes changed')
    need(sha(aosp / sensor / 'BoardConfig.mk') == expected['sensors/BoardConfig.mk']['sha256'], 'CONFIG_PATH_ERROR: sensor BoardConfig is not r7 postimage')
    return dict(dumpvars_sha256=sha(path),policy_dirs={k:values[k] for k in POLICY_VARS},
                manifests={k:values[k] for k in MANIFEST_VARS}, sensor_policy=policy,
                sensor_manifest_sha256=sha(sensor_manifest), sensor_board_sha256=sha(aosp/sensor/'BoardConfig.mk'),
                source_configuration_paths_verified=True, native_compilation_started_by_this_check=False)

if __name__ == '__main__':
    try:
        path, root, output = map(Path, sys.argv[1:])
        write(output, verify(path, read(root / 'inputs/plan.json')))
        print('Actual dumpvars: all policy directories/manifests are relative and present; exact sensor paths verified.')
    except (RuntimeError, OSError, ValueError) as error:
        raise SystemExit('CONFIG_PATH_ERROR before native compilation: ' + str(error))
