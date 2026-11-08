from pathlib import Path
import re,hashlib
for root in ['/srv/android/lineage24/vendor/asus/p00a','/srv/android/asus-device-product/staged-vendor-r7/vendor/asus/p00a']:
 p=Path(root);print('\nROOT',root,'EXISTS',p.exists())
 for f in sorted(p.rglob('*')):
  if f.is_file() and f.suffix in ['.mk','.bp','.xml']:
   print('FILE',f,'SHA256',hashlib.sha256(f.read_bytes()).hexdigest())
   for i,l in enumerate(f.read_text(errors='replace').splitlines(),1):
    if f.suffix=='.mk' or re.search('name:|srcs:|vintf|audio|camera|sensor',l): print(i,l)
