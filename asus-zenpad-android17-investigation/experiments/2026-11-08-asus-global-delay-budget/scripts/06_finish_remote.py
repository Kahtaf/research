from pathlib import Path
import base64,hashlib,json,os
B=Path('/srv/android/asus-minimal-platform-build-r3-20261108');R=Path('/srv/android/asus-global-delay-budget-20261108');K=R/'kernel';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changed=[];count=0;manifest=[]
for parent,ds,ns in os.walk(K):
 for name in ns:
  p=Path(parent)/name;rel=p.relative_to(K);old=B/'kernel'/rel
  if p.is_symlink():
   assert old.is_symlink() and os.readlink(p)==os.readlink(old);manifest.append([str(rel),'symlink',os.readlink(p)])
  else:
   h=sha(p);count+=1;manifest.append([str(rel),'sha256',h]);assert p.stat().st_ino!=old.stat().st_ino
   if h!=sha(old):changed.append(str(rel))
prep=json.loads((E/'preparation.json').read_text());assert set(changed)==set(prep['source_changes']),changed
for n,v in prep['source_changes'].items():assert sha(K/n)==v['postimage'] and sha(B/'kernel'/n)==v['preimage']
pins={n:dict(bytes=(B/'out'/n).stat().st_size,sha256=sha(B/'out'/n)) for n in ['arch/arm64/boot/Image.gz-dtb','System.map','.config']}
assert pins['arch/arm64/boot/Image.gz-dtb']['sha256']=='d164cbbee409d192caf9b0135238f0382c2f66ed31e622cc0bdb4f815baa8cec'
assert pins['System.map']['sha256']=='cd169931cd16ca97f2e77d55232a2693fb54422861d62bacc82ebb1862249237'
assert pins['.config']['sha256']=='01d6729f825798899e21192e6c33f96a80b47ccbedd5dc6cab10f78c1f9c7f31'
m=('\n'.join('\t'.join(row) for row in sorted(manifest))+'\n').encode();(E/'kernel-source-manifest.tsv').write_bytes(m)
rec=dict(status='FINAL_SOURCE_AND_ANCESTOR_PINS_PASS',source_files=count,source_changes=changed,source_manifest_sha256=hashlib.sha256(m).hexdigest(),ancestor_pins=pins,helper_builds=0,kernel_builds=1,ancestors_not_mutated=True,isolated_prefix=str(R),no_hardlinks=True,no_clean_or_timestamp_or_command_file_manipulation=True)
p=E/'final-preservation.json';p.write_text(json.dumps(rec,indent=2)+'\n')
files={}
for p in [E/'kernel-source-manifest.tsv',E/'final-preservation.json']:
 d=p.read_bytes();files['evidence/'+p.name]=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
print(json.dumps(dict(files=files,preservation=rec)))
