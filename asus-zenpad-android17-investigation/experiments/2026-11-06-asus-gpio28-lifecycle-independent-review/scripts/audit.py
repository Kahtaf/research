"""Read only selected public inputs; independent lexical extraction and pins."""
import hashlib,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'2026-11-06-asus-gpio28-lifecycle-fix'
REL=Path('sound/soc/mediatek/mt_soc_audio_8163')
H=lambda b:hashlib.sha256(b).hexdigest()

def masked(s):
    return re.sub(r'/\*[\s\S]*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',lambda m: ''.join('\n' if c=='\n' else ' ' for c in m[0]),s)

def functions(s):
    m=masked(s);out={}
    for r in re.finditer(r'(?m)^([A-Za-z_][\w \t*]*?)\b(\w+)\s*\(',m):
        a=r.end();d=1
        while d and a<len(m):d+=(m[a]=='(')-(m[a]==')');a+=1
        while a<len(m) and m[a].isspace():a+=1
        # Sparse lock annotations can occur between a kernel signature and body.
        while re.match(r'__(?:releases|acquires)\s*\(',m[a:]):
            a=m.index('(',a)+1;d=1
            while d:d+=(m[a]=='(')-(m[a]==')');a+=1
            while a<len(m) and m[a].isspace():a+=1
        if a==len(m) or m[a]!='{':continue
        b=a+1;d=1
        while d:d+=(m[b]=='{')-(m[b]=='}');b+=1
        key=r[2] if r[2] not in out else r[2]+'@'+str(s.count('\n',0,r.start())+1)
        out[key]={'text':s[r.start():b]+'\n','body':s[a:b],'start':r.start(),'end':b,'line':s.count('\n',0,r.start())+1,'prefix':r[1]}
    return out

def snapshot():
    paths=[]
    for folder in ('candidate','preimage','inputs/api','baseline/tests','baseline/inputs/api','tests/generated','inputs/prior/tests','inputs/prior/evidence','inputs/review/evidence'):
        paths.extend(p for p in (SOURCE/folder).rglob('*') if p.is_file())
    paths.extend(SOURCE/p for p in ('patches/lifecycle-from-gpio28-candidate.patch','report/HANDOFF.md','evidence/pre-post-pins.json','evidence/input-pins.json','scripts/make_tests.py','scripts/source.py','tests/contract.c','tests/lifecycle.c'))
    # Original inputs referenced by the candidate are public local exact source pins.
    originals=json.loads((SOURCE/'evidence/input-pins.json').read_text())
    for r in originals:
        p=ROOT.parent/r['original']; assert H(p.read_bytes())==r['sha256'],str(p)
        assert H((SOURCE/r['copy']).read_bytes())==r['sha256'],r['copy']
        paths.append(p)
    pins={str(p.relative_to(ROOT.parent)):H(p.read_bytes()) for p in sorted(set(paths))}
    dest=ROOT/'evidence/input-manifest.json'
    if dest.exists():assert json.loads(dest.read_text())==pins,'Input mutation detected'
    else:dest.write_text(json.dumps(pins,indent=2)+'\n')
    return pins

def main():
    pins=snapshot()
    pre=(SOURCE/'preimage'/REL/'mt_soc_codec_63xx.c').read_text();post=(SOURCE/'candidate'/REL/'mt_soc_codec_63xx.c').read_text()
    fs=functions(post);old=functions(pre)
    clean=masked(post)
    references=[]
    for r in re.finditer(r'\bmCodec_data\b',clean):
        owners=[n for n,f in fs.items() if f['start']<=r.start()<f['end']]
        references.append({'line':post.count('\n',0,r.start())+1,'function':owners[0] if owners else 'global declaration'})
    assert sum(r['function']=='global declaration' for r in references)==1
    calls={n:{target for target in fs if target.split('@')[0] in set(re.findall(r'\b(\w+)\s*\(',masked(f['body'])))} for n,f in fs.items()}
    direct={r['function'] for r in references}-{'global declaration'};reach=set(direct)
    while True:
        add={n for n,c in calls.items() if c&reach}-reach
        if not add:break
        reach|=add
    # Derive callbacks from real control arrays, independent of supplied audit list.
    tables=re.findall(r'static const struct snd_kcontrol_new\s+(\w+)\[\]\s*=\s*\{([\s\S]*?)\n\};',post)
    controls=[]
    for table,body in tables:
        for n in sorted(set(re.findall(r'\b[A-Za-z_]\w*\b',masked(body)))&reach):
            wrapped=bool(re.search(r'CODEC_CONTROL\(\s*'+re.escape(n)+r'\s*\)',body))
            assert wrapped,(table,n)
            assert not re.search(r'\b'+re.escape(n)+r'\b',re.sub(r'CODEC_CONTROL\(\s*'+re.escape(n)+r'\s*\)','',body)),('unguarded duplicate',table,n)
            assert len(re.findall(r'CODEC_STATE_CONTROL\('+n+r'\)',post))==1,n
            controls.append({'table':table,'callback':n,'line':fs[n]['line'],'wrapper':wrapped})
    assert len(controls)==46
    boundaries={n:f['line'] for n,f in fs.items() if n in reach and 'static' not in f['prefix'].split()}
    assert set(boundaries)=={'SetAnalogSuspend','OpenAnalogHeadphone','UpdateHeadsetGain','UpdateHeadsetGainLocked'}
    outside=[]
    for r in re.finditer(r'\b(?:'+'|'.join(re.escape(n.split('@')[0]) for n in reach)+r')\b',clean):
        if not any(f['start']<=r.start()<f['end'] for f in fs.values()):
            line=post.count('\n',0,r.start())+1
            outside.append({'line':line,'text':post.splitlines()[line-1].strip()})
    (ROOT/'evidence/private-outside-function-references.json').write_text(json.dumps(outside,indent=2)+'\n')
    preserved=[]
    for n in ('Speaker_Amp_Change','Speaker_Amp_Get','Speaker_Amp_Set','Apply_Speaker_Gain','Audio_Speaker_Class_Set','Audio_Speaker_Class_Get','Audio_Speaker_Pga_Gain_Set','Audio_Speaker_Pga_Gain_Get','Headset_Speaker_Amp_Change'):
        assert old[n]['text']==fs[n]['text'],n
        preserved.append({'function':n,'whole_function_sha256':H(fs[n]['text'].encode())})
    for a,b in [('UpdateHeadsetGain','UpdateHeadsetGain_locked'),('SetMicPGAGain','SetMicPGAGain'),('InitCodecDefault','InitCodecDefault'),('OpenAnalogHeadphone','OpenAnalogHeadphone_locked')]:
        assert old[a]['body']==fs[b]['body'],a
        preserved.append({'pre':a,'post':b,'body_sha256':H(fs[b]['body'].encode())})
    # Validate every supplied extraction using this independent lexical scanner.
    extraction=[]
    for r in json.loads((SOURCE/'evidence/production-extraction.json').read_text()):
        p=SOURCE/r['source']; data=p.read_text()
        b=functions(data)[r['function']]['text'] if 'function' in r else data
        assert H(b.encode())==r['sha256'],r
        extraction.append(r)
    expected_routing='c458de71bb3c2cccd8b0d39a4c7c6e3a75f962cc8bdda44697eacca4f30bbd3a'
    assert H((SOURCE/'candidate'/REL/'mt_soc_pcm_routing.c').read_bytes())==expected_routing
    changes=json.loads((SOURCE/'evidence/pre-post-pins.json').read_text())
    for r in changes:
        assert H((SOURCE/'candidate'/r['path']).read_bytes())==r['post_sha256']
        if r['pre_sha256']:assert H((SOURCE/'preimage'/r['path']).read_bytes())==r['pre_sha256']
        else:assert not (SOURCE/'preimage'/r['path']).exists() and r['destination_must_be_absent']
    changed={r['path'] for r in changes}
    unchanged=[]
    for p in (SOURCE/'preimage').rglob('*'):
        if p.is_file() and str(p.relative_to(SOURCE/'preimage')) not in changed:
            rel=p.relative_to(SOURCE/'preimage');assert p.read_bytes()==(SOURCE/'candidate'/rel).read_bytes(),str(rel)
            unchanged.append({'path':str(rel),'sha256':H(p.read_bytes())})
    report={'inputs':len(pins),'function_count':len(fs),'private_reference_count':len(references),'private_references':references,'private_reachable':sorted(reach),'calls':{n:sorted(c) for n,c in calls.items()},'private_external_boundaries':boundaries,'actual_private_control_registrations':controls,'preserved_bodies':preserved,'validated_production_extractions':extraction,'five_path_pins':changes,'unchanged_files':unchanged,'patch_sha256':H((SOURCE/'patches/lifecycle-from-gpio28-candidate.patch').read_bytes())}
    (ROOT/'evidence/source-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(pins),'pins;',len(references),'private references;',len(controls),'actual registrations;',len(extraction),'independently verified extracts')

if __name__=='__main__':main()
