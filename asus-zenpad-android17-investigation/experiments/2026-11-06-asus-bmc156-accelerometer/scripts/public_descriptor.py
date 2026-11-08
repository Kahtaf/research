from pathlib import Path
import struct,subprocess,re,json,hashlib
p=Path('/srv/android/asus-hardware-completeness-audit/public-selected/lib64_hw_sensors.mt8163.so');d=p.read_bytes()
s=subprocess.check_output(['readelf','-Ws',str(p)],text=True);row=next(l for l in s.splitlines() if l.endswith(' sSensorList'));address=int(row.split()[1],16)
# Resolve the public ELF64 virtual address using its program headers.
e=struct.unpack_from('<16sHHIQQQIHHHHHH',d)
for i in range(e[10]):
 ph=struct.unpack_from('<IIQQQQQQ',d,e[5]+i*e[9]);typ,flags,off,va,pa,filesz,memsz,align=ph
 if typ==1 and va<=address<va+filesz:
  at=off+address-va;break
else:raise ValueError('no PT_LOAD')
version,handle,typ,maxrange,resolution,power,mindelay=struct.unpack_from('<iiifffi',d,at+16)
assert handle==1 and typ==1
print(json.dumps(dict(source=str(p),sha256=hashlib.sha256(d).hexdigest(),symbol=row.strip(),offset=at,version=version,handle=handle,type=typ,maxRange=maxrange,resolution=resolution,power=power,minDelay=mindelay),indent=2))
