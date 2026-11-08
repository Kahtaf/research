import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];W=ROOT.parent
P=W/'2026-11-06-asus-stock-gpio28-source-port';V=W/'2026-11-06-asus-stock-gpio28-independent-review';K=W/'2026-11-05-asus-p00a-power-port/sources/kernel';rows=[]
H=lambda b:hashlib.sha256(b).hexdigest()
def cp(src,dest,expect=None):
 b=src.read_bytes();h=H(b)
 if expect:assert h==expect,(src,h,expect)
 p=ROOT/dest;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);rows.append({'original':str(src.relative_to(W)),'copy':dest,'sha256':h,'bytes':len(b),'expected':expect});return b
for p in (P/'candidate').rglob('*'):
 if p.is_file():
  rel=p.relative_to(P/'candidate');b=cp(p,'preimage/'+str(rel));q=ROOT/'candidate'/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
for rel in ['sound/soc/mediatek/mt_soc_audio_8163/mt_soc_pcm_routing.c','sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.h','sound/soc/mediatek/mt_soc_audio_8163/mt_soc_audio.h']:
 p=K/rel
 if not p.exists():continue
 expect='c458de71bb3c2cccd8b0d39a4c7c6e3a75f962cc8bdda44697eacca4f30bbd3a' if rel.endswith('routing.c') else None
 b=cp(p,'preimage/'+rel,expect);q=ROOT/'candidate'/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
for p in (P/'inputs/api').rglob('*'):
 if p.is_file():cp(p,'inputs/api/'+str(p.relative_to(P/'inputs/api')))
for rel in ['report/HANDOFF.md','evidence/bind-exact-routing.json','evidence/routing-repro-extraction.json','remote/evidence/lifetime-routing-pm-run.log','remote/evidence/lifetime-null-run.log','remote/evidence/lifetime-stale-suspend-run.log','remote/evidence/mtk-boundary-run.log']:
 cp(V/rel,'inputs/review/'+rel)
for name in ['contract.c','adversarial.c','lifetime-null.c','lifetime-routing-pm.c','lifetime-stale-suspend.c','mtk-boundary.c']:
 cp(V/'inputs/tests'/name,'baseline/tests/'+name)
for p in (V/'inputs/tests/generated').glob('*'):
 if p.is_file():cp(p,'baseline/tests/generated/'+p.name)
for p in (P/'inputs/api').rglob('*'):
 if p.is_file():q=ROOT/'baseline/inputs/api'/p.relative_to(P/'inputs/api');q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
for rel in ['tests/contract.c','scripts/extract_tests.py','scripts/bounded.py','evidence/internal-functions-unchanged.json','evidence/pre-post-pins.json','evidence/config-deltas.json','evidence/HAL-unchanged.json']:
 cp(P/rel,'inputs/prior/'+rel)
# The public header and selected GPIO/routing consumer search, no excluded patch paths.
(ROOT/'evidence/input-pins.json').write_text(json.dumps(rows,indent=2)+'\n');print(len(rows),'pinned public input files')
