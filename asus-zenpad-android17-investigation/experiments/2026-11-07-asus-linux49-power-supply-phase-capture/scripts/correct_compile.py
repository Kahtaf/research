from pathlib import Path
import json,base64,os,subprocess
from vm import R,channel
i=json.loads((R/'evidence/identity.json').read_text());pins=json.loads((R/'evidence/source-pins.json').read_text())
s=(R/'scripts/build_remote.py').read_text().replace("assert not (E/'build-status.json').exists(),'One complete kernel candidate only'", "assert json.loads((E/'build-status.json').read_text())['status']=='failed'\n(E/'build-status-attempt-1.json').write_bytes((E/'build-status.json').read_bytes())")
# Actual inherited string is slightly different, require the failed-attempt guard.
s=s.replace("assert not (E/'build-status.json').exists(),'One complete kernel candidate only'",'')
if "assert not (E/'build-status.json').exists()" in s:
 a=s.index("assert not (E/'build-status.json').exists()");z=s.index('\n',a)
 s=s[:a]+"assert json.loads((E/'build-status.json').read_text())['status']=='failed'\n(E/'build-status-attempt-1.json').write_bytes((E/'build-status.json').read_bytes())"+s[z:]
s=s.replace('compile_attempts=1','compile_attempts=2').replace("'compile-1.log'","'compile-2.log'")
assert 'build-status-attempt-1.json' in s
(R/'scripts/build_correction_remote.py').write_text(s)
files={'kernel/'+n:(R/'source'/n).read_bytes() for n in pins};files.update({'evidence/source-pins.json':(R/'evidence/source-pins.json').read_bytes(),'scripts/build_correction_remote.py':s.encode()})
script='''from pathlib import Path
import json,base64,subprocess
R=Path(ROOT)
assert json.loads((R/'evidence/build-status.json').read_text())['status']=='failed'
assert 'implicit declaration of function' in (R/'evidence/compile-1.log').read_text()
for n,v in FILES.items():(R/n).write_bytes(base64.b64decode(v))
with (R/'evidence/build-correction.stdout').open('w') as out,(R/'evidence/build-correction.stderr').open('w') as err:
 p=subprocess.Popen(['python3','-B',str(R/'scripts/build_correction_remote.py')],stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
print(json.dumps(dict(same_candidate_compile_correction_pid=p.pid)))
'''.replace('ROOT',repr(i['remote_root'])).replace('FILES',repr({n:base64.b64encode(v).decode() for n,v in files.items()}))
os.chdir(R);q=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True);q.check_returncode();print(q.stdout)
