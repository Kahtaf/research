from pathlib import Path
import base64,json,hashlib
r=Path(__file__).resolve().parents[1];p=r/'evidence/artifact-transfer.json';rows=json.loads(p.read_text())
for row in rows:
 d=base64.b64decode(row.pop('base64'));assert hashlib.sha256(d).hexdigest()==row['sha256'];assert len(d)==row['bytes']
 dest=r/'fixture'/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(d);row['local']=str(dest.relative_to(r))
(r/'evidence/artifact-pins.json').write_text(json.dumps(rows,indent=2)+'\n');p.unlink()
for name in ['input-pins.json','compile.json']:(r/'evidence'/name).write_bytes((r/'fixture/abi-out'/name).read_bytes())
print('verified and unpacked',len(rows),'artifacts')
