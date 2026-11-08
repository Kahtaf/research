"""Controlled logging-only boot parameter change. No device operations."""
from pathlib import Path
import ast, difflib, hashlib, json, shutil, struct, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[1]
B = R.parent / '2026-11-07-asus-linux49-ram-before-alarm-probe'
for name in ['bootformat.py', 'fdt.py', 'adb', 'legacy_adb.py']:
    shutil.copy2(B / 'source' / name, R / 'source' / name)
sys.path.insert(0, str(R / 'source'))
import bootformat as b, fdt
old = (B / 'artifacts/candidate.img').read_bytes()
assert b.sha(old) == '37b91769f1236a8e332f84b61cb451293e22c24040bd26d81316427694315ebc'
preimage = b.sha(old + bytes(b.PARTITION_SIZE - len(old)))
assert preimage == '14a651dc2c1862f2d8a68153134d95864db495d0382f687a617ff27513e9c1c6'
header, kernel, ram, tail = b.parse_image(old)
assert not tail
raw, dt = b.ungzip(kernel[512:])
stream = kernel[512:-len(dt)]
h, nodes, tokens = fdt.parse(dt)
oldargs = nodes['/chosen']['bootargs'].rstrip(b'\0')
assert not any(x.startswith(b'printk.devkmsg=') for x in oldargs.split())
args = oldargs + b' printk.devkmsg=on'
assert len(args) < 512
strings = dt[h[3]:h[3]+h[8]]
newstream = bytearray()
changed = 0
for t, node, name, value, encoded in tokens:
    if (t, node, name) == (3, '/chosen', 'bootargs'):
        v = args + b'\0'
        newstream += encoded[:4] + struct.pack('>I', len(v)) + encoded[8:12] + v + bytes((-len(v)) % 4)
        changed += 1
    else:
        newstream += encoded
assert changed == 1
nh = list(h)
nh[1] = h[2] + len(newstream) + len(strings)
nh[3] = h[2] + len(newstream)
nh[9] = len(newstream)
newdt = struct.pack('>10I', *nh) + dt[40:h[2]] + newstream + strings
_, nn, nt = fdt.parse(newdt)
expected = {p: dict(v) for p, v in nodes.items()}
expected['/chosen']['bootargs'] = args + b'\0'
assert nn == expected and newdt[40:h[2]] == dt[40:h[2]]
assert len(tokens) == len(nt)
for before, after in zip(tokens, nt):
    if before != after:
        assert before[:3] == after[:3] == (3, '/chosen', 'bootargs')
newkernel = b.wrap(kernel, stream + newdt)
newheader = bytearray(header)
newheader[64:576] = args + bytes(512-len(args))
image = b.make_image(bytes(newheader), newkernel, ram)
ah, ak, ar, at = b.parse_image(image)
rr, rd = b.ungzip(ak[512:])
assert rr == raw and ak[512:-len(rd)] == stream and ar == ram and not at
assert [i for i, (x, y) in enumerate(zip(kernel[:512], ak[:512])) if x != y] == [i for i in range(4, 8) if kernel[i] != ak[i]]
assert all(x == y for i, (x, y) in enumerate(zip(header, ah)) if i not in set(range(8,12)) | set(range(64,576)) | set(range(576,608)))
full = image + bytes(b.PARTITION_SIZE-len(image))
for n, data in [('candidate.img', image), ('candidate.p10.raw', full), ('runtime.dtb', newdt)]:
    assert not (R/'artifacts'/n).exists()
    (R/'artifacts'/n).write_bytes(data)
prior = (B/'source/install.py').read_text()
inst = prior
changes = {
    "IMAGE_SHA='37b91769f1236a8e332f84b61cb451293e22c24040bd26d81316427694315ebc'": f"IMAGE_SHA='{b.sha(image)}'",
    f"FULL_SHA='{preimage}'": f"FULL_SHA='{b.sha(full)}'",
    'len(image)==7972864': f'len(image)=={len(image)}',
    "profile='exact-linux49-ram-before-alarm-5fa3e2cd-r1'": "profile='exact-linux49-devkmsg-on-same-helper-r1'",
}
for a, z in changes.items():
    assert inst.count(a) == 1
    inst = inst.replace(a, z)
line = next(l for l in inst.splitlines() if l.startswith('INSTALL_PREIMAGES='))
assert preimage not in line
inst = inst.replace(line, line[:-1] + f",'{preimage}')")
def body(s, name):
    n = next(n for n in ast.parse(s).body if getattr(n, 'name', None) == name)
    return '\n'.join(s.splitlines()[n.lineno-1:n.end_lineno])
for name in ['execute', 'Transport', 'Guard']:
    assert body(prior, name) == body(inst, name)
(R/'source/install.py').write_text(inst)
(R/'source/install.diff').write_text(''.join(difflib.unified_diff(prior.splitlines(True), inst.splitlines(True))))
receipt = dict(candidate_sha256=b.sha(image), full_p10_sha256=b.sha(full), candidate_bytes=len(image), full_p10_bytes=len(full), preimage_sha256=preimage, changed_boot_parameter='printk.devkmsg=on', old_bootargs=oldargs.decode(), new_bootargs=args.decode(), kernel_raw_sha256=b.sha(raw), kernel_gzip_sha256=b.sha(stream), unchanged_compressed_kernel=True, unchanged_raw_kernel=True, unchanged_entire_ramdisk=True, unchanged_all_DT_properties_except_chosen_bootargs=True, unchanged_initrd_bounds=True, unchanged_hardware_and_reservations=True, unchanged_execution_and_guard_bodies=True, helper_uuid_reused_deliberately='5fa3e2cd-430d-4bbb-8b37-1adff9bb9439', freshness='Same helper is a controlled experiment. UUID alone is not fresh proof. Require exact installed new container hash, single entry from a verified stock boot, verified different subsequent stock boot and complete new log; compare post-tenth helper records.', device_contacted=False)
(R/'evidence/packaging-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
