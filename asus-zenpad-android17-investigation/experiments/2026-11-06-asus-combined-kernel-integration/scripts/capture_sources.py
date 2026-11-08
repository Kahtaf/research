from pathlib import Path
import hashlib,json,subprocess,difflib,tarfile,datetime,stat,shutil
R=Path('/srv/android/asus-build-continuation');E=R/'integration-r5';K=R/'kernel';A=Path('/srv/android/asus-android17/kernel-bpf-fd')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,j): (E/n).write_text(json.dumps(j,indent=2)+'\n')
def manifest(root):return {str(p.relative_to(root)):({'symlink':str(p.readlink())} if p.is_symlink() else {'sha256':sha(p)}) for p in sorted(root.rglob('*')) if p.is_file() or p.is_symlink()}
b=json.loads((R/'evidence/snapshot.json').read_text());assert len(b['files'])==61976
for p,h in b['files'].items():assert sha(A/p)==h,p
old=json.loads((R/'evidence/combined-source-receipt.json').read_text());assert old['compiled_kernel_sha256']=='84007607154fd2b7d5f69dff63a1474589d2b6ddd0086511ff1cca4f34ebd59f'
net=json.loads((E/'network-applied.json').read_text());newdelta={p:{'before':v['baseline_sha256'],'after':v['tested_sha256']} for p,v in net['files'].items()}
newdelta.update({v['path']:{'before':v['before_sha256'],'after':v['after_sha256']} for v in net['firstboot_preserved']})
assert not set(old['changes'])&set(newdelta)
expected=old['changes']|newdelta
files=subprocess.check_output(['git','-C',str(K),'ls-files','--cached','--others','--exclude-standard','-z']).decode().strip('\0').split('\0')
changes={};patch=[]
for p in sorted(set(files)):
 h=sha(K/p);pre=b['files'].get(p)
 if h==pre:continue
 changes[p]={'before':pre,'after':h}
 oldtext=(A/p).read_text().splitlines(keepends=True) if pre else []
 patch.append(f'diff --git a/{p} b/{p}\n')
 if pre is None:patch.append('new file mode 100644\n')
 patch.extend(difflib.unified_diff(oldtext,(K/p).read_text().splitlines(keepends=True),fromfile='a/'+p if pre else '/dev/null',tofile='b/'+p))
assert changes==expected,{'unexpected':list(set(changes)-set(expected)),'missing':list(set(expected)-set(changes)),'mismatched':[p for p in changes.keys()&expected.keys() if changes[p]!=expected[p]]}
P=E/'combined-from-active-soc.patch';P.write_text(''.join(patch))
subprocess.run(['git','-C',str(A),'apply','--check','--whitespace=nowarn',str(P)],check=True)
with tarfile.open(E/'combined-source-changes.tar.gz','w:gz') as t:
 for p in changes:t.add(K/p,arcname=p)
save('source-receipt.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),base_commit=b['head'],active_source_files_verified=len(b['files']),active_source_unchanged=True,prior_r3_changes_preserved=len(old['changes']),declared_new_delta=newdelta,changes=changes,patch_sha256=sha(P),patch_applies_to_frozen_active=True,source_archive_sha256=sha(E/'combined-source-changes.tar.gz')))
basecfg=json.loads((R/'evidence/runtime-config-baseline.json').read_text());basesrc=json.loads((R/'evidence/runtime-source-baseline.json').read_text())['selected_files']
rows={p:dict(before=v['sha256'],actual=sha(K/p),expected=newdelta.get(p,{}).get('after',v['sha256']),declared_delta=p in newdelta) for p,v in basesrc.items()}
assert len(rows)==282 and all(x['actual']==x['expected'] for x in rows.values())
save('runtime-source-preservation.json',dict(total=len(rows),unchanged=sum(x['before']==x['actual'] for x in rows.values()),declared_delta=[p for p,x in rows.items() if x['declared_delta']],files=rows))
product=json.loads((R/'evidence/product-staging.json').read_text());active=Path(product['active']);candidate=Path(product['candidate']);assert manifest(active)==product['before']
now=manifest(candidate);diff={p:dict(before=product['before'].get(p),after=now.get(p)) for p in product['before'].keys()|now.keys() if product['before'].get(p)!=now.get(p)}
assert set(diff)==set(product['changes'])
for p,row in diff.items():
 if p!='BoardConfig.mk':assert row==product['changes'][p],p
assert sha(Path('/srv/android/lineage24/system/connectivity/wificond/wificond.rc'))==product['wificond_before_sha256']
assert 'soc/11230000.mmc' in (candidate/'rootdir/fstab.mt8163').read_text()
assert 'TARGET_KERNEL_CONFIG := asus_p00a_defconfig' in (candidate/'BoardConfig.mk').read_text()
for p,row in net['connectivity'].items():assert sha(R/'platform-connectivity'/p)==row['tested_sha256']
shutil.copytree(candidate,E/'product-device',symlinks=True)
shutil.copytree(R/'platform-connectivity',E/'platform-connectivity')
assert manifest(E/'product-device')==now
save('staged-product-receipt.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),active=str(active),candidate=str(E/'product-device'),active_unchanged=True,before=product['before'],after=now,changes=diff,staged_connectivity=net['connectivity'],connectivity_patch='11-network-policy-and-required-loader.patch',optional_patch12_staged=False,physical_config_copied=False,prebuilt_kernel_replacement='Deferred: use final integration-r5/Image.gz-dtb and physical resolved.config under future full-build integration lock',fstab_alias_preserved='soc/11230000.mmc',radio_Health_Google='Existing candidate retained; full Soong, Google byte checks, VINTF and runtime not completed'))
print('PASS:61976 active files unchanged;',len(changes),'exact source changes;282 runtime files checked;',len(diff),'staged product differences; Connectivity11 retained.')
