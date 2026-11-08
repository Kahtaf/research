from pathlib import Path
import datetime
import difflib
import hashlib
import json
import os
import re
import resource
import time

PAYLOAD = None
os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
started = time.monotonic()
OWN = Path('/srv/android/asus-memory-firstboot-kernel-qualification-20261106')
OWN.mkdir(exist_ok=False)
V = Path('/srv/android/asus-sdk37-lmkd-functional/kernel-memory-r1/source')
B = Path('/srv/android/asus-bmc156-full-kernel-r1/kernel')
VO = V.parent/'out'
BO = B.parent/'out'

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for buf in iter(lambda: f.read(1024*1024), b''):
            h.update(buf)
    return h.hexdigest()

def cfg(p):
    result = {}
    for line in p.read_text().splitlines():
        m = re.match(r'(CONFIG_\w+)=(.*)', line)
        n = re.match(r'# (CONFIG_\w+) is not set$', line)
        if m: result[m[1]] = m[2]
        elif n: result[n[1]] = 'n'
    return result

def artifact(p, expected):
    s = p.stat()
    actual = sha(p)
    return {'path': str(p), 'resolved_path': str(p.resolve(strict=True)), 'bytes': s.st_size, 'sha256': actual, 'expected_sha256': expected, 'matches': actual == expected}

out = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'roots': {'virtual': str(V), 'physical': str(B)}, 'limits': {'affinity': sorted(os.sched_getaffinity(0)), 'address_space_bytes': resource.getrlimit(resource.RLIMIT_AS)[0], 'cpu_seconds': resource.getrlimit(resource.RLIMIT_CPU)[0]}, 'artifacts': {}, 'sources': {}, 'selected_config': {}, 'selected_config_differences': {}}
pins = PAYLOAD['memory_export']['files']
for label,p,key in [('memory_image', VO/'arch/arm64/boot/Image','kernel-memory-r1/out/arch/arm64/boot/Image'), ('memory_config', VO/'.config','kernel-memory-r1/out/.config')]:
    out['artifacts'][label] = artifact(p,pins[key]['sha256'])
for label,p,key in [('physical_image',BO/'arch/arm64/boot/Image.gz-dtb','arch/arm64/boot/Image.gz-dtb'),('physical_config',BO/'.config','.config')]:
    out['artifacts'][label] = artifact(p,PAYLOAD['physical_full']['artifacts'][key]['sha256'])
vc,bc = cfg(VO/'.config'),cfg(BO/'.config')
out['configs'] = {'virtual': vc, 'physical': bc}
out['whole_config_differences'] = [{'option':k, 'virtual':vc.get(k,'absent'), 'physical':bc.get(k,'absent')} for k in sorted(vc.keys() | bc.keys()) if vc.get(k,'absent') != bc.get(k,'absent')]
for group, rows, pathkey, vkey, bkey in [('firstboot',PAYLOAD['firstboot']['sources'],'path','r7_source_sha256','combined_source_sha256'),('memory',PAYLOAD['memory_sources'],'path','owned_virtual','physical')]:
    checked = []
    for row in rows:
        rel = row[pathkey]
        assert not Path(rel).is_absolute() and '..' not in Path(rel).parts
        vp,bp = V/rel,B/rel
        vh,bh = sha(vp),sha(bp)
        item = {'path':rel, 'virtual':vh, 'physical':bh, 'frozen_virtual':row[vkey], 'frozen_physical':row[bkey], 'equal_physical':vh==bh, 'matches_frozen_virtual':vh==row[vkey], 'matches_frozen_physical':bh==row[bkey]}
        if vh!=bh:
            item['diff'] = ''.join(difflib.unified_diff(bp.read_text().splitlines(True),vp.read_text().splitlines(True),fromfile='physical/'+rel,tofile='virtual/'+rel))
        checked.append(item)
    out['sources'][group] = checked
for group, rows, key, vkey, bkey in [('firstboot',PAYLOAD['firstboot']['selected_config'],'option','r7','combined'), ('memory',PAYLOAD['memory_config']['selected'],'name','virtual','physical')]:
    checked = [{'option':r[key], 'virtual':vc.get(r[key],'absent'), 'physical':bc.get(r[key],'absent'), 'frozen_virtual':r[vkey], 'frozen_physical':r[bkey]} for r in rows]
    out['selected_config'][group] = checked
    out['selected_config_differences'][group] = [r for r in checked if r['virtual'] != r['physical']]
# Explicit test-board source adaptation, kept outside the selected subsystem claim.
gic = 'drivers/irqchip/irq-gic-v3.c'
out['virtual_board_source'] = {'path':gic, 'virtual':sha(V/gic), 'physical':sha(B/gic), 'diff': ''.join(difflib.unified_diff((B/gic).read_text().splitlines(True),(V/gic).read_text().splitlines(True),fromfile='physical/'+gic,tofile='virtual/'+gic))}
out['source_root_resolution'] = {str(p):str(p.resolve(strict=True)) for p in [V,B]}
out['elapsed_seconds'] = time.monotonic()-started
out['remote_receipt'] = str(OWN/'inspection.json')
raw = json.dumps(out,indent=2)+'\n'
(OWN/'inspection.json').write_text(raw)
print(raw)
