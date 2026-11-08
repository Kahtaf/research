#!/usr/bin/env python3
"""Assemble a stock-pair-only rescue image offline, without approving deployment."""
from pathlib import Path
import gzip
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
DELIVERY = WORK / '2026-11-06-asus-android17-target-rescue'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(ok, why):
    if not ok:
        raise ValueError(why)


def main():
    need(__debug__, 'Inherited parsers require non-optimized Python')
    pins = json.loads((DELIVERY / 'SOURCE_PINS.json').read_text())['source_files']
    for name in ['bootformat.py', 'client.py', 'manifest.py']:
        need(sha((DELIVERY / 'source' / name).read_bytes()) == pins['source/' + name],
             'Original parser source changed')
    sys.path.insert(0, str(DELIVERY / 'source'))
    import bootformat as boot
    from client import parse

    source = WORK / '2026-11-06-asus-rescue-block-context-fix/artifacts/candidate-kind-fix/UNTESTED-target-rescue-block-kinds.img'
    original = source.read_bytes()
    need(sha(original) == '299e65cbc1b5290b1e9ef89e0495ca5b8eac63d0d6e486d15611624ba63d35ea',
         'Reviewed context-kind image changed')
    manifest = (ROOT / 'artifacts/rescue.manifest').read_bytes()
    source_receipt = json.loads((ROOT / 'artifacts/rescue.SOURCE.json').read_text())
    need(sha(manifest) == source_receipt['manifest_sha256'], 'Source manifest mismatch')
    rows = parse(manifest)
    need(len(rows) == 2 and [r['part'] for r in rows] == [25, 9], 'Stock pair only')
    need([r['size'] for r in rows] == [3753902080, 16740352], 'Actual stock geometry required')
    need([r['count'] for r in rows] == [3580, 16], 'One-MiB stock chunk tables required')
    need([r['full'].hex() for r in rows] == [
        '4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49',
        '7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'],
        'Exact original image pair required')
    need(len(source_receipt['sources']) == 1 and source_receipt['sources'][0]['full_preflight'],
         'Fresh actual held-SYSTEM-source preflight required')
    h, k, r, tail = boot.parse_image(original)
    need(not tail and sha(k) == 'b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880',
         'Exact stock wrapped kernel required')
    entries = boot.parse_cpio(boot.ungzip(r[512:])[0])
    need(entries['rescue.manifest'][3][:16] == b'ASUSR002\x02\0\0\0\0\0\0\0',
         'Expected non-authorizing source manifest')
    need(sha(entries['file_contexts.bin'][3]) == '7723428608524a84b06144e4d48836c65219fe48503f230070567063b50b3f89',
         'Reviewed block-kind contexts required')
    need(sha(entries['sepolicy'][3]) == '189c477ac73ecb161a6527f7f98a6fec76a913b0d5cf8d11591d440dc79af842',
         'Narrow no-userdata policy required')
    replacement = dict(entries)
    replacement['rescue.manifest'] = (*entries['rescue.manifest'][:3], manifest)
    cpio = boot.make_cpio(replacement)
    need(boot.parse_cpio(cpio) == replacement, 'Cpio reproduction mismatch')
    gz = bytearray(gzip.compress(cpio, compresslevel=9, mtime=0))
    gz[9] = 255
    need(len(gz) <= 0x400000, 'Compressed ramdisk overlaps fixed reservation')
    image = boot.make_image(h, k, boot.wrap(r, bytes(gz)))
    oh, ok, ora, ot = boot.parse_image(image)
    need(not ot and ok == k and oh[64:576] == h[64:576], 'Kernel or command line changed')
    need(boot.parse_cpio(boot.ungzip(ora[512:])[0]) == replacement, 'Actual image payload mismatch')
    need(all(entries[n] == replacement[n] for n in entries if n != 'rescue.manifest'),
         'Unexpected daemon, policy or key change')
    need(len(image) <= boot.PARTITION_SIZE, 'Recovery partition overflow')
    padded_hash = hashlib.sha256(image)
    padded_hash.update(bytes(boot.PARTITION_SIZE - len(image)))
    out = ROOT / 'artifacts/stock-pair-candidate'
    out.mkdir(exist_ok=False)
    name = 'UNTESTED-STOCK-ONLY-commissioning.img'
    (out / name).write_bytes(image)
    contract = dict(mode='PARENT_REVIEW_REQUIRED', armed=True, userdata_enabled=False,
                    manifest_sha256=sha(manifest), p10_full_sha256=padded_hash.hexdigest(),
                    p10_bytes=boot.PARTITION_SIZE, kernel_wrapped_sha256=sha(k),
                    original_recovery_sha256=boot.RECOVERY_SHA, physical_validation=False)
    (out / 'session-contract.UNAPPROVED.json').write_text(json.dumps(contract, indent=2) + '\n')
    report = dict(status='OFFLINE_STOCK_PAIR_ASSEMBLED_DEPLOYMENT_UNAPPROVED', image=name,
                  image_bytes=len(image), image_sha256=sha(image),
                  padded_p10_sha256=padded_hash.hexdigest(), manifest_sha256=sha(manifest),
                  manifest_bytes=len(manifest), manifest_records=2,
                  roles=['original_system', 'original_boot'], userdata_enabled=False,
                  compressed_ramdisk_bytes=len(gz), compressed_ramdisk_start='0x44000000',
                  compressed_ramdisk_end=hex(0x44000000 + len(gz)),
                  source_reviewed_image_sha256=sha(original), changed_cpio_entries=['rescue.manifest'],
                  all_other_cpio_bytes_and_metadata_unchanged=True, kernel_unchanged=True,
                  policy_unchanged=True, block_kind_contexts_unchanged=True,
                  source_receipt_sha256=sha((ROOT / 'artifacts/rescue.SOURCE.json').read_bytes()),
                  deployment_approved=False, device_operations=0, physical_boot_verified=False,
                  full_os_flash_ready=False)
    (out / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
