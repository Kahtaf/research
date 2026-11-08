from pathlib import Path
import hashlib,json,subprocess,shutil,resource,datetime
R=Path('/srv/android/asus-genuine-service-runtime');P=Path('/srv/android/asus-firstboot-runtime');T=Path('/srv/android/lineage24');G=R/'inputs/policy-r6';G.mkdir();B=R/'inputs/capture-r1/out/soong/.intermediates/system/sepolicy';old=P/'inputs/early-r1/compiled-policy'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Exact selected module command captured as evidence only. No Ninja execution.
command=''
module=''
for line in (T/'out/soong/build.lineage_p00a.8.ninja').open():
 if line.startswith('# Module:'):module=line.split(':',1)[1].strip()
 if module=='precompiled_sepolicy' and line.startswith('    command ='):
  command=line.strip()[len('command = '):];break
assert command.startswith('out/host/linux-x86/bin/secilc -v -m -M true -G -c 30 ')
# Recover only from already frozen CILs, including two unchanged supporting CILs
# from the qualified capture. Byte-identical recompilation is the acceptance gate.
rels=command.split(' -o ',1)[0].split(' -c 30 ',1)[1].split();rows=[];argv=[]
for rel in rels:
 local=Path(rel).relative_to('out/soong/.intermediates/system/sepolicy');src=B/local
 provenance='capture-r1'
 if not src.is_file():src=old/local;provenance='qualified-prior-capture'
 assert src.is_file(),src
 dst=G/'cil'/local;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst);rows.append(dict(input=str(local),source=str(src),sha256=sha(dst),provenance=provenance));argv.append(str(dst))
tool=G/'secilc';src=T/'out/host/linux-x86/bin/secilc';a=sha(src);shutil.copy2(src,tool);assert sha(src)==sha(tool)==a
out=G/'recompiled-policy';cmd=[str(tool),'-v','-m','-M','true','-G','-c','30',*argv,'-o',str(out),'-f','/dev/null']
def limit():resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
p=subprocess.run(cmd,capture_output=True,text=True,preexec_fn=limit,timeout=60);expected=next((B/'precompiled_sepolicy').rglob('precompiled_sepolicy'))
rec=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),official_command=command,inputs=rows,compiler_sha256=a,command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,expected_policy_sha256=sha(expected),actual_policy_sha256=sha(out) if out.exists() else None)
(R/'evidence/policy-r6-recompilation.json').write_text(json.dumps(rec,indent=2));assert p.returncode==0,p.stderr;assert sha(out)==sha(expected),(sha(out),sha(expected))
I=R/'inputs/boot-r6';shutil.copytree(R/'inputs/boot-r5',I,symlinks=True);root=I/'root';before=sha(root/'system/vendor/etc/selinux/precompiled_sepolicy')
for prefix,part in [('plat','system'),('system_ext','system/system_ext'),('product','system/product'),('vendor','system/vendor')]:
 src=next((B/(prefix+'_sepolicy.cil')).rglob(prefix+'_sepolicy.cil'));dest=root/part/'etc/selinux';shutil.copy2(src,dest/src.name)
 if prefix!='vendor':
  mapping=next((B/(prefix+'_mapping_file')).rglob('202704.cil'));assert sha(mapping)==sha(dest/'mapping/202704.cil')
  digest=hashlib.sha256(src.read_bytes()+mapping.read_bytes()).hexdigest()+'\n';assert digest==(dest/(prefix+'_sepolicy_and_mapping.sha256')).read_text()
shutil.copy2(expected,root/'system/vendor/etc/selinux/precompiled_sepolicy')
# Validate every generated service label against this exact current snapshot policy.
valid=[]
for f in root.glob('system/**/etc/selinux/*service_contexts'):
 mode='-l' if 'hwservice' in f.name else '-v' if f.name=='vndservice_contexts' else '-s';c=[str(R/'inputs/service-contexts-r1/checkfc'),mode,str(expected),str(f)];v=subprocess.run(c,capture_output=True,text=True,preexec_fn=limit,timeout=20);valid.append(dict(command=c,returncode=v.returncode,stderr=v.stderr));assert v.returncode==0
(R/'evidence/policy-r6-installation.json').write_text(json.dumps(dict(before_sha256=before,after_sha256=sha(expected),bytes=expected.stat().st_size,changed_cil='vendor_sepolicy.cil; platform/system_ext/product and mappings already match',context_validation=valid,origin='pre-r6 capture-r1 at 22:19:09 UTC; not the later supplemental capture; actual product-compiled policy reproduced byte-for-byte from frozen genuine CILs'),indent=2))
print('Current pinned policy exactly reproduced and installed:',sha(expected))
