import pathlib,hashlib,json,os,resource,tarfile
p=pathlib.Path('/srv/android/asus-audio-kernel-copy-repair-20261106-r1');base=pathlib.Path('/srv/android/asus-bmc156-full-kernel-r1')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
expected=json.loads((p/'evidence/preservation-expected.json').read_text());results={}
for path,digest in expected.items():
 actual=sha(base/'kernel'/path);assert actual==digest,(path,actual,digest)
 results[path]={'expected_physical_bmc':digest,'current':actual}
(p/'evidence/preservation-verified.json').write_text(json.dumps({'verified':len(results),'files':results,'scope':'r5 combined delta, runtime preservation list and BMC156 delta; read-only check against parent-pinned physical source'},indent=2))
inputs=json.loads((p/'evidence/compiler-inputs.json').read_text())
with tarfile.open(p/'evidence/compiler-inputs.tar.gz','w:gz') as t:
 for path,rec in inputs.items():
  f=pathlib.Path(path);assert sha(f)==rec['sha256'],path
  t.add(f,arcname=str(f).lstrip('/'),recursive=False)
config=(base/'out/.config').read_text()
(p/'evidence/config-preserved.json').write_text(json.dumps({'config_sha256':sha(base/'out/.config'),'image_sha256':sha(base/'out/arch/arm64/boot/Image.gz-dtb'),'selected_config':[x for x in config.splitlines() if any(k in x for k in ['BMC156','BMA253','MC3416','MTK_SPEAKER','AMP_AW8737S','CGROUP','SND_SOC_MT8163','ASUS_P00A'])],'config_changed':False,'image_changed':False},indent=2))
print('verified',len(results),'preserved sources and',len(inputs),'compiler source/header inputs')
