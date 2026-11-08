from pathlib import Path
T=Path('/srv/android/lineage24')
for rel in ['out/target/product/p00a/.installable_files','out/target/product/p00a/product_packages.txt','out/target/product/p00a/obj/PACKAGING/system_intermediates/file_list.txt']:
 p=T/rel;print('FILE',rel,p.exists())
 if p.exists():
  text=p.read_text();print('SIZE',len(text));print('\n'.join(x for x in text.splitlines() if 'bpf' in x.lower() or '.bpf' in x))
for name in ['out/build-lineage_p00a.ninja','out/soong/build.lineage_p00a.ninja']:
 keep=0
 for l in (T/name).open():
  if l.startswith('rule rule359722') or l.startswith('build out/target/product/p00a/obj/PACKAGING/system_intermediates/system.img:') or (l.startswith('build ') and ('/bpfloader/android_arm64_armv8-a/unstripped/bpfloader:' in l or ('bpf' in l and '_intermediates/' in l and 'ETC/' in l and l.startswith('build out/target/product/p00a/obj/ETC/')))):keep=5
  if keep:print(name,l.rstrip()[:10000]);keep-=1
