from pathlib import Path
import subprocess as s,json,hashlib,os,shlex,re
R=Path('/srv/android/asus-firstboot-runtime');T=Path('/srv/android/lineage24');I=R/'inputs/property-generator-r2';I.mkdir();M=I/'mirror';M.mkdir();manifest=[];runs=[]
def freeze(rel,dest=None):
 src=T/rel;d=src.read_bytes();assert d==src.read_bytes();out=M/(dest or rel);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(d);out.chmod(src.stat().st_mode&0o777);manifest.append(dict(source=str(src),path=str(out.relative_to(I)),sha256=hashlib.sha256(d).hexdigest(),bytes=len(d)));return out
for p in ['out/build_date.txt','out/soong/build_uuid-lineage_p00a.txt','out/soong/build_number.txt','out/soong/build_hostname.txt','out/target/product/p00a/build_fingerprint-lineage_p00a.txt','out/target/product/p00a/build_system_fingerprint-lineage_p00a.txt','out/soong/soong.lineage_p00a.variables','out/soong/soong.lineage_p00a.extra.variables']:freeze(p)
for src,name in [('build/make/tools/post_process_props.py','post_process_props'),('build/soong/scripts/uffd_gc_utils.py','uffd_gc_utils.py'),('build/make/tools/check_radio_versions.py','check_radio_versions')]:freeze(src,'out/host/linux-x86/bin/'+name).chmod(0o755)
for p in ['build/soong/scripts/merge_json.py','build/soong/scripts/gen_build_prop.py','build/soong/android/product_config.go','build/soong/java/sdk.go']:freeze(p)
(I/'bin').mkdir();os.symlink('/usr/bin/python3',I/'bin/python');env=os.environ.copy();env['PATH']=str(I/'bin')+':'+env['PATH'];env['TMPDIR']=str(R/'tmp');env['PYTHONDONTWRITEBYTECODE']='1'
for p in ['out/target/product/p00a/system/vendor','out/target/product/p00a/obj/ETC/android_info_prop_intermediates','out/soong/.intermediates/build/soong/product_config']:(M/p).mkdir(parents=True,exist_ok=True)
def run(argv):
 p=s.run(argv,cwd=M,env=env,capture_output=True,text=True);runs.append(dict(command=argv,cwd=str(M),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(I/'commands.json').write_text(json.dumps(runs,indent=2));assert p.returncode==0,p.stderr
run(['python3',str(M/'build/soong/scripts/merge_json.py'),'out/soong/.intermediates/build/soong/product_config/product_config.json','out/soong/soong.lineage_p00a.variables','out/soong/soong.lineage_p00a.extra.variables'])
for n in ['ninja-android-info.txt','ninja-vendor-build.prop.txt']:
 text=(R/'evidence'/n).read_text();line=next(l for l in text.splitlines() if l.startswith(' command = '));cmd=line[len(' command = '):].replace('$$','$');argv=['/bin/sh','-c',cmd];assert cmd.startswith('/bin/bash -c ');assert '/srv/android/lineage24' not in cmd
 if n=='ninja-vendor-build.prop.txt':
  # This exact dependency rule comes from captured rule114957. grep's no-match is piped to sed.
  run(['/bin/bash','-c',"cat out/target/product/p00a/android-info.txt | grep 'require version-' | sed -e 's/require version-/ro.build.expect./g' > out/target/product/p00a/obj/ETC/android_info_prop_intermediates/android-info.prop"])
 run(argv)
(I/'input-manifest.json').write_text(json.dumps(manifest,indent=2));f=M/'out/target/product/p00a/system/vendor/build.prop';(I/'output-manifest.json').write_text(json.dumps(dict(path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),bytes=f.stat().st_size),indent=2));print('genuine vendor properties generated',f.stat().st_size)
