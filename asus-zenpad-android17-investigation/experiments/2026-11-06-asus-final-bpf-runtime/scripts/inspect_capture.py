from pathlib import Path
import subprocess as s,json
O=Path('/srv/android/asus-final-bpf-runtime-20261106');print([(p.name,p.stat().st_size) for p in (O/'capture').iterdir()]);
for p in (O/'capture').glob('*.img'):
 print(s.run(['file',str(p)],capture_output=True,text=True).stdout)
print(s.run(['which','fsck.erofs','dump.erofs','debugfs','aarch64-linux-gnu-gcc'],capture_output=True,text=True).stdout)
R=Path('/srv/android/asus-root-enabled-incremental-r1/host-r2/validation');d=json.loads((R/'r8-product-provenance.json').read_text());print('PAYLOAD',[(r.get('destination'),r.get('path'),r.get('module'),r.get('installed_path'),r.get('sha256')) for r in d['payloads']][:5]);
print('ROOTBYTES',sum(p.stat().st_size for p in Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106/inputs/runtime-root-r2').rglob('*') if p.is_file()))
