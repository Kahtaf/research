"""Inspect exact duplicate CPIO records and Make bool definition without writes."""
from pathlib import Path
import hashlib
import json
import os
import resource
import signal
import sys

resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
signal.alarm(1190)
r = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
sys.path.insert(0, str(r / 'scripts'))
from integrate import read, sha, need
plan = read(r / 'inputs/plan.json')
a = Path(plan['aosp'])
tools = Path(plan['staging']) / 'full-boot-tools/scripts'
sys.path.insert(0, str(tools))
import package_full_boot as packager
boot = Path(plan['product_out']) / 'boot.img'
need(sha(boot) == '4b83266cc1f7f14a95d6e8ad5da490e1d358a4a1cebbdb2354454790a0d05b51', 'BOOT drift')
ram = packager.components(boot.read_bytes())[2]
raw, tail = packager.ungzip(ram)
need(not tail, 'Unexpected gzip tail')
offset = 0
seen = {}
duplicates = []
count = 0
while True:
    start = offset
    need(raw[offset:offset + 6] == b'070701', 'Wrong newc magic')
    fields = [int(raw[offset + 6 + i * 8:offset + 14 + i * 8], 16) for i in range(13)]
    offset += 110
    size, namesize = fields[6], fields[11]
    name_bytes = raw[offset:offset + namesize]
    need(len(name_bytes) == namesize and name_bytes.endswith(b'\0'), 'Invalid CPIO name')
    name = name_bytes[:-1].decode()
    offset = (offset + namesize + 3) & ~3
    content = raw[offset:offset + size]
    need(len(content) == size, 'Truncated CPIO content')
    offset = (offset + size + 3) & ~3
    if name == 'TRAILER!!!':
        break
    record = {'offset': start, 'header_fields': fields, 'mode_octal': oct(fields[1]),
              'uid': fields[2], 'gid': fields[3], 'bytes': size,
              'content_sha256': hashlib.sha256(content).hexdigest()}
    if name in seen:
        duplicates.append({'name': name, 'first': seen[name], 'duplicate': record})
    else:
        seen[name] = record
    count += 1
need(not any(raw[offset:]), 'Nonzero archive tail')
macro = a / 'build/make/common/json.mk'
parser = tools.parent / 'probe/bootformat.py'
product = a / 'device/asus/p00a/lineage_p00a.mk'
print(json.dumps({'source_boot_sha256': sha(boot), 'compressed_ramdisk_sha256': hashlib.sha256(ram).hexdigest(),
                  'decompressed_cpio_bytes': len(raw), 'record_count': count, 'unique_names': len(seen),
                  'duplicates': duplicates, 'parser': {'path': str(parser), 'sha256': sha(parser), 'content': parser.read_text()},
                  'json_macro': {'path': str(macro), 'sha256': sha(macro), 'content': macro.read_text()},
                  'device_product': {'path': str(product), 'sha256': sha(product), 'content': product.read_text()}}, indent=2))
