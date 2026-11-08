import json,re,shutil
from audit import ROOT,SOURCE,REL,H,functions

def copy_file(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)

for name in ('contract.c','lifecycle.c'):
    copy_file(SOURCE/'tests'/name,ROOT/'tests'/name)
for p in (SOURCE/'tests/generated').glob('*.inc'):copy_file(p,ROOT/'tests/generated'/p.name)
copy_file(SOURCE/'inputs/api/mt_soc_analog_type.h',ROOT/'inputs/api/mt_soc_analog_type.h')
for p in (SOURCE/'baseline/tests').rglob('*'):
    if p.is_file():copy_file(p,ROOT/'work/old/tests'/p.relative_to(SOURCE/'baseline/tests'))
copy_file(SOURCE/'inputs/api/mt_soc_analog_type.h',ROOT/'work/old/inputs/api/mt_soc_analog_type.h')

api={}
for p in (SOURCE/'inputs/api').rglob('*'):
    if p.suffix in ('.c','.h'):
        for n,f in functions(p.read_text()).items():api.setdefault(n,[]).append((p,f))
evidence=[]
for folder,production in [(ROOT/'tests/generated',SOURCE/'candidate'),(ROOT/'work/old/tests/generated',SOURCE/'preimage')]:
    codec=functions((production/REL/'mt_soc_codec_63xx.c').read_text())
    gpio=functions((production/REL/'AudDrv_Gpio.c').read_text())
    for filename,registry in [('actual-codec-bodies.inc',{n:[(production/REL/'mt_soc_codec_63xx.c',f)] for n,f in codec.items()}),('actual-gpio-bodies.inc',{n:[(production/REL/'AudDrv_Gpio.c',f)] for n,f in gpio.items()}),('actual-gpio24-backend.inc',{n:[(production/REL/'AudDrv_Gpio.c',f)] for n,f in gpio.items()}),('actual-api-bodies.inc',api)]:
        p=folder/filename
        if not p.exists():continue
        text=p.read_text();edits=[]
        for n,f in functions(text).items():
            candidates=registry.get(n,[])
            matches=[(origin,actual) for origin,actual in candidates if actual['text']==f['text']]
            assert matches,(str(p),n)
            origin,actual=matches[0]
            edits.append((f['start'],f['end'],actual['text'].rstrip('\n')))
            evidence.append({'fixture':str(p.relative_to(ROOT)),'function':n,'source':str(origin.relative_to(ROOT.parent)),'line':actual['line'],'sha256':H(actual['text'].encode())})
        for a,b,replacement in sorted(edits,reverse=True):text=text[:a]+replacement+text[b:]
        assert text==p.read_text()
        p.write_text(text)
    gate=folder/('p00a_stock_gate.inc' if production.name=='candidate' else 'actual-gate.inc')
    actual=(production/REL/'p00a_stock_gate.h').read_text()
    stripped='\n'.join(l for l in actual.splitlines() if not l.startswith('#include '))+'\n'
    assert gate.read_text()==stripped
    gate.write_text(stripped)

# Routing old fixture embeds the exact PM and AFE functions directly.
routing=functions((SOURCE/'preimage'/REL/'mt_soc_pcm_routing.c').read_text())
old=functions((ROOT/'work/old/tests/lifetime-routing-pm.c').read_text())
for n,actual in [('mtk_routing_pm_ops_suspend',routing['mtk_routing_pm_ops_suspend']),('ConditionEnterSuspend',api['ConditionEnterSuspend'][0][1])]:
    assert old[n]['text']==actual['text'],n
    evidence.append({'fixture':'work/old/tests/lifetime-routing-pm.c','function':n,'sha256':H(actual['text'].encode())})

# Rebuild selected current PM include directly from the independently scanned sources.
parts=[api['ConditionEnterSuspend'][0][1]['text'],routing['mtk_routing_pm_ops_suspend']['text'],routing['mtk_routing_pm_ops_resume']['text']]
assert (ROOT/'tests/generated/actual-routing-pm.inc').read_text()=='\n'.join(parts)
(ROOT/'tests/generated/actual-routing-pm.inc').write_text('\n'.join(parts))
(ROOT/'evidence/fixture-source-binding.json').write_text(json.dumps(evidence,indent=2)+'\n')
print('PASS independent production binding/re-extraction:',len(evidence),'functions; baseline and current gate headers')
