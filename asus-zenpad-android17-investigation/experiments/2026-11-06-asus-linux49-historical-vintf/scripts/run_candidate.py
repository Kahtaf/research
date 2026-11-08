from pathlib import Path
import subprocess,json,time,hashlib,os,shutil,xml.etree.ElementTree as E
P=Path('/srv/android/asus-linux49-historical-vintf-20261106');B=P/'baseline';C=P/'candidate-p';W=P/'work-p';W.mkdir();shutil.copytree(B,C)
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[];env=os.environ.copy()
# Keep the normal assembler defaults; no ignore/runtime/kernel bypass flags.
def run(name,argv):
 t=time.monotonic();q=subprocess.run([str(x) for x in argv],capture_output=True,text=True,timeout=30,env=env)
 log=P/'evidence'/(name+'.log');log.write_text(q.stdout+q.stderr)
 r={'name':name,'argv':[str(x) for x in argv],'exit':q.returncode,'seconds':time.monotonic()-t,'log_sha256':h(log)};records.append(r)
 (P/'evidence'/(name+'.json')).write_text(json.dumps(r,indent=2));return q
assemble=P/'tools/bin/assemble_vintf';check=P/'tools/bin/checkvintf';K=P/'historical/p/android-4.9'
q=run('01-p-fixup',['python3','-B',P/'historical/kconfig_xml_fixup.py','--input',K/'android-base-conditional.xml','--output-matrix',W/'conditional.xml','--output-version',W/'version.txt']);assert q.returncode==0
version=(W/'version.txt').read_text();assert version=='4.9.84'
arg=version+':'+':'.join(str(K/f) for f in ['android-base.config','android-base-arm.config','android-base-arm64.config'])
q=run('02-p-kernel-assemble',[assemble,'-i',W/'conditional.xml','--kernel',arg,'-o',W/'kernel.xml']);assert q.returncode==0
q=run('03-p-matrix-assemble',[assemble,'-i',str(P/'candidate-source/device/asus/p00a/vintf-legacy/compatibility_matrix.p00a-p.xml')+':'+str(W/'kernel.xml'),'-o',C/'system/etc/vintf/compatibility_matrix.p00a-legacy.xml']);assert q.returncode==0
original=B/'vendor/etc/vintf/manifest.xml';s=original.read_text();assert '<manifest version="9.0" type="device">' in s
(W/'vendor-input.xml').write_text(s.replace('<manifest version="9.0" type="device">','<manifest version="9.0" type="device" target-level="3">\n    <kernel target-level="3" />',1))
q=run('04-p-vendor-assemble',[assemble,'-i',W/'vendor-input.xml','-o',C/'vendor/etc/vintf/manifest.xml']);assert q.returncode==0
argv=[check,'--check-compat']
for part in ['system','vendor','product','system_ext','odm','apex']:argv+=['--dirmap',f'/{part}:{C}/{part}']
argv+=['--kernel',f'{P}/inputs/kernel.release:{P}/inputs/resolved.config']
for v in ['ro.product.first_api_level=23','ro.boot.product.hardware.sku=','ro.boot.product.vendor.sku=']:argv+=['--property',v]
q=run('05-p-checkvintf',argv)
changed=[];unchanged=[]
for src in B.rglob('*'):
 if src.is_file():
  rel=src.relative_to(B);(unchanged if h(src)==h(C/rel) else changed).append(str(rel))
result={'commands':records,'check_exit':q.returncode,'existing_metadata_changed':changed,'existing_metadata_unchanged':unchanged,'added_metadata':['system/etc/vintf/compatibility_matrix.p00a-legacy.xml'],'version_file':(P/'inputs/kernel.release').read_text(),'config_sha256':h(P/'inputs/resolved.config'),'limits':{'cpus':list(os.sched_getaffinity(0)),'individual_timeout_seconds':30},'owned_bytes':sum(p.stat().st_size for p in P.rglob('*') if p.is_file()),'generated':{str(p.relative_to(P)):{'sha256':h(p),'text':p.read_text()} for p in [W/'kernel.xml',C/'system/etc/vintf/compatibility_matrix.p00a-legacy.xml',C/'vendor/etc/vintf/manifest.xml']}}
assert changed==['vendor/etc/vintf/manifest.xml'];assert result['owned_bytes']<256*1024*1024
(P/'evidence/p-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
