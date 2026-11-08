"""Read-only local integrity and in-memory NONDEPLOYED package-size experiment.

No manifest/image is written, no approval fields are changed, and no builder,
arming, device or full-size payload reader is invoked. Hypothetical install
rows reuse the ACTUAL STOCK source chunk hashes and are NOT Android17 inputs.
"""
import collections
import gzip
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

R = Path(__file__).resolve().parents[1]
W = R.parent
S = W / '2026-11-06-asus-android17-target-rescue'
sys.path.insert(0, str(S / 'source'))
from bootformat import parse_image, parse_cpio, ungzip, make_cpio, elf_static
from file_contexts import extract

def sha(b):
    return hashlib.sha256(b).hexdigest()

def pin(p):
    b = p.read_bytes()
    return {'path': str(p.relative_to(W)), 'bytes': len(b), 'sha256': sha(b)}

def main():
    inventory = json.loads((S / 'ARTIFACTS.json').read_text())
    verified = []
    for name, wanted in inventory.items():
        got = pin(S / name)
        assert (got['bytes'], got['sha256']) == (wanted['bytes'], wanted['sha256'])
        verified.append(got)
    pins = json.loads((S / 'SOURCE_PINS.json').read_text())
    for name, wanted in pins['source_files'].items():
        assert pin(S / name)['sha256'] == wanted
    c = S / 'artifacts/candidate-delivery'
    header, kernel, ramdisk, _ = parse_image((c / 'UNTESTED-target-rescue.img').read_bytes())
    entries = parse_cpio(ungzip(ramdisk[512:])[0])
    stock = parse_image((S / 'inputs/initial/recovery.bin').read_bytes())
    assert kernel == stock[1]
    assert sha(kernel) == pins['stock_kernel']['wrapped_sha256']
    manifest = entries['rescue.manifest'][3]
    assert len(manifest) == 112 and struct.unpack_from('<I', manifest, 12)[0] == 0
    planpath = S / 'artifacts/stock-inverse.PLAN_ONLY.json'
    datapath = W / '2026-11-06-asus-android17-internal-data-validation/evidence/fresh_userdata.reference-1MiB.json'
    plan = json.loads(planpath.read_text())
    data = json.loads(datapath.read_text())
    stocksys, stockboot = [plan['images'][k] for k in ('original_system','original_boot')]
    assert (stocksys['bytes'], len(stocksys['chunks'])) == (3753902080, 3580)
    assert (stockboot['bytes'], len(stockboot['chunks'])) == (16740352, 16)
    assert (data['bytes'], len(data['chunks'])) == (11331268096, 10807)
    # No multi-GB image is read: source digests are the captured inventories.
    configs = []
    for count, rows in [(0, []), (2, [stocksys, stockboot]),
                        (4, [stocksys, stockboot, stocksys, stockboot]),
                        (5, [stocksys, stockboot, stocksys, stockboot, data])]:
        b = manifest[:12] + struct.pack('<I', count) + manifest[16:]
        for i, row in enumerate(rows):
            b += struct.pack('<IIQ', i, 26 if i == 4 else 9 if i % 2 else 25, row['bytes'])
            b += bytes.fromhex(row['sha256']) + struct.pack('<I', len(row['chunks']))
            b += b''.join(bytes.fromhex(x) for x in row['chunks'])
        e = dict(entries)
        e['rescue.manifest'] = (*entries['rescue.manifest'][:3], b)
        gz = bytearray(gzip.compress(make_cpio(e), compresslevel=9, mtime=0))
        gz[9] = 255
        if count == 0:
            assert bytes(gz) == ramdisk[512:], 'baseline must reproduce exact delivered gzip'
        configs.append({'records': count, 'manifest_bytes': len(b),
                        'compressed_ramdisk_bytes': len(gz), 'wrapped_ramdisk_bytes': len(gz)+512,
                        'headroom_vs_2MiB_payload': 2097152-len(gz),
                        'headroom_vs_2MiB_wrapped': 2097152-len(gz)-512,
                        'gzip_sha256_memory_only': sha(gz),
                        'scope': 'exact current package' if count == 0 else
                          'NONDEPLOYED memory-only size fixture; unchanged default policy; '
                          'install rows reuse actual STOCK hashes, NOT new OS; 5-row policy delta excluded'})
    # Extract real appended FDT chosen properties without writing any kernel/FDT.
    _, tail = ungzip(kernel[512:])
    assert tail[:4] == bytes.fromhex('d00dfeed')
    magic, total, soff, stroff, reserve, version, last, cpu, strsize, ssize = struct.unpack_from('>10I',tail)
    fdt = tail[:total]
    pos = soff; stack = []; chosen = []
    while pos < soff + ssize:
        tag = struct.unpack_from('>I', fdt, pos)[0]; pos += 4
        if tag == 1:
            end = fdt.index(0,pos); stack.append(fdt[pos:end].decode()); pos = (end+4)&~3
        elif tag == 2: stack.pop()
        elif tag == 3:
            size, noff = struct.unpack_from('>II', fdt, pos); pos += 8
            nameend = fdt.index(0, stroff+noff); name = fdt[stroff+noff:nameend].decode()
            value = fdt[pos:pos+size]
            if '/'.join(stack) == '/chosen':
                chosen.append({'name': name, 'offset_in_fdt': pos,
                               'value_hex': value.hex(),
                               'ascii': value.rstrip(b'\0').decode('ascii', errors='replace')})
            pos = (pos+size+3)&~3
        elif tag == 4: pass
        elif tag == 9: break
        else: raise ValueError(tag)
    result = {'passed': True, 'artifact_entries_verified': verified,
              'source_entries_verified': len(pins['source_files']),
              'stock_kernel_wrapped_sha256': sha(kernel),
              'header_cmdline': header[64:576].split(b'\0')[0].decode(),
              'appended_fdt': {'bytes':total, 'sha256':sha(fdt), 'chosen':chosen},
              'runtime': {'python':sys.version, 'zlib':zlib.ZLIB_RUNTIME_VERSION},
              'memory_only_package_measurements':configs,
              'chunk_inventory_pins':[pin(planpath),pin(datapath)],
              'chunk_entropy_note': {name:{'chunks':len(row['chunks']), 'unique':len(set(row['chunks']))}
                                   for name,row in [('actual_stock_system',stocksys),('actual_stock_boot',stockboot),('pristine_data',data)]},
              'elfs':{name:elf_static(entries[name][3]) for name in ('init','sbin/adbd','sbin/os-rescue','sbin/rescue-proxy')},
              'contexts_rows':len(extract(entries['file_contexts.bin'][3])),
              'no_full_system_or_data_read':True,'no_manifest_or_image_output':True}
    (R / 'evidence/delivery-inspection.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'artifacts':len(verified), 'sources':len(pins['source_files']),
                      'sizes':configs,'fdt':{'bytes':total,'chosen':chosen}}, indent=2))

if __name__ == '__main__':
    main()
