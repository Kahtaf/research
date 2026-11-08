from pathlib import Path
import subprocess,tarfile,io
s=Path(__file__).resolve().parents[1]
args=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o',f'UserKnownHostsFile={Path.home()}/.ssh/google_compute_known_hosts','android@IP_REDACTED','tar -czf - -C /srv/android/asus-minimal-audio-hal-20261106 out/compile.json out/link-inputs.json out/audio.primary.mt8163.so out/libtinyalsav2.so out/audio.primary.mt8163.so.elf.txt out/libtinyalsav2.so.elf.txt out/public-dc-disassembly.txt out/validation.json out/assembled-audio.xml out/compile-input-pins.json out/hal-test.json out/public-primary-dc.txt']
r=subprocess.run(args,capture_output=True,check=True)
with tarfile.open(fileobj=io.BytesIO(r.stdout),mode='r:gz') as t:
 for m in t:
  if m.isfile():
   p=s/'evidence/remote'/Path(m.name).name;p.parent.mkdir(exist_ok=True);p.write_bytes(t.extractfile(m).read())
print('Downloaded',len(r.stdout),'public evidence bytes')
