from pathlib import Path
import os, json, shutil, hashlib, subprocess, difflib, datetime
R=Path('/srv/android/asus-gpio28-lifecycle-full-kernel-20261107-r1')
B=Path('/srv/android/asus-bmc156-full-kernel-r1'); K=R/'kernel'; O=R/'out'; E=R/'evidence'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,v): (E/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))}); os.nice(10)
assert not K.exists() and not O.exists()
assert sha(B/'out/.config')=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1'
assert sha(B/'out/arch/arm64/boot/dts/mediatek/asus-p00a.dtb')=='a099d0538b270e23ec0d034b507eef9248252a3c459a11aa70edb6520bfd2b77'
assert shutil.disk_usage(R).free>4*1024**3
s1=json.loads((E/'stage1-pins.json').read_text()); s2=json.loads((E/'stage2-pins.json').read_text())
paths=sorted({p['path'] for p in s1+s2 if p['path']!='resolved.config'})
# Read and hash only the eight source paths in the delivered patches.
pre={p: {'sha256':sha(B/'kernel'/p),'bytes':(B/'kernel'/p).stat().st_size} if (B/'kernel'/p).exists() else None for p in paths}
for row in s1:
 p=B/'out/.config' if row['path']=='resolved.config' else B/'kernel'/row['path']
 assert (not p.exists()) if row['destination_must_be_absent'] else sha(p)==row['pre_sha256'],row
for row in s2:
 if row['path'] not in {x['path'] for x in s1}:
  p=B/'kernel'/row['path']
  assert (not p.exists()) if row['destination_must_be_absent'] else sha(p)==row['pre_sha256'],row
# Ordinary isolated copy, without Git metadata or build objects; no complete source hash/manifest sweep.
assert not (B/'kernel/.git').exists()
copy_stats={'files':0,'bytes':0,'allocated_file_bytes':0}
def copy_one(src,dst):
 shutil.copy2(src,dst)
 st=os.stat(dst);copy_stats['files']+=1;copy_stats['bytes']+=st.st_size;copy_stats['allocated_file_bytes']+=st.st_blocks*512
 assert copy_stats['allocated_file_bytes']<2*1024**3,'source alone exceeded owned disk budget'
 return dst
shutil.copytree(B/'kernel',K,symlinks=True,copy_function=copy_one)
O.mkdir(); (R/'tmp').mkdir(); shutil.copy2(B/'out/.config',O/'.config'); shutil.copy2(B/'out/.config',E/'baseline.config')
dump('source-copy.json',copy_stats)

def check_stage(rows,after):
 for row in rows:
  p=O/'.config' if row['path']=='resolved.config' else K/row['path']
  expected=row['post_sha256' if after else 'pre_sha256']
  assert (not p.exists()) if expected is None else sha(p)==expected,(str(p),expected)
def patch(name,cwd):
 cmd=['patch','--batch','--forward','--fuzz=0','-p1','-i',str(R/'patches'/name)]
 with (E/(name+'.log')).open('x') as f: subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,check=True)
check_stage(s1,False)
patch('01-stock-gpio28.patch',K);patch('02-resolved-config.patch',O)
check_stage(s1,True);check_stage(s2,False)
patch('03-lifecycle.patch',K);check_stage(s2,True)
final=[];combined=[]
for p in paths:
 dst=K/p; before=B/'kernel'/p
 final.append({'path':p,'before':pre[p],'after':{'sha256':sha(dst),'bytes':dst.stat().st_size},'destination_must_be_absent':pre[p] is None})
 combined.extend(difflib.unified_diff(before.read_text().splitlines(True) if before.exists() else [],dst.read_text().splitlines(True),fromfile='a/'+p if before.exists() else '/dev/null',tofile='b/'+p))
(R/'patches/combined-from-bmc.patch').write_text(''.join(combined))
dump('pre-post-pins.json',final)
# Small untouched source sample only. No blanket verification sweep.
sample=['sound/soc/mediatek/mt_soc_audio_8163/mt_soc_pcm_routing.c','sound/soc/mediatek/mt_soc_audio_8163/mt_soc_afe_control.c','drivers/pinctrl/mediatek/pinctrl-mt8163.c','init/main.c','mm/vmscan.c','net/core/dev.c']
selected={}
for p in sample:
 if (B/'kernel'/p).is_file():
  a=sha(B/'kernel'/p);b=sha(K/p);assert a==b;selected[p]={'baseline':a,'owned':b}
dump('unchanged-selected-sources.json',selected)
dump('preparation.json',{'status':'pinned patches replayed with fuzz0','source':str(K),'output':str(O),'baseline':str(B),'source_paths':paths,'source_copy':copy_stats,'source_has_no_git':True,'affinity':sorted(os.sched_getaffinity(0)),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(json.dumps({'status':'prepared','prefix':str(R),'source_copy':copy_stats,'changed_source_paths':len(paths)}))
