"""Check real installed root route without executing target code or contacting a device."""
from pathlib import Path
import struct
import subprocess
import xml.etree.ElementTree as ET
from integrate import need, sha
from verify_google_payload import digest


def elf64(path):
    with path.open('rb') as f:
        header = f.read(20)
    need(len(header) == 20 and header[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', header, 18)[0] == 183,
         'Missing genuine AArch64 root ELF: ' + str(path))


def verify(product, apex, root_init_hash, raw=None, debugfs=None):
    daemon = product / 'system/system_ext/bin/adb_root'
    init = product / 'system/system_ext/etc/init/adb_root.rc'
    elf64(daemon)
    need(sha(init) == root_init_hash, 'Installed adb_root init differs from reviewed source')
    entries = [e for e in ET.parse(apex / 'apex-info-list.xml').getroot()
               if e.attrib.get('moduleName') == 'com.android.adbd' and e.attrib.get('isActive') == 'true']
    need(len(entries) == 1, 'Real APEX metadata must select exactly one adbd module')
    module = entries[0].attrib['modulePath']
    need(module.startswith('/system/apex/') and '..' not in Path(module).parts, 'Unexpected adbd APEX location')
    source_apex = product / module.lstrip('/')
    need(source_apex.is_file(), 'Missing source adbd APEX')
    adbd = apex / 'com.android.adbd/bin/adbd'
    elf64(adbd)
    expected = {'ro.secure': '1', 'ro.debuggable': '1', 'ro.adb.secure': '1'}
    observed = {key: [] for key in expected}
    props = []
    for rel in ['system/build.prop', 'system/etc/prop.default', 'root/prop.default',
                'system/system_ext/build.prop', 'system/product/build.prop',
                'system/vendor/build.prop', 'system/vendor/default.prop']:
        path = product / rel
        if not path.is_file(): continue
        for line in path.read_text().splitlines():
            key, sep, value = line.partition('=')
            if sep and key.strip() in expected:
                observed[key.strip()].append({'file': rel, 'value': value.strip()})
        props.append(path)
    for key, wanted in expected.items():
        need(observed[key] and all(x['value'] == wanted for x in observed[key]), 'Generated secure userdebug property mismatch: ' + key)
    files = [daemon, init, source_apex, *props]
    receipt = {str(p.relative_to(product)): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in files}
    if raw:
        need(debugfs is not None, 'Missing final-image reader')
        for path in files:
            rel = str(path.relative_to(product))
            if rel.startswith('root/'):
                # Ramdisk properties are checked against actual BOOT by the caller.
                continue
            process = subprocess.Popen([str(debugfs), '-R', 'cat /' + rel, str(raw)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            actual = digest(process.stdout)
            error = process.stderr.read().decode(errors='replace')
            need(process.wait() == 0 and actual == {'sha256': sha(path), 'size': path.stat().st_size}, 'Root-route file differs in SYSTEM: ' + rel + ' ' + error)
            receipt[rel]['final_ext4_bytes_match'] = True
    return {'installed_files': receipt, 'generated_security_properties': observed,
            'adbd_apex_metadata': entries[0].attrib, 'extracted_adbd_sha256': sha(adbd),
            'root_runtime_verified': False, 'service_chain_verified': False, 'device_accessed': False}


def verify_ramdisk_properties(entries, product):
    expected = {'ro.secure': '1', 'ro.debuggable': '1', 'ro.adb.secure': '1'}
    result = {}
    for name in ['prop.default', 'default.prop', 'system/etc/prop.default']:
        if name not in entries: continue
        mode, uid, gid, content = entries[name]
        need(mode & 0o170000 == 0o100000, 'Ramdisk property file is not regular')
        for line in content.decode().splitlines():
            key, sep, value = line.partition('=')
            if sep and key.strip() in expected:
                need(value.strip() == expected[key.strip()], 'Insecure actual ramdisk property: ' + key)
        if name == 'prop.default' and (product / 'root/prop.default').is_file():
            need(content == (product / 'root/prop.default').read_bytes(), 'Ramdisk property source differs')
        result[name] = __import__('hashlib').sha256(content).hexdigest()
    return result
