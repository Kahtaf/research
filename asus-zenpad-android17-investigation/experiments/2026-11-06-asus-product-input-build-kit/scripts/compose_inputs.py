"""Parent-owned isolated composition; never touches active AOSP or kernel inputs."""
from pathlib import Path
import base64
import hashlib
import json
from remote import run

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
OLD = WORK / '2026-11-06-asus-reviewed-build-kit'
MAPPING = WORK / '2026-11-06-asus-android17-input-mapping'
FILES = {
    'input/Goodix_Capacitive_TouchScreen.idc': 'ff9c53351559ea415c5bbb2aafd3472bbedd6f264646903d20189e41da2d8a55',
    'input/mtk-kpd.kl': 'a940764c7807d582cb04cadeb3140566d6472353cf27a31a52a2e7aefcb0a942',
    'input/input-mapping.mk': '6ec0030412932f6dcef9795aa9d708425661ff2368282b6b4536e03f743c1a75',
}
SUFFIX = '\n$(call inherit-product, device/asus/p00a/input/input-mapping.mk)\n'

def sha(data):
    return hashlib.sha256(data).hexdigest()

if (ROOT / 'evidence/composition.json').exists():
    raise RuntimeError('Composition already recorded; never overwrite or silently resume')
assert sha((OLD / 'inputs/kit-pins.json').read_bytes()) == '9b9eea2ae274a873d99459ea4faa352dba1dd6a9ba8b5986fae0304047ee941b'
for rel, digest in json.loads((OLD / 'inputs/kit-pins.json').read_text()).items():
    assert sha((OLD / rel).read_bytes()) == digest, rel
payload = {}
for rel, digest in FILES.items():
    data = (MAPPING / 'staged/device/asus/p00a' / rel).read_bytes()
    assert sha(data) == digest, rel
    payload[rel] = base64.b64encode(data).decode()
old_receipt = (OLD / 'inputs/STAGED.json').read_bytes()
args = {'files': payload, 'hashes': FILES, 'suffix': SUFFIX,
        'old_staged_sha256': sha(old_receipt)}
script = r'''
from pathlib import Path
import base64,hashlib,json,shutil,datetime,os
args = json.loads(ARGUMENTS)
old=Path('/srv/android/asus-product-integration-staging/r1')
new=Path('/srv/android/asus-product-integration-staging/r2')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def item(p):
 if p.is_symlink(): return {'symlink':os.readlink(p)}
 return {'sha256':sha(p)}
def manifest(p):
 return {str(f.relative_to(p)):item(f) for f in sorted(p.rglob('*')) if f.is_file() or f.is_symlink()}
old_bytes=(old/'STAGED.json').read_bytes()
assert hashlib.sha256(old_bytes).hexdigest()==args['old_staged_sha256']
s=json.loads(old_bytes)
assert manifest(old/'product-device')==s['product_after']
assert manifest(old/'platform-connectivity')==s['connectivity']
assert manifest(Path('/srv/android/lineage24/device/asus/p00a'))==s['product_before']
assert manifest(old/'full-boot-tools')=={k:{'sha256':v} for k,v in s['packaging'].items()}
assert sha(old/'kernel-config/asus_p00a_combined_defconfig')==s['kernel_config_sha256']
assert not new.exists()
base=(old/'product-device/device.mk').read_bytes()
assert b'input/input-mapping.mk' not in base
shutil.copytree(old,new,symlinks=True)
for rel,data in args['files'].items():
 p=new/'product-device'/rel
 assert not p.exists() and not p.is_symlink()
 p.parent.mkdir(parents=True,exist_ok=True)
 decoded=base64.b64decode(data)
 assert hashlib.sha256(decoded).hexdigest()==args['hashes'][rel]
 p.write_bytes(decoded)
(new/'product-device/device.mk').write_bytes(base+args['suffix'].encode())
after=manifest(new/'product-device')
changed={p for p in s['product_after'].keys()|after.keys() if s['product_after'].get(p)!=after.get(p)}
assert changed==set(args['files'])|{'device.mk'}
assert manifest(old/'product-device')==s['product_after']
assert manifest(Path('/srv/android/lineage24/device/asus/p00a'))==s['product_before']
assert manifest(new/'platform-connectivity')==s['connectivity']
delta={'files':args['hashes'],'device_mk_before_sha256':hashlib.sha256(base).hexdigest(),
 'device_mk_after_sha256':after['device.mk']['sha256'],'suffix':args['suffix'],
 'base_staged_sha256':args['old_staged_sha256']}
s.update(path=str(new),kernel_config_path=str(new/'kernel-config/asus_p00a_combined_defconfig'),
 product_after=after,parent_input_delta=delta,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 firstboot_parity_accepted=False,scoped_parity_requires_supplement=True)
(new/'STAGED.json').write_text(json.dumps(s,indent=2)+'\n')
print(json.dumps({'staged':s,'base_device_mk_b64':base64.b64encode(base).decode(),
 'staged_sha256':sha(new/'STAGED.json'),'input_delta':delta,
 'old_product_unchanged':True,'active_device_unchanged':True,'build_started':False,
 'device_operations':False,'candidate_path':str(new)}))
'''.replace('ARGUMENTS', repr(json.dumps(args)))
result = json.loads(run(script))
(ROOT / 'inputs/STAGED.json').write_text(json.dumps(result['staged'], indent=2) + '\n')
assert sha((ROOT / 'inputs/STAGED.json').read_bytes()) == result['staged_sha256']
(ROOT / 'inputs/base-radio-device.mk').write_bytes(base64.b64decode(result.pop('base_device_mk_b64')))
delta = result['input_delta']
delta['public_input_handoff_sha256'] = sha((MAPPING / 'evidence/input-mapping.json').read_bytes())
(ROOT / 'inputs/input-mapping.json').write_text(json.dumps(delta, indent=2) + '\n')
plan = json.loads((ROOT / 'inputs/plan.json').read_text())
plan['input_mapping_receipt'] = plan['run_root'] + '/inputs/input-mapping.json'
plan['input_mapping_base'] = plan['run_root'] + '/inputs/base-radio-device.mk'
plan['external_pins'][plan['staging'] + '/STAGED.json'] = result['staged_sha256']
for rel, digest in FILES.items():
    plan['external_pins'][plan['staging'] + '/product-device/' + rel] = digest
plan['external_pins'][plan['staging'] + '/product-device/device.mk'] = delta['device_mk_after_sha256']
plan['production_build_jobs'] = 8
(ROOT / 'inputs/plan.json').write_text(json.dumps(plan, indent=2, sort_keys=True) + '\n')
(ROOT / 'evidence/composition.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'staged'}, indent=2))
