from pathlib import Path
import json,subprocess
from vm import R,channel
root=json.loads((R/'evidence/identity.json').read_text())['remote_root']
script='''from pathlib import Path
import hashlib,json,subprocess
R=Path(ROOT);B=Path('/srv/android/asus-sparse-watchdog-observation-20261108-e0b1a1ba')
p=R/'kernel/arch/arm64/kernel/head.S';base=B/'kernel/arch/arm64/kernel/head.S'
assert p.read_bytes()==base.read_bytes() and p.stat().st_ino!=base.stat().st_ino
assert (R/'out/source').resolve()==R/'kernel'
s=p.read_text();ls=s.splitlines();hits=[j for j,l in enumerate(ls) if any(x in l for x in ['4403','initrd','ASUS_ENTRY_TAG'])]
lines=sorted(set(k for j in hits for k in range(max(0,j-4),min(len(ls),j+5))))
dis=subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--disassemble=stext',str(R/'out/vmlinux')],text=True)
print(json.dumps(dict(head_source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),head_source_unchanged=True,out_source_independent=str((R/'out/source').resolve()),guard_source='\\n'.join(str(j+1)+': '+ls[j] for j in lines),stext_disasm=dis)))
'''.replace('ROOT',repr(root))
p=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True);assert not p.returncode,p.stderr
d=json.loads(p.stdout);(R/'evidence/entry-check.json').write_text(json.dumps(d,indent=2)+'\n');print(d['guard_source'])
