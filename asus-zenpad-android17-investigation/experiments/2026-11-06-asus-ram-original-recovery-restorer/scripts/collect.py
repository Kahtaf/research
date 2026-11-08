from pathlib import Path
import io,tarfile,subprocess,shlex
from remote import R,REMOTE,SSH
names=['evidence','source/core_binding.h','source/generated_host_binding.py','tests/probe_binding.h','artifacts/candidate','artifacts/os-rescue','artifacts/p10-restore','artifacts/p10-restore-reproduction','artifacts/legacy-reproduction','artifacts/restore-sepolicy','artifacts/file_contexts.bin','artifacts/core.cpio.gz','artifacts/core-entries.json','artifacts/policy_build','artifacts/policy_audit','artifacts/core_tests','artifacts/session_server','artifacts/rescue-proxy','artifacts/concat-probe']
p=subprocess.run(SSH+['tar -C '+shlex.quote(REMOTE)+' -cf - '+' '.join(map(shlex.quote,names))],capture_output=True,timeout=60)
assert p.returncode==0,p.stderr;assert len(p.stdout)<80*1024*1024
with tarfile.open(fileobj=io.BytesIO(p.stdout)) as t:
 for member in t.getmembers():
  if member.isfile():
   rel=Path(member.name);assert not rel.is_absolute() and '..' not in rel.parts and member.size<20*1024*1024
   out=R/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(t.extractfile(member).read())
print('Collected bounded owned-fixture outputs')
