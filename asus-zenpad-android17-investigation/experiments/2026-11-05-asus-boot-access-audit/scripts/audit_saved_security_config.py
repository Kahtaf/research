#!/usr/bin/env python3
"""Read saved security data only; never emit an unlock image or access USB."""
from pathlib import Path
import hashlib
import json
import struct
from Crypto.Cipher import AES

root = Path(__file__).resolve().parents[1]
lk = (root / 'sources/firmware/lk.bin').read_bytes()
assert hashlib.sha256(lk).hexdigest() == 'c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765'
data = (root / 'artifacts/device-backup/initial/seccfg.bin').read_bytes()
assert data == (root / 'artifacts/device-backup/verify/seccfg.bin').read_bytes()
assert data[:16] == b'AND_SECCFG_v\0\0\0\0'
assert struct.unpack_from('<I', data, 0x10)[0] == 0x4d4d4d4d
assert struct.unpack_from('<I', data, 0x185c)[0] == 0x45454545

# Exact LK disassembly: 41e3a11c returns 0x1830; 41e3a13c adds 0x2c
# before decrypt. Header version/size are not used for that length.
ciphertext = data[0x2c:0x185c]
plain = AES.new(b'25A1763A21BC854CD569DC23B4782B63', AES.MODE_CBC,
                bytes.fromhex('57325A5A125497661254976657325A5A')).decrypt(ciphertext)
status = struct.unpack_from('<I', plain, 0x850 - 0x2c)[0]
attr = struct.unpack_from('<I', plain, 0x854 - 0x2c)[0]
source = root.parent / '2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/drivers/misc/mediatek/masp'
makefile = (source / 'Makefile').read_text()
driver = (source / 'asfv2/core/sec_mod_core.c').read_text()
assert 'asf_link := asfv2' in makefile
assert 'case SEC_SECCFG_DECRYPT:' not in driver
report = {
    'scope': 'offline read-only analysis of two matching device backups and public source',
    'seccfg_sha256': hashlib.sha256(data).hexdigest(),
    'header': {key: hex(struct.unpack_from('<I', data, offset)[0]) for key, offset in
               [('version', 0x14), ('declared_size', 0x18), ('encrypted_offset', 0x1c), ('encrypted_length', 0x20)]},
    'matching_lk_read_path': {'record_bytes': 0x1860, 'crypt_start': 0x2c,
                              'crypt_bytes': 0x1830, 'endflag': '0x45454545',
                              'decrypted_lock_attribute_offset': '0x854',
                              'unlock_attribute': '0x44444444'},
    'pinned_mtkclient_software_cipher': {'status_matches': status in [0x43434343, 0x49494949],
        'attribute_matches': attr in [0x33333333, 0x44444444, 0x6000, 0x6001, 0x6002, 0x6003],
        'validated': False},
    'public_kernel_source': {'selected_driver': 'asfv2', 'seccfg_decrypt_case_present': False,
        'source_version_limit': 'Published ASUS 3.18.22 source; running release is 3.18.35. This is source evidence, not binary equivalence proof.',
        'files': {str(source / name): hashlib.sha256((source / name).read_bytes()).hexdigest()
                  for name in ['Makefile', 'asfv2/core/sec_mod_core.c']}},
    'decision': 'Do not run generic seccfg unlock or probe the unsupported decrypt ioctl. Hardware decryption, image authorization and restore access remain unresolved.',
    'device_commands_sent': [], 'unlock_image_generated': False,
}
output = root / 'evidence/saved-security-config-audit.json'
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: report[key] for key in ['header', 'matching_lk_read_path', 'pinned_mtkclient_software_cipher', 'decision']}, indent=2))
