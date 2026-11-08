"""Offline, nonroot local Linux fixture; mounts only this owned spike.
No image build, network, device, credential, active source or remote access.
"""
from pathlib import Path
import json,subprocess
R=Path(__file__).resolve().parents[1]
image='sha256:98529c9b6853' # resolve local image to its full immutable ID
q=subprocess.run(['docker','--context','orbstack','image','inspect','98529c9b6853','--format','{{.Id}}'],capture_output=True,text=True,check=True)
image=q.stdout.strip();assert image.startswith('sha256:98529c9b6853')
cmd=['docker','--context','orbstack','run','--rm','--pull','never','--network','none','--read-only','--user','501:20','--cpuset-cpus','0','--cpus','1','--memory','1g','--memory-swap','1g','--pids-limit','32','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,size=64m','-v',f'{R}:/work','-w','/work',image,'sh','tests/run_linux.sh']
(R/'evidence/local-container-command.json').write_text(json.dumps(dict(argv=cmd,image=image,scope='local existing public audit tool image; only this spike mounted'),indent=2)+'\n')
with (R/'evidence/final-linux.stdout').open('w') as out,(R/'evidence/final-linux.stderr').open('w') as err:
 q=subprocess.run(cmd,stdout=out,stderr=err)
(R/'evidence/final-linux.exit').write_text(str(q.returncode)+'\n')
raise SystemExit(q.returncode)
