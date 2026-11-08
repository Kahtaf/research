#!/usr/bin/env python3
"""Generate a file-kind correction only. No device, network or policy mutation."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT.parent / '2026-11-06-asus-android17-target-rescue'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pinned(name):
    path = DELIVERY / 'source' / name
    pins = json.loads((DELIVERY / 'SOURCE_PINS.json').read_text())['source_files']
    assert sha(path.read_bytes()) == pins['source/' + name]
    spec = importlib.util.spec_from_file_location('pinned_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    contexts, boot = pinned('file_contexts.py'), pinned('bootformat.py')
    stock = (DELIVERY / 'inputs/initial/recovery.bin').read_bytes()
    assert sha(stock) == boot.RECOVERY_SHA
    stock_fc = boot.parse_cpio(boot.ungzip(boot.parse_image(stock)[2][512:])[0])['file_contexts.bin'][3]
    before = contexts.derive(stock_fc)
    types = {'rescue_boot_device', 'rescue_system_device', 'rescue_recovery_device',
             'rescue_disk_device', 'rescue_userdata_device'}
    rows, changed = [], []
    for line in before.decode().splitlines():
        fields = line.split()
        if fields[-1].split(':')[2] in types:
            assert len(fields) == 2 and fields[0].startswith('/dev/block/')
            fields.insert(1, '-b')
            changed.append(fields[0])
        rows.append(' '.join(fields))
    assert len(changed) == 9
    after = ('\n'.join(rows) + '\n').encode()
    for old_line, new_line in zip(before.decode().splitlines(), after.decode().splitlines()):
        assert old_line == new_line or old_line.split() == [new_line.split()[0], new_line.split()[2]]
    out = ROOT / 'artifacts'
    out.mkdir(exist_ok=True)
    path = out / 'file_contexts'
    with path.open('xb') as stream:
        stream.write(after)
    receipt = {'old_context_text_sha256': sha(before), 'new_context_text_sha256': sha(after),
               'changed_rows': changed, 'operation': 'Add block-only -b selector; no rule/type/permission added',
               'policy_unchanged_sha256': '189c477ac73ecb161a6527f7f98a6fec76a913b0d5cf8d11591d440dc79af842',
               'device_operations': 0, 'physical_qualified': False}
    (out / 'source-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
