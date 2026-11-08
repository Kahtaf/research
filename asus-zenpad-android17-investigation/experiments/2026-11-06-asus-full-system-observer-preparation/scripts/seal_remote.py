import os,resource,signal,pathlib,json,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(90)
R=pathlib.Path('/srv/android/asus-full-system-observer-preparation-20261106');I=R/'immutable';pins=json.loads((R/'immutable-pins.json').read_text())
for row in pins:
 p=I/row['relative'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];p.chmod(p.stat().st_mode&0o777&~0o222)
assert all((I/r['relative']).stat().st_mode&0o222==0 for r in pins)
result=dict(owned_immutable_inputs_sealed=True,files=len(pins),all_content_pins_match=True,no_write_bits=True,
            original_fixture_inputs_chmodded=False,actual_product_touched=False)
(R/'immutable-seal.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
