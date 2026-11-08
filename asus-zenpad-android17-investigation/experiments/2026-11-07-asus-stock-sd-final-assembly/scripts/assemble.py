"""Parent-local final join; never deploys, arms a card, or fabricates admissions."""
from pathlib import Path
import argparse
import gzip
import importlib.util
import json
import os
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent / '2026-11-07-asus-stock-kernel-sd-rescue'
sys.path.insert(0, str(BASE / 'source'))
import bootformat as b
from package_core import package, KERNEL_SHA

spec = importlib.util.spec_from_file_location('stock_final_admission', BASE / 'scripts/final_package.py')
admit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admit)
ordinary = admit.ordinary
MANIFEST_SHA = '9fe4ec15800257262092f11698525939ebdfb404e150fbc7d308c7f8280ba534'
POLICY_SHA = 'b922a37875f68a13f1f4133f4356478fdaca692d8cb62cfb4afdec226dbde584'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--arm-file', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args()
    manifest = ordinary(args.manifest, 1024**2)
    roles = admit.five_roles(manifest)
    if b.sha(manifest) != MANIFEST_SHA:
        raise ValueError('exact parent-admitted final five-role manifest required')
    original = ordinary(BASE / 'inputs/original-stock.manifest', 128 * 1024)
    if (b.sha(original) != '605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47'
            or manifest[16:112] != original[16:112]
            or manifest[112:len(original)] != original[112:]):
        raise ValueError('exact original-pair prefix required')
    arm = ordinary(args.arm_file, 65)
    if (len(arm) != 65 or arm[-1:] != b'\n'
            or any(c not in b'0123456789abcdef' for c in arm[:64])
            or arm[:64] == b'0' * 64):
        raise ValueError('existing real parent arm ID required')
    for rel, pin in json.loads((BASE / 'evidence/DELIVERY_PINS.json').read_text()).items():
        if b.sha(ordinary(BASE / rel, 8 * 1024**2)) != pin:
            raise ValueError('delivered stock core changed: ' + rel)
    common = ordinary(BASE / 'artifacts/common-rootfs.cpio.gz', 4 * 1024**2)
    entries = b.parse_cpio(gzip.decompress(common))
    before = dict(entries)
    policy_path = ROOT.parent / '2026-11-07-asus-stock-sd-mount-policy/artifacts/sepolicy'
    policy = ordinary(policy_path, 1024**2)
    if (b.sha(policy) != POLICY_SHA
            or b.sha(entries['sepolicy'][3]) != 'e559a17ee13b141ceca868df7311bee2e095cf340afee2fedb549d314b5cad11'):
        raise ValueError('exact physically exercised policy correction required')
    entries['sepolicy'] = (*entries['sepolicy'][:3], policy)
    if [name for name in entries if entries[name] != before[name]] != ['sepolicy']:
        raise ValueError('unexpected common-rootfs delta')
    assert 'rescue.manifest' not in entries and 'rescue.sd.arm' not in entries
    assert b'start rescue-sd-offline' not in entries['init.rc'][3]
    entries['rescue.manifest'] = (0o100444, 0, 0, manifest)
    entries['rescue.sd.arm'] = (0o100444, 0, 0, arm)
    action = ordinary(BASE / 'source/init.offline.action.rc', 4096)
    entries['init.rc'] = (0o100644, 0, 0, entries['init.rc'][3] + b'\n' + action)
    assert entries['init.rc'][3].count(b'start rescue-sd-offline') == 1
    assert 'system/bin/sh' not in entries and 'sbin/adbd' not in entries
    assert 'sbin/p10-restore' in entries and entries['rescue.original.manifest'][3] == original
    stock_path = ROOT.parent / '2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin'
    stock = ordinary(stock_path, b.PARTITION_SIZE)
    if len(stock) != b.PARTITION_SIZE or b.sha(stock) != b.RECOVERY_SHA:
        raise ValueError('exact original recovery required')
    header, kernel, rd, _ = b.parse_image(stock)
    assert b.sha(kernel) == KERNEL_SHA
    image, members, contract = package(entries, kernel, header, kernel[:512], rd[:512])
    padded = image + bytes(b.PARTITION_SIZE - len(image))
    args.output_dir.mkdir(mode=0o700)

    def write(name, data):
        fd = os.open(args.output_dir / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

    write('candidate.img', image)
    write('candidate.p10.raw', padded)
    write('operational-ramdisk.members', members)
    binding = b.parse_cpio(members[contract['core_gzip_bytes']:])['rescue.current.binding'][3]
    write('rescue.current.binding', binding)
    mid = b.sha(manifest).encode()
    write('execute.trigger', b'OFFLINE-PREARMED ASUSR002 ' + mid + b' ' + arm[:64] + b' install:2,4,3\n')
    for name, selection in [('asus-rescue.mode.install', b'INSTALL'), ('asus-rescue.mode.stock', b'STOCK-RESTORE')]:
        write(name, b'OFFLINE-SELECT ASUSR002 ' + mid + b' ' + arm[:64] + b' ' + selection + b'\n')
    for role, name in [(0, 'system.trigger'), (1, 'boot.trigger')]:
        write(name, b'OFFLINE-PREARMED ASUSR002 ' + mid + b' ' + arm[:64] + (' rollback:%d:inverse:-1\n' % role).encode())
    write('manifest.sha256', mid + b'\n')
    receipt = dict(status='ASSEMBLED_NOT_DEPLOYED_NOT_FLASH_APPROVAL', manifest_sha256=MANIFEST_SHA,
                   roles=roles, image_bytes=len(image), image_sha256=b.sha(image),
                   p10_bytes=len(padded), p10_sha256=b.sha(padded), packaging=contract,
                   policy_sha256=POLICY_SHA, common_delta=['sepolicy'],
                   production_executables_unchanged=True, normal_install_order=[2, 4, 3],
                   normal_graph_keeps_custom_recovery=True, stock_fallback_explicit=True,
                   stock_success_outcome='OEM_RESET_REQUIRED', stock_success_reboot='POWER_OFF',
                   card_armed=False, device_contacted=False, physical_linux49_boot_proven=False,
                   complete_card_source_preflight_proven=False)
    write('assembly.json', (json.dumps(receipt, indent=2) + '\n').encode())
    d = os.open(args.output_dir, os.O_RDONLY | os.O_DIRECTORY)
    os.fsync(d)
    os.close(d)
    (ROOT / 'evidence/assembly.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ['status', 'image_bytes', 'image_sha256', 'p10_sha256', 'card_armed']}))


if __name__ == '__main__':
    main()
