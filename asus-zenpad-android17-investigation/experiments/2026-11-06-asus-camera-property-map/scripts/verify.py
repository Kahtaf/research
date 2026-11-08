from pathlib import Path
import json,hashlib,re,ast
r=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pre=json.loads((r/'evidence/local-inputs-pre.json').read_text());post=[]
for x in pre:
 p=r.parent/x['path'];got={'path':x['path'],'bytes':p.stat().st_size,'sha256':sha(p)};assert got==x,p;post.append(got)
(r/'evidence/local-inputs-post.json').write_text(json.dumps(post,indent=2)+'\n')
assert json.loads((r/'evidence/input-pins.json').read_text())==json.loads((r/'evidence/input-pins-post.json').read_text())
for file,prefix in [('donor-pins.json','donor'),('support-pins.json','donor'),('uapi-pins.json','supplement')]:
 for x in json.loads((r/'evidence'/file).read_text()):
  rel=x['path'];p=r/rel if rel.startswith('backend/') else r/prefix/rel
  assert sha(p)==x['sha256'],p
for arch,size,offsets in [('arm',20,[4,8,12,16]),('arm64',40,[8,16,24,32])]:
 for fn,subject in [('layouts.txt','AsusPropMap'),('donor-layouts.txt','PropertyMap')]:
  s=(r/'artifacts'/arch/fn).read_text();b=next(b for b in s.split('*** Dumping AST Record Layout') if 'class android::'+subject+'\n' in b).split('*** Dumping IRgen')[0]
  assert f'[sizeof={size},' in b
  for field,off in zip(['mStorage','mCount','mFlags','mItemSize'],offsets):assert re.search(r'^\s*'+str(off)+r'\s*\|[^\n]*\b'+field+r'\b',b,re.M),(arch,field)
  v=s[s.index("Vtable for 'android::SortedVector'"):];assert '(11 entries)' in v
  names=['do_construct','do_destroy','do_copy','do_splat','do_move_forward','do_move_backward','do_compare'];assert [v.index(n) for n in names]==sorted(v.index(n) for n in names)
host=json.loads((r/'evidence/host-commands.json').read_text());assert all(x['rc']==0 for x in host)
assert 'src/legacy_property_map.cpp' in ' '.join(host[1]['argv'])
assert 'PASS 64518 checks' in host[-1]['stdout'] and 'allocated=3414 freed=3413 live=1' in host[-1]['stdout']
assert not re.search('runtime error:',host[-1]['stderr'])
b=json.loads((r/'evidence/binding.json').read_text());assert b['pre_sha256']==b['post_original_sha256'];assert len(b['mapping'])==9
for p in (r/'scripts').glob('*.py'):ast.parse(p.read_text())
# All file links in the report are present. Primary upstream links are externally pinned.
for dest in re.findall(r'\]\(([^)]+)\)',(r/'report/PROPERTY-MAP.md').read_text()):
 if not dest.startswith('http') and dest!='../evidence/verification.json':assert (r/'report'/dest).exists(),dest
budget=json.loads((r/'evidence/remote-budget.json').read_text());assert budget['scratch_bytes']<budget['limit_bytes']
result={'status':'PASS','unchanged_original_local_files':len(pre),'unchanged_remote_selected_compiler_inputs':len(json.loads((r/'evidence/input-pins.json').read_text())),'donor_transitive_inputs':len(json.loads((r/'evidence/supplement-input-pins.json').read_text())),'target_adapter_compile_link':['ARM32 --no-undefined','ARM64 --no-undefined'],'donor_layouts':'20/40 bytes unchanged donor matches private adapter','host_behavior':'production adapter, UBSan, ownership baseline and canaries pass','binding':'nine renamed ARM32 imports + explicit needed, originals preserved','runtime_qualified':False,'runtime_limits':['No Android execution','Missing libbase.so/libvndksupport.so/ld-android.so snapshots','No OEM ARM64 constructor/vtable or importer rewrite','Host m32 toolchain headers absent'],'no_camera_compatibility_claim':True}
(r/'evidence/verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
