from pathlib import Path
import subprocess,json,hashlib,xml.etree.ElementTree as E,base64
P=Path('/srv/android/asus-linux49-historical-vintf-20261106');B=P/'baseline';C=P/'candidate-p';A=P/'tools/bin/assemble_vintf'
r={}
for label,root in [('baseline',B),('candidate',C)]:
 files=sorted(p for part in ['system','system_ext','product'] for p in (root/part/'etc/vintf').glob('compatibility_matrix*.xml'))
 argv=[str(A),'-i',':'.join(map(str,files)),'-o',str(P/'evidence'/('combined-'+label+'.xml'))]
 q=subprocess.run(argv,capture_output=True,text=True,timeout=30);r[label]={'argv':argv,'exit':q.returncode,'log':q.stdout+q.stderr};assert q.returncode==0
 r[label]['matrix']=(P/'evidence'/('combined-'+label+'.xml')).read_text()
source=Path('/srv/android/lineage24/system/libvintf/xsd/compatibilityMatrix')
r['schema_directory']=[p.name for p in source.iterdir() if p.is_file()]
for p in source.glob('*.xsd'):
 dest=P/'schema'/p.name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(p.read_bytes());r[str(p)]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'base64':base64.b64encode(p.read_bytes()).decode()}
print(json.dumps(r,indent=2))
