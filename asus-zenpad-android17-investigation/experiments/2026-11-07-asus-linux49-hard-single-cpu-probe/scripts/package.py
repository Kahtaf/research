"""One equal-length boot argument correction; no helper or kernel-code changes."""
from pathlib import Path
import ast, difflib, json, shutil, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[1]
B = R.parent/'2026-11-07-asus-linux49-direct-clock-syscall-control'
for n in ['bootformat.py', 'fdt.py', 'adb', 'legacy_adb.py']:
    shutil.copy2(B/'source'/n, R/'source'/n)
sys.path.insert(0, str(R/'source'))
import bootformat as b, fdt
old = (B/'artifacts/candidate.img').read_bytes()
assert b.sha(old) == '28e87b5ad0f4d45ca232aae1f294b266b00f5d627bac17f16dbc0721465d0487'
pre = b.sha(old+bytes(b.PARTITION_SIZE-len(old)))
assert pre == '39241265432908288561ce54d8dde8ae28f55ce97468b3193251444f6a43c52c'
h, k, ram, tail = b.parse_image(old)
assert not tail
raw, dt = b.ungzip(k[512:])
stream = k[512:-len(dt)]
fh, nodes, tokens = fdt.parse(dt)
args = nodes['/chosen']['bootargs'].rstrip(b'\0')
assert args == h[64:576].rstrip(b'\0')
assert args.split().count(b'maxcpus=1') == 1 and b'nr_cpus=1' not in args.split()
newargs = args.replace(b'maxcpus=1', b'nr_cpus=1')
assert len(newargs) == len(args) < 92
newdt = bytearray(dt)
pos = fh[2]
changed = 0
for t, node, name, value, encoded in tokens:
    if (t, node, name) == (3, '/chosen', 'bootargs'):
        assert value == args+b'\0'
        newdt[pos+12:pos+12+len(value)] = newargs+b'\0'
        changed += 1
    pos += len(encoded)
assert changed == 1
newdt = bytes(newdt)
nh, nn, nt = fdt.parse(newdt)
expected = {p: dict(v) for p, v in nodes.items()}
expected['/chosen']['bootargs'] = newargs+b'\0'
assert nh == fh and nn == expected
for a, z in zip(tokens, nt):
    if a != z:
        assert a[:3] == z[:3] == (3, '/chosen', 'bootargs')
        assert a[4][:12] == z[4][:12] and len(a[4]) == len(z[4])
newk = k[:512]+stream+newdt
assert len(newk) == len(k)
header = bytearray(h)
header[64:576] = newargs+bytes(512-len(newargs))
image = b.make_image(bytes(header), newk, ram)
hh, kk, rr, tt = b.parse_image(image)
assert not tt and rr == ram and kk[:512] == k[:512]
rraw, rdt = b.ungzip(kk[512:])
assert rraw == raw and kk[512:-len(rdt)] == stream and rdt == newdt
assert len(image) == len(old)
assert all(x == y for i, (x, y) in enumerate(zip(h, hh)) if i not in set(range(64,576)) | set(range(576,608)))
full = image+bytes(b.PARTITION_SIZE-len(image))
for n, data in [('candidate.img', image), ('candidate.p10.raw', full), ('runtime.dtb', newdt)]:
    assert not (R/'artifacts'/n).exists()
    (R/'artifacts'/n).write_bytes(data)
prior = (B/'source/install.py').read_text()
s = prior
changes = {
    "IMAGE_SHA='28e87b5ad0f4d45ca232aae1f294b266b00f5d627bac17f16dbc0721465d0487'": f"IMAGE_SHA='{b.sha(image)}'",
    f"FULL_SHA='{pre}'": f"FULL_SHA='{b.sha(full)}'",
}
profile = next(l for l in s.splitlines() if "profile='" in l)
newprofile = profile[:profile.index("profile='")]+"profile='exact-linux49-hard-single-cpu-r1',"
changes[profile] = newprofile
preline = next(l for l in s.splitlines() if l.startswith('INSTALL_PREIMAGES='))
assert pre not in preline
changes[preline] = preline[:-1]+f",'{pre}')"
for a, z in changes.items():
    assert s.count(a) == 1
    s = s.replace(a, z)
def body(text, name):
    n = next(n for n in ast.parse(text).body if getattr(n, 'name', None) == name)
    return '\n'.join(text.splitlines()[n.lineno-1:n.end_lineno])
for n in ['execute', 'Transport', 'Guard']:
    assert body(prior, n) == body(s, n)
(R/'source/install.py').write_text(s)
(R/'source/install.diff').write_text(''.join(difflib.unified_diff(prior.splitlines(True),s.splitlines(True))))
result = dict(candidate_bytes=len(image), candidate_sha256=b.sha(image), full_p10_sha256=b.sha(full),
    preimage_sha256=pre, old_bootargs=args.decode(), new_bootargs=newargs.decode(),
    kernel_gzip_unchanged=True, kernel_raw_unchanged=True, entire_helper_ramdisk_unchanged=True,
    all_DT_except_chosen_bootargs_unchanged=True, DT_geometry_reservations_and_hardware_unchanged=True,
    initrd_bounds_unchanged=True, wrappers_and_load_addresses_unchanged=True,
    execute_Transport_Guard_unchanged=True, reused_helper_uuid='f0c3c82c-d639-4d8a-90f2-155fd4224ceb',
    freshness='Exact new installed container, nr_cpus token and actual IRQ CPU column count, fresh stock boot transition; reused UUID alone is insufficient.',
    motivation='Prior actual IRQ table exposed two online CPUs despite maxcpus=1; correct that newly measured configuration confounder before kernel tracing.',
    device_contacted=False)
(R/'evidence/packaging-receipt.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
