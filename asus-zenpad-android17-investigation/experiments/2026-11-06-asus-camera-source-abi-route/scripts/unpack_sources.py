from pathlib import Path
import json,hashlib,sys
r=Path(__file__).resolve().parents[1];pins=[]
for row in json.loads(Path(sys.argv[1]).read_text()):
 if row.get('missing'):print('Absent:',row['path']);continue
 data=row.pop('text').encode();assert hashlib.sha256(data).hexdigest()==row['sha256']
 p=r/'fixture/sdk37'/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);pins.append(row)
Path(sys.argv[2]).write_text(json.dumps(pins,indent=2)+'\n')
