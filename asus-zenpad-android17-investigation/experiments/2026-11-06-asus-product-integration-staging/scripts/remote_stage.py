"""Read pinned old inputs and create one isolated staging directory only."""
from pathlib import Path
import base64
import datetime
import hashlib
import json
import os
import shutil
import sys


def need(value, why):
    if not value:
        raise RuntimeError(why)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(1048576), b''):
            h.update(part)
    return h.hexdigest()


def manifest(root):
    result = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            result[str(p.relative_to(root))] = {'symlink': os.readlink(p)}
        elif p.is_file():
            result[str(p.relative_to(root))] = {'sha256': digest(p)}
    return result


def stage(payload):
    old = Path('/srv/android/asus-build-continuation/integration-r5')
    active = Path('/srv/android/lineage24/device/asus/p00a')
    out = Path('/srv/android/asus-product-integration-staging/r1')
    need(not out.exists(), 'Preserve existing staging revision; do not overwrite')
    for name, expected in payload['handoff_pins'].items():
        need(digest(old / name) == expected, 'Handoff changed: ' + name)
    product = json.loads((old / 'staged-product-receipt.json').read_text())
    need(manifest(active) == product['before'], 'Active product changed')
    need(manifest(old / 'product-device') == product['after'], 'Staged radio product changed')
    inherited = manifest(old / 'product-device')
    net_before = manifest(old / 'platform-connectivity')
    # All source and destination roots are fixed. Preserve the public-key symlink;
    # do not dereference it or copy any external target.
    need(inherited['prebuilt/debug-adb-public-key'] == {
        'symlink': '/srv/android/asus-device-product/debug-adb-public-key'},
        'Unexpected public ADB key link')
    out.mkdir(parents=True)
    try:
        shutil.copytree(old / 'product-device', out / 'product-device', symlinks=True)
        shutil.copytree(old / 'platform-connectivity', out / 'platform-connectivity', symlinks=True)
        shutil.copy2(old / 'Image.gz-dtb', out / 'product-device/prebuilt/Image.gz-dtb')
        cfg = out / 'kernel-config/asus_p00a_combined_defconfig'
        cfg.parent.mkdir()
        shutil.copy2(old / 'resolved.config', cfg)
        board = out / 'product-device/BoardConfig.mk'
        text = board.read_text()
        token = 'TARGET_KERNEL_CONFIG := asus_p00a_defconfig'
        need(text.count(token) == 1, 'Unexpected staged kernel config selection')
        board.write_text(text.replace(token, 'TARGET_KERNEL_CONFIG := asus_p00a_combined_defconfig'))
        for rel, item in payload['packaging_files'].items():
            p = Path(rel)
            need(not p.is_absolute() and '..' not in p.parts, 'Invalid packaging path')
            data = base64.b64decode(item['base64'], validate=True)
            need(hashlib.sha256(data).hexdigest() == item['sha256'], 'Packaging payload changed')
            target = out / 'full-boot-tools' / p
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        final = manifest(out / 'product-device')
        changed = {p: {'before': inherited.get(p), 'after': final.get(p)}
                   for p in inherited.keys() | final.keys() if inherited.get(p) != final.get(p)}
        need(set(changed) == {'BoardConfig.mk', 'prebuilt/Image.gz-dtb'},
             'Unexpected product modifications')
        need(final['prebuilt/Image.gz-dtb']['sha256'] == payload['handoff_pins']['Image.gz-dtb'],
             'Selected prebuilt mismatch')
        need(digest(cfg) == payload['handoff_pins']['resolved.config'], 'Selected config mismatch')
        need(manifest(active) == product['before'], 'Active product changed during preparation')
        need(manifest(old / 'product-device') == inherited, 'Original candidate changed')
        need(manifest(old / 'platform-connectivity') == net_before, 'Original connectivity changed')
        need(manifest(out / 'platform-connectivity') == net_before, 'Copied connectivity changed')
        record = {
            'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'status': 'STAGED_ONLY', 'path': str(out), 'handoff_pins': payload['handoff_pins'],
            'product_before': product['before'], 'product_after': final,
            'changes_from_radio_candidate': changed, 'connectivity': net_before,
            'packaging': {k: v['sha256'] for k, v in payload['packaging_files'].items()},
            'kernel_config_path': str(cfg), 'kernel_config_sha256': digest(cfg),
            'active_product_unchanged': True, 'original_candidates_unchanged': True,
            'active_kernel_written': False, 'build_started': False,
            'firstboot_parity_accepted': False, 'physical_boot_verified': False,
            'full_product_ready': False, 'device_operations': 0,
            'remaining': ['Actual firstboot parity acceptance', 'Original AOSP build terminal',
                          'Locked active integration with source patch and preimage checks',
                          'New complete SDK37 product build and image validation',
                          'Physical probe, rescue and hardware qualification']}
        (out / 'STAGED.json').write_text(json.dumps(record, indent=2) + '\n')
        return record
    except BaseException as e:
        (out / 'FAILED.json').write_text(json.dumps({'error': str(e), 'partial_staging_only': True}) + '\n')
        raise


if __name__ == '__main__':
    print(json.dumps(stage(json.load(sys.stdin)), indent=2))
