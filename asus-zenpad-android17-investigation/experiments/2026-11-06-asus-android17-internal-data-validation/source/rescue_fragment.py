"""Read-only adapter for the prior reference controller's 1 MiB framing.
The authoritative requested manifest remains 32 MiB. This fragment contains no
approval, device identity, backup receipt or fabricated runtime gates.
"""
from image import *
p=R/'artifacts/A17DATA-pristine.raw';safe(p);m=json.loads((R/'evidence/image-manifest.json').read_text());h=hashlib.sha256();chunks=[];groups=[];group=hashlib.sha256();pos=0
with p.open('rb') as f:
 while pos<SIZE:
  b=f.read(min(1024*1024,SIZE-pos));need(bool(b),'short read');h.update(b);group.update(b);chunks.append(hashlib.sha256(b).hexdigest());pos+=len(b)
  if pos%CHUNK==0 or pos==SIZE:groups.append(group.hexdigest());group=hashlib.sha256()
 need(not f.read(1),'long image')
need(h.hexdigest()==m['sha256'],'full hash mismatch');need(groups==[c['sha256'] for c in m['chunks']],'32MiB group mismatch')
out=R/'evidence/fresh_userdata.reference-1MiB.json'
with out.open('x') as f:json.dump(dict(bytes=SIZE,sha256=h.hexdigest(),chunks=chunks),f,indent=2);f.write('\n')
print(json.dumps(dict(path=str(out),bytes=SIZE,chunk_bytes=1024*1024,count=len(chunks),sha256=h.hexdigest(),fragment_sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
