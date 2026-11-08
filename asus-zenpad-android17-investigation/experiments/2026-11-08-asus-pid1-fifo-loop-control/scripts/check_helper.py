from pathlib import Path
import base64,json,subprocess
from vm import R,channel
root=json.loads((R/'evidence/identity.json').read_text())['remote_root']
script='''from pathlib import Path
import base64,json,subprocess
R=Path(ROOT)
p=R/'artifacts/init.unstripped'
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(p)],text=True)
dis=''
for sym in ['main','observe','monotonic_clock','finish']:
 dis+=subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--disassemble='+sym,str(p)],text=True)
print(json.dumps(dict(dis=dis,symbols='\\n'.join(l for l in nm.splitlines() if l.split()[-1] in ['main','observe','monotonic_clock','finish','event']))))
'''.replace('ROOT',repr(root))
p=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True);assert not p.returncode,p.stderr
d=json.loads(p.stdout);(R/'evidence/helper-scoped.disasm').write_text(d['dis']);(R/'evidence/helper-symbols.txt').write_text(d['symbols']);print(d['symbols'])
