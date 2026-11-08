"""Read only this sealed preparation; caller must authenticate the delivered seal."""
import hashlib,json,os,resource
from pathlib import Path
R=Path(__file__).resolve().parents[1]
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
def sha(p):
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<=48*1024**2
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
marker=json.loads((R/'FINALIZED.json').read_bytes());assert sha(R/'tool-pins.json')==marker['tool_seal_sha256'];assert sha(R/'HANDOFF.json')==marker['handoff_sha256']
pins=json.loads((R/'tool-pins.json').read_bytes());assert len(pins)<=256
size=0
for n,h in pins.items():
 assert not Path(n).is_absolute() and '..' not in Path(n).parts
 p=R/n;assert p.resolve().is_relative_to(R);size+=p.stat().st_size;assert size<=128*1024**2;assert sha(p)==h,n
print(json.dumps({'status':'SEALED_BYTES_MATCH','tool_seal_sha256':marker['tool_seal_sha256'],'files':len(pins),'pinned_bytes':size,'fixture_qualification_only':True,'independent_review':'pending'}))
