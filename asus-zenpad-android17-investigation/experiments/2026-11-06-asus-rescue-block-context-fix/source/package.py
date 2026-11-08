#!/usr/bin/env python3
"""Package only the compiled inode-kind fix into a NEW unarmed recovery image."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT.parent / '2026-11-06-asus-android17-target-rescue'
spec = importlib.util.spec_from_file_location('prepare', ROOT / 'source/prepare.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)
boot = prepare.pinned('bootformat.py')
contexts = prepare.pinned('file_contexts.py')


def main():
    import gzip
    original = (DELIVERY / 'artifacts/candidate-delivery/UNTESTED-target-rescue.img').read_bytes()
    assert boot.sha(original) == '93d647ea58784aefe4104cb0cbddbac04fe6169b30923ad63c5684e0dc920419'
    h, k, r, tail = boot.parse_image(original)
    assert not tail and b'initrd=' not in h[64:576] and len(h[64:576].split(b'\0')[0]) == 68
    entries = boot.parse_cpio(boot.ungzip(r[512:])[0])
    new_contexts = (ROOT / 'evidence/compiled-validation/file_contexts.bin').read_bytes()
    assert boot.sha(new_contexts) == '7723428608524a84b06144e4d48836c65219fe48503f230070567063b50b3f89'
    before = contexts.extract(entries['file_contexts.bin'][3])
    after = contexts.extract(new_contexts)
    assert len(before) == len(after)
    # Stock context rows can share a regex across inode kinds; compare multisets,
    # rather than treating a regex-only dictionary as complete provenance.
    from collections import Counter
    expected = Counter(before)
    changed = []
    for row in before:
        if row[2].split(':')[2].startswith('rescue_') and row[2].split(':')[2].endswith('_device'):
            assert row[1] == ''
            expected[row] -= 1
            expected[(row[0], '-b', row[2])] += 1
            changed.append(row[0])
    assert len(changed) == 9 and +expected == Counter(after)
    replacement = dict(entries)
    replacement['file_contexts.bin'] = (*entries['file_contexts.bin'][:3], new_contexts)
    assert all(replacement[n] == entries[n] for n in entries if n != 'file_contexts.bin')
    assert boot.sha(entries['sepolicy'][3]) == '189c477ac73ecb161a6527f7f98a6fec76a913b0d5cf8d11591d440dc79af842'
    assert entries['rescue.manifest'][3][:16] == b'ASUSR002\x02\0\0\0\0\0\0\0'
    cpio = boot.make_cpio(replacement)
    assert boot.parse_cpio(cpio) == replacement
    gz = bytearray(gzip.compress(cpio, compresslevel=9, mtime=0))
    gz[9] = 255
    image = boot.make_image(h, k, boot.wrap(r, bytes(gz)))
    new_h, new_k, new_r, new_tail = boot.parse_image(image)
    assert not new_tail and new_k == k and new_h[64:576] == h[64:576]
    assert 0x44000000 + len(gz) < 0x44400000
    out = ROOT / 'artifacts/candidate-kind-fix'
    out.mkdir(exist_ok=False)
    name = 'UNTESTED-target-rescue-block-kinds.img'
    (out / name).write_bytes(image)
    report = {'status': 'UNARMED_CONTEXT_KIND_FIX_PHYSICAL_UNPROVED', 'candidate': name,
              'image_bytes': len(image), 'image_sha256': boot.sha(image),
              'padded_p10_sha256': boot.sha(image + bytes(boot.PARTITION_SIZE - len(image))),
              'source_image_sha256': boot.sha(original), 'changed_cpio_entries': ['file_contexts.bin'],
              'context_mode_rows_changed': changed, 'compiled_contexts_sha256': boot.sha(new_contexts),
              'policy_unchanged_sha256': boot.sha(entries['sepolicy'][3]),
              'kernel_unchanged_sha256': boot.sha(k), 'all_other_cpio_bytes_unchanged': True,
              'header_cmdline_unchanged': True, 'ramdisk_payload_bytes': len(gz),
              'lk_modeled_payload_range': [hex(0x44000000), hex(0x44000000 + len(gz))],
              'manifest_records': 0, 'armed': False, 'physical_validation': False,
              'device_operations': 0, 'full_os_flash_ready': False}
    (out / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
