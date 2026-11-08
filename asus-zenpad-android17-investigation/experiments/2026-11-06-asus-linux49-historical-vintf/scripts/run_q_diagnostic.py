from pathlib import Path
import subprocess,json,time,hashlib,os,shutil
P=Path('/srv/android/asus-linux49-historical-vintf-20261106');B=P/'baseline';C=P/'diagnostic-q';W=P/'work-q';W.mkdir();shutil.copytree(B,C)
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();records=[]
def run(name,argv):
 t=time.monotonic();q=subprocess.run([str(x) for x in argv],capture_output=True,text=True,timeout=30)
 log=P/'evidence'/(name+'.log');log.write_text(q.stdout+q.stderr);r={'name':name,'argv':[str(x) for x in argv],'exit':q.returncode,'seconds':time.monotonic()-t,'log_sha256':h(log)};records.append(r);(P/'evidence'/(name+'.json')).write_text(json.dumps(r,indent=2));return q
assemble=P/'tools/bin/assemble_vintf';check=P/'tools/bin/checkvintf';K=P/'historical/q/android-4.9'
q=run('06-q-fixup',['python3','-B',P/'historical/kconfig_xml_fixup.py','--input',K/'android-base-conditional.xml','--output-matrix',W/'conditional.xml','--output-version',W/'version.txt']);assert q.returncode==0
version=(W/'version.txt').read_text();assert version=='4.9.165'
q=run('07-q-kernel-assemble',[assemble,'-i',W/'conditional.xml','--kernel',version+':'+str(K/'android-base.config'),'-o',W/'kernel.xml']);assert q.returncode==0
q=run('08-q-matrix-assemble',[assemble,'-i',str(P/'historical/compatibility_matrix.4.xml')+':'+str(W/'kernel.xml'),'-o',C/'system/etc/vintf/compatibility_matrix.p00a-legacy.xml']);assert q.returncode==0
s=(B/'vendor/etc/vintf/manifest.xml').read_text();(W/'vendor-input.xml').write_text(s.replace('<manifest version="9.0" type="device">','<manifest version="9.0" type="device" target-level="4">\n    <kernel target-level="4" />',1))
q=run('09-q-vendor-assemble',[assemble,'-i',W/'vendor-input.xml','-o',C/'vendor/etc/vintf/manifest.xml']);assert q.returncode==0
argv=[check,'--check-compat']
for part in ['system','vendor','product','system_ext','odm','apex']:argv+=['--dirmap',f'/{part}:{C}/{part}']
argv+=['--kernel',f'{P}/inputs/kernel.release:{P}/inputs/resolved.config']
for v in ['ro.product.first_api_level=23','ro.boot.product.hardware.sku=','ro.boot.product.vendor.sku=']:argv+=['--property',v]
q=run('10-q-checkvintf',argv)
result={'status':'REJECTED_Q_DIAGNOSTIC','commands':records,'check_exit':q.returncode,'check_log':q.stdout+q.stderr,'no_test_config_edits':True,'owned_bytes':sum(p.stat().st_size for p in P.rglob('*') if p.is_file()),'generated_kernel_xml':(W/'kernel.xml').read_text()}
assert result['owned_bytes']<256*1024*1024
(P/'evidence/q-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
