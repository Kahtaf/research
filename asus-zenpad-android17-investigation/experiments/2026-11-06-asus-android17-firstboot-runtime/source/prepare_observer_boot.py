from pathlib import Path
import shutil,json,hashlib,subprocess as s,os
R=Path('/srv/android/asus-firstboot-runtime');T=Path('/srv/android/lineage24');I=R/'inputs/boot-r6';shutil.copytree(R/'inputs/boot-r5',I,symlinks=True);root=I/'root';manifest=[]
def put(src,dst):
 b=src.read_bytes();assert b==src.read_bytes();dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b);manifest.append(dict(source=str(src),path=str(dst.relative_to(I)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
for p in (root/'system/etc/task_profiles').glob('*/*.json'):
 name=p.parent.name+'_'+p.name;shutil.copyfile(p,root/'system/etc/task_profiles'/name)
# Remove only the incorrect fixture-only path from prior preparation; retain its frozen input revision.
for d in ['cgroups','task_profiles']:shutil.rmtree(root/'system/etc/task_profiles'/d)
put(R/'artifacts/observer',root/'system/bin/firstboot-observer');(root/'system/bin/firstboot-observer').chmod(0o755)
ctx=I/'work/file_contexts';ctx.write_text(ctx.read_text()+'\n/system/bin/firstboot-observer u:object_r:shell_exec:s0\n')
cmd=[str(I/'tools/sefcontext_compile'),'-o',str(I/'work/file_contexts.bin'),str(ctx)];p=s.run(cmd,capture_output=True,text=True);(I/'context-command.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,p.stderr
f=root/'system/etc/init/firstboot-observe.rc';f.write_text(f.read_text()+'''
service firstboot-observer /system/bin/firstboot-observer
    class core
    user shell
    group shell readproc
    seclabel u:r:shell:s0
    console
    disabled
    oneshot

on init
    start firstboot-observer
''')
for src,dst in [('system/apex/apexd/apexd.rc','system/etc/init/apexd.rc'),('system/security/keystore2/keystore2.rc','system/etc/init/keystore2.rc'),('system/hwservicemanager/hwservicemanager.rc','system/system_ext/etc/init/hwservicemanager.rc'),('frameworks/native/cmds/servicemanager/servicemanager.rc','system/etc/init/servicemanager.rc'),('hardware/interfaces/keymaster/4.0/default/ACCOUNT_REDACTED','system/vendor/etc/init/ACCOUNT_REDACTED')]:put(T/src,root/dst)
(I/'extension-manifest.json').write_text(json.dumps(manifest,indent=2));print('observer boot prepared')
