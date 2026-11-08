from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
rows={}
for rev,src in [('before','baseline'),('after','source')]:
 p=R/src/'rescue.c';raw=p.read_bytes();first,body=raw.split(b'\n',1);assert first==b'#include "common.h"'
 out=R/f'tests/generated/{rev}.c';out.parent.mkdir(exist_ok=True);out.write_bytes(body)
 assert out.read_bytes()==p.read_bytes().split(b'\n',1)[1]
 rows[rev]=dict(original_sha256=hashlib.sha256(raw).hexdigest(),body_sha256=hashlib.sha256(body).hexdigest(),only_removed_line=first.decode())
(R/'evidence/model-body-receipts.json').write_text(json.dumps(rows,indent=2)+'\n')
