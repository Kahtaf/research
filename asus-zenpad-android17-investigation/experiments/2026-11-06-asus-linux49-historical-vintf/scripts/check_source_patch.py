from pathlib import Path
import json,hashlib,subprocess,os
P=Path('/srv/android/asus-linux49-historical-vintf-20261106');S=Path('/srv/android/lineage24')
# Source is read-only; the concurrent root-property file and all out metadata are excluded.
sourcepins={'device/asus/p00a/device.mk': '788d0a4a0bebf492886651d8fb3ef3020654c063e704231c5baa282281c6fc14', 'device/asus/p00a/manifest.xml': '320a21a0778bed69082a08bc457d58969352471130bf57ab241cbd71653fe0a6', 'device/asus/p00a/BoardConfig.mk': 'e5296e182b457ec662694e044fffd322bdc246d556783743d080c23f5e4bde55'}
observed={f:{'before':sha,'after':hashlib.sha256((S/f).read_bytes()).hexdigest()} for f,sha in sourcepins.items()}
assert all(x['before']==x['after'] for x in observed.values())
argv=[str(P/'tools/bin/assemble_vintf'),'-i',str(P/'candidate-source/device/asus/p00a/manifest.xml'),'-o',str(P/'work-p/source-primary-manifest.xml')]
env={'PATH':'/usr/bin:/bin','BOARD_SEPOLICY_VERS':'202704'}
q=subprocess.run(argv,capture_output=True,text=True,timeout=30,env=env)
r={'sources':observed,'all_source_preimages_unchanged':True,'source_manifest_assemble_argv':argv,'source_manifest_assemble_env':env,'source_manifest_assemble_exit':q.returncode,'source_manifest_assemble_log':q.stdout+q.stderr,'output':(P/'work-p/source-primary-manifest.xml').read_text() if q.returncode==0 else None}
assert q.returncode==0
(P/'evidence/source-patch-check.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
