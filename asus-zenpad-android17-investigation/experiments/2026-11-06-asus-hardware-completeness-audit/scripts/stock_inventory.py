from pathlib import Path
import subprocess,json
img=Path('/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img')
print('IMAGE',img,'SIZE',img.stat().st_size,'Hash not repeated; parent independently verified OEM equality.')
for d in ['/vendor/lib/hw','/vendor/lib64/hw','/vendor/lib','/vendor/lib64','/etc','/vendor/etc','/usr/idc','/usr/keylayout']:
 r=subprocess.run(['debugfs','-R','ls -p '+d,str(img)],capture_output=True,text=True)
 print('\nDIR',d); print(r.stdout)
