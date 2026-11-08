from pathlib import Path
import urllib.request,json,base64,hashlib
r=Path(__file__).resolve().parents[1];repo='https://android.googlesource.com/platform/bionic'
p=r/'evidence/bionic-commit.json'
if not p.exists():p.write_bytes(urllib.request.urlopen(repo+'/+/refs/heads/main?format=JSON',timeout=30).read())
commit=json.loads(p.read_bytes()[4:])['commit'];pins=[]
for rel in ['libc/kernel/uapi/asm-arm64/asm/'+x for x in ['fcntl.h','mman.h','ioctls.h','ioctl.h','socket.h','sockios.h','sigcontext.h','signal.h','stat.h','posix_types.h','sve_context.h','siginfo.h','errno.h']]+['libc/kernel/uapi/asm-generic/'+x for x in ['signal.h','signal-defs.h','siginfo.h']]:
 url=f'{repo}/+/{commit}/{rel}?format=TEXT'
 d=base64.b64decode(urllib.request.urlopen(url,timeout=30).read());dest=r/'supplement'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(d);pins.append({'url':url,'commit':commit,'path':rel,'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)})
(r/'evidence/uapi-pins.json').write_text(json.dumps(pins,indent=2)+'\n');print('Pinned',len(pins),'headers',commit)
