"""Extract only public service/property/file label tables from verified stock BOOT."""
from pathlib import Path
import sys,struct,hashlib,json
S=Path(__file__).resolve().parents[1];W=S.parent
sys.path.insert(0,str(W/'2026-11-06-asus-stock-userdata-recovery/source'))
from bootformat_reference import parse_cpio,ungzip,align
p=W/'2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/boot.img';b=p.read_bytes();pin=hashlib.sha256(b).hexdigest();assert pin=='7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'
ks,_,rs,_,ss,_,_,page=struct.unpack_from('<8I',b,8);assert page==2048 and ss==0
r=b[page+align(ks):page+align(ks)+rs];assert r[:4]==bytes.fromhex('88168858')
entries=parse_cpio(ungzip(r[512:])[0]);out=[]
for name in ['service_contexts','property_contexts','file_contexts.bin']:
 data=entries[name][3];dst='inputs/boot__'+name;(S/dst).write_bytes(data);out.append(dict(file=dst,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),source=str(p)+'#'+name))
(S/'evidence/boot-label-pins.json').write_text(json.dumps(dict(boot_sha256=pin,files=out),indent=2)+'\n')
print((S/'inputs/boot__service_contexts').read_text().split('recovery')[1][:100]);print((S/'inputs/boot__file_contexts.bin').read_bytes()[:80].hex())
