"""Targeted finite-boundary controls for the already-generated joined fixture."""
from pathlib import Path
import json
import decode_delay as d
from symbolize_delay import summary
R=Path(__file__).resolve().parents[1]
data=(R/'evidence/controls/joined.bin').read_bytes();base=data.index(('A49DL2 uuid='+d.UUID).encode());out=d.decode(data);assert out['outcome']=='UNKNOWN_STOP' and out['target']['current_physical_access_observed']
def field(b,off,v):b[off:off+16]=f'{v:016x}'.encode()
def row(tag,f,tail=160):
 b=bytearray(b' '*192);b[:9]=tag;b[-1]=10
 for j,v in enumerate(f):field(b,9+j*17,v)
 field(b,tail,f[0]);return b
b=bytearray(data);field(b,base+64+9+7*17,1)
for j in range(1,4):b[base+1152+j*192:base+1152+(j+1)*192]=row(b'VA49DS   ',[0]*8)
g=d.decode(b);assert g['status']=='FINITE_DELAY_CAPTURE' and g['outcome']=='UNKNOWN_STOP' and not g['target']['current_physical_access_observed']
results={'missing_start':dict(status=g['status'],outcome=g['outcome'],current_physical_access_observed=False),'missing_return':dict(status=out['status'],outcome=out['outcome'])}
b=bytearray(data);field(b,base+64+9+1*17,4);field(b,base+64+9+7*17,79)
f=[out['header']['generation'],6,257,4000,3900,0,4,73];off=base+1152+6*192;b[off:off+192]=row(b'VA49DS   ',f)
g=d.decode(b);assert g['status']=='FINITE_DELAY_CAPTURE' and g['outcome']=='SELECTED_RETURN_OBSERVED_ADC_POST_SEPARATE'
results['return_before_ADC_post']=dict(status=g['status'],outcome=g['outcome'])
public=summary(g);assert public['outcome']==g['outcome'] and public['map_verified'];(R/'evidence/controls/synthetic-symbolized.json').write_text(json.dumps(public,indent=2)+'\n')
for name,index,value in [('wrong_return_generation',0,5),('false_return_condition',3,3999)]:
 bad=bytearray(b);ff=f.copy();ff[index]=value;bad[off:off+192]=row(b'VA49DS   ',ff);got=d.decode(bad);assert got['status']=='UNKNOWN';results[name]=dict(status=got['status'],reason=got['reason'])
receipt=json.loads((R/'evidence/decoder-controls.json').read_text());receipt['finite_boundary_controls']=results;(R/'evidence/decoder-controls.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(results,indent=2))
