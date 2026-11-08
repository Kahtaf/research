"""Finalize only the unattempted own kit, refusing all unexpected prior bytes."""
from pathlib import Path
import base64,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('remote',R/'scripts/remote.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
files=['inputs/plan.json','scripts/continuation.py','scripts/verify_config_paths.py','scripts/build.sh','inputs/kit-pins.json']
payload={p:base64.b64encode((R/p).read_bytes()).decode() for p in files}
code='''
from pathlib import Path
import base64,hashlib,json,sys
K=Path('/srv/android/asus-reviewed-build-kit/r7');sys.path.insert(0,str(K/'scripts'))
import integrate as i
i.need(i.verify_pins(K)=='80afe24c28437e42efc4501116433f585fa029529875afe1800fd296b2d7090a','Unexpected pre-final own kit')
i.revision_unused(i.read(K/'inputs/plan.json'))
for rel,data in PAYLOAD.items():
 p=K/rel;tmp=p.with_name(p.name+'.finalizing');tmp.write_bytes(base64.b64decode(data));tmp.replace(p)
print(json.dumps(dict(final_seal=i.verify_pins(K),attempt_exists=(K/'attempt').exists())))
'''.replace('PAYLOAD',repr(payload))
print(m.run(code))
