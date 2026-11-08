#!/usr/bin/env python3
"""Replay the charging patch offline while preserving proven Linux compile fixes."""
from pathlib import Path
import difflib,hashlib,json,re,shutil,subprocess
R=Path(__file__).resolve().parents[1];S=R.parent/'2026-11-06-asus-android17-charging-integration'
m=json.loads((S/'evidence/patch-manifest.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
original=S/'patches'/m['patch'];assert sha(original)==m['sha256']=='aa827a36912d94012ebf85b10dd07af576ac29adbd3c68976a3bf7aa43c9a187'
W=R/'charging-rebase-work';W.mkdir()
for name in ['before','after']:shutil.copytree(S/'source/kernel-after-soc',W/name)
for path,values in m['files'].items():assert sha(W/'before'/path)==values['before'],path
subprocess.run(['git','apply','--check','--whitespace=error-all',str(original)],cwd=W/'after',check=True)
subprocess.run(['git','apply','--whitespace=error-all',str(original)],cwd=W/'after',check=True)
for path,values in m['files'].items():assert sha(W/'after'/path)==values['after'],path
soc='drivers/power/supply/mediatek/battery/asus_p00a_soc.inc'
for name in ['before','after']:
 p=W/name/soc;p.write_text(re.sub(r'\bcurrent\b','model_current',p.read_text()))
frozen=json.loads((R/'evidence/source-inputs-full-r5.json').read_text())['sha256']
assert sha(W/'before'/soc)==frozen['/srv/android/asus-android17/kernel-bpf-fd/'+soc]
p=W/'after/drivers/misc/mediatek/power/mt8163/asus_p00a/control.h';s=p.read_text()
for function,next_function,identifier in [('p00a_fault_sample','p00a_source','raw_fault'),('p00a_adc_sample','p00a_sample','raw_current')]:
 start=s.index('static int '+function+'(');end=s.index('static int '+next_function+'(',start)
 s=s[:start]+re.sub(r'\bcurrent\b',identifier,s[start:end])+s[end:]
p.write_text(s)
bundle=R/'charging-rebased';(bundle/'patches').mkdir(parents=True);(bundle/'evidence').mkdir();(bundle/'scripts').mkdir()
text='';files={}
for path in m['files']:
 before=W/'before'/path;after=W/'after'/path
 text+=''.join(difflib.unified_diff(before.read_text().splitlines(True) if before.is_file() else [],after.read_text().splitlines(True),fromfile='a/'+path if before.is_file() else '/dev/null',tofile='b/'+path))
 files[path]=dict(before=sha(before),after=sha(after))
patch=bundle/'patches/0003-charging-after-linux-compile-fixes.patch';patch.write_text(text)
manifest=dict(m,patch=patch.name,sha256=sha(patch),files=files,original_patch_sha256=m['sha256'],reviewed_rebase=['Preserve prior SOC current -> model_current Linux macro collision fix','Rename new fault and ADC local variables colliding with Linux current; no logic change'])
(bundle/'evidence/patch-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copy2(S/'scripts/apply_kernel.py',bundle/'scripts/apply_kernel.py')
subprocess.run(['git','apply','--check','--whitespace=error-all',str(patch)],cwd=W/'before',check=True)
subprocess.run(['git','apply','--whitespace=error-all',str(patch)],cwd=W/'before',check=True)
for path,values in files.items():assert sha(W/'before'/path)==values['after'],path
print('Reviewed charging rebase passes exact replay:',sha(patch))
