#!/usr/bin/env python3
import pathlib,hashlib,json,subprocess,tarfile,difflib,datetime
R=pathlib.Path('/srv/android/asus-build-continuation');A=pathlib.Path('/srv/android/asus-android17/kernel-bpf-fd');K=R/'kernel'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((R/'evidence/snapshot.json').read_text());assert all(sha(A/p)==h for p,h in baseline['files'].items()),'Active kernel changed'
files=subprocess.check_output(['git','-C',str(K),'ls-files','--cached','--others','--exclude-standard','-z']).decode().strip('\0').split('\0')
changes={};patch=[]
for p in sorted(set(files)):
 h=sha(K/p);oldhash=baseline['files'].get(p)
 if h==oldhash:continue
 old=(A/p).read_text().splitlines(keepends=True) if oldhash else []
 new=(K/p).read_text().splitlines(keepends=True)
 patch.append(f'diff --git a/{p} b/{p}\n')
 if oldhash is None:patch.append('new file mode 100644\n')
 patch.extend(difflib.unified_diff(old,new,fromfile='a/'+p if oldhash else '/dev/null',tofile='b/'+p))
 changes[p]={'before':oldhash,'after':h}
P=R/'evidence/combined-from-active-soc.patch';P.write_text(''.join(patch))
subprocess.run(['git','-C',str(A),'apply','--check','--whitespace=nowarn',str(P)],check=True)
with tarfile.open(R/'artifacts/combined-source-changes.tar.gz','w:gz') as t:
 for p in changes:t.add(K/p,arcname=p)
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_owner':'asus-build-continuation','base_commit':baseline['head'],'active_source_unchanged':True,'source_files_verified':len(baseline['files']),'compiled_kernel_sha256':sha(R/'build/arch/arm64/boot/Image.gz-dtb'),'config_sha256':sha(R/'build/.config'),'patch_sha256':sha(P),'patch_applies_to_frozen_active':True,'changes':changes}
(R/'evidence/combined-source-receipt.json').write_text(json.dumps(report,indent=2)+'\n');print('Verified',len(baseline['files']),'active source files unchanged;',len(changes),'combined changes')
