from pathlib import Path
import hashlib
import os
import struct
import sys
sys.path.insert(0, 'source')
import bundle

root = Path('artifacts')
(root / 'chunks').mkdir()
base = root / 'fixture-sys'
for relative in ('sys/class/block', 'sys/dev/block', 'proc/self'):
    (base / relative).mkdir(parents=True)
for i in (0, 1):
    card = base / ('sys/devices/mmc%d/card%d' % (i, i))
    disk = card / ('block/mmcblk%d' % i)
    disk.mkdir(parents=True)
    (disk / 'device').symlink_to(os.path.relpath(card, disk))
    (card / 'type').write_text('SD\n' if i else 'MMC\n')
    (disk / 'removable').write_text(str(i) + '\n')
    (disk / 'dev').write_text('179:%d\n' % (i*32))
    (disk / 'size').write_text('20000\n')
    for link in (base / ('sys/class/block/mmcblk%d' % i), base / ('sys/dev/block/179:%d' % (i*32))):
        link.symlink_to(os.path.relpath(disk, link.parent))
    if i:
        part = disk / 'mmcblk1p1'
        part.mkdir()
        for name, value in dict(dev='179:33', partition='1', start='2048', size='10000').items():
            (part / name).write_text(value + '\n')
        for link in (base / 'sys/class/block/mmcblk1p1', base / 'sys/dev/block/179:33'):
            link.symlink_to(os.path.relpath(part, link.parent))
(base / 'proc/self/mountinfo').write_text('7 1 179:33 / /mnt/rescue-sd rw,nosuid,nodev,noexec - vfat /dev/block/mmcblk1p1 rw\n')

geometry = {9: 17, 25: bundle.CHUNK + 7, 26: bundle.CHUNK + 355840}
b = b'ASUSR002' + struct.pack('<II', 2, 5) + bytes(96)
images = []
for i in range(5):
    part = 26 if i == 4 else 9 if i % 2 else 25
    image = (b'X' if i == 2 else b'\0') * geometry[part]
    images.append(image)
    chunks = [hashlib.sha256(image[j:j+bundle.CHUNK]).digest() for j in range(0, len(image), bundle.CHUNK)]
    b += struct.pack('<IIQ32sI', i, part, len(image), hashlib.sha256(image).digest(), len(chunks)) + b''.join(chunks)
rows = bundle.parse(b, geometry)
assert bundle.selection(rows, None) == [2, 4, 3]
work = root / 'bundle-case'
(work / 'raw').mkdir(parents=True)
for i in (2, 4, 3):
    (work / ('raw/role-%d.raw' % i)).write_bytes(images[i])
wfd = bundle.directory(work)
try:
    bundle.produce(wfd, b, rows, [2, 4, 3])
finally:
    os.close(wfd)
output = work / 'card/asus-rescue'
assert not list((output / 'role-4').iterdir())
assert (output / 'role-2/000001.raw').stat().st_size == 7
assert not (output / 'execute.trigger').exists()
assert (output / 'manifest.sha256').read_text() == hashlib.sha256(b).hexdigest() + '\n'
assert bundle.capacity(rows, [2, 4, 3])['source_payload_bytes'] == len(images[2])
print('PASS streaming bundle verifies full/chunk hashes, omits only zeros, publishes binding last; no trigger/admission created')
