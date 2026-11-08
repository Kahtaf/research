"""Use the independent review parser to verify the actual two-role container."""
from pathlib import Path
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if not __debug__:
        raise RuntimeError('Independent bounded parser requires assertions')
    parser = WORK / '2026-11-06-asus-rescue-independent-review/scripts/verify_variant.py'
    text = parser.read_text()
    prefix, marker, _ = text.partition('old,ok,orr,oe,om=unpack(')
    assert marker
    namespace = {'__file__': str(parser)}
    # Only its imports and independent unpack function definitions execute.
    # Its original top-level artifact checks and output writes do not execute.
    exec(compile(prefix, str(parser), 'exec'), namespace)
    unpack = namespace['unpack']
    base = WORK / '2026-11-06-asus-rescue-block-context-fix/artifacts/candidate-kind-fix/UNTESTED-target-rescue-block-kinds.img'
    out = ROOT / 'artifacts/stock-pair-candidate'
    new = out / 'UNTESTED-STOCK-ONLY-commissioning.img'
    oldbytes, oldkernel, oldram, oldentries, _ = unpack(base)
    data, kernel, ram, entries, geometry = unpack(new)
    assert sha(oldbytes) == '299e65cbc1b5290b1e9ef89e0495ca5b8eac63d0d6e486d15611624ba63d35ea'
    assert kernel == oldkernel and data[64:576] == oldbytes[64:576]
    normalized = bytearray(data[:2048])
    normalized[16:20] = oldbytes[16:20]
    normalized[576:608] = oldbytes[576:608]
    assert bytes(normalized) == oldbytes[:2048]
    assert ram[:4] == oldram[:4] and ram[8:512] == oldram[8:512]
    assert set(entries) == set(oldentries)
    assert [n for n in entries if entries[n] != oldentries[n]] == ['rescue.manifest']
    assert entries['rescue.manifest'][:3] == oldentries['rescue.manifest'][:3]
    binary = entries['rescue.manifest'][3]
    assert binary == (ROOT / 'artifacts/rescue.manifest').read_bytes()
    assert binary[:16] == b'ASUSR002\x02\0\0\0\x02\0\0\0'
    assert binary[16:112] == oldentries['rescue.manifest'][3][16:112]
    pos = 112
    rows = []
    expected = [(0, 25, 3753902080, 3580, '4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49'),
                (1, 9, 16740352, 16, '7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316')]
    for role, part, size, count, digest in expected:
        assert struct.unpack_from('<IIQ', binary, pos) == (role, part, size)
        assert binary[pos + 16:pos + 48].hex() == digest
        assert struct.unpack_from('<I', binary, pos + 48)[0] == count
        pos += 52
        table = binary[pos:pos + count * 32]
        assert len(table) == count * 32
        rows.append(dict(role=role, part=part, bytes=size, chunks=count,
                         sha256=digest, chunk_table_sha256=sha(table)))
        pos += count * 32
    assert pos == len(binary) == 115288
    assert len(ram) - 512 <= 0x400000 and len(data) <= 16740352
    padded = hashlib.sha256(data)
    padded.update(bytes(16740352 - len(data)))
    contract = json.loads((out / 'session-contract.UNAPPROVED.json').read_text())
    assert contract['mode'] == 'PARENT_REVIEW_REQUIRED' and contract['armed'] is True
    assert contract['userdata_enabled'] is False and contract['physical_validation'] is False
    assert contract['manifest_sha256'] == sha(binary)
    assert contract['p10_full_sha256'] == padded.hexdigest()
    result = dict(independent_parser_sha256=sha(parser.read_bytes()), passed=True,
                  image_sha256=sha(data), padded_p10_sha256=padded.hexdigest(),
                  manifest_sha256=sha(binary), rows=rows,
                  only_manifest_cpio_entry_changed=True, stock_kernel_unchanged=True,
                  policy_and_contexts_and_keys_unchanged=True, geometry=geometry,
                  reservation_headroom_bytes=0x400000 - (len(ram) - 512),
                  p10_headroom_bytes=16740352 - len(data),
                  deployment_approved=False, device_operations=0)
    target = ROOT / 'evidence/independent-container-check-r2.json'
    with target.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
