"""Independent bounded integrity and exact-delta verification, no transports."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import resource
import signal

resource.setrlimit(resource.RLIMIT_CPU,(15,15));signal.alarm(30)
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent
SUBJECT=WORK/'2026-11-06-asus-full-install-host-lifecycle-fix'
PRIOR=WORK/'2026-11-06-asus-full-install-bounded-host-io'
OLD_REVIEW=WORK/'2026-11-06-asus-full-install-bounded-host-io-review'

def digest(p):
    assert p.is_file() and not p.is_symlink() and p.stat().st_size<16*1024**2,str(p)
    return hashlib.sha256(p.read_bytes()).hexdigest()
def emit(n,v):(ROOT/'evidence'/n).write_text(json.dumps(v,indent=2)+'\n')
def definitions(p):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def assigned(p,name):
    for n in ast.parse(p.read_text()).body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets):return ast.dump(n.value,include_attributes=False)
    raise AssertionError(name)

before=json.loads((ROOT/'evidence/inputs-before.json').read_text())
after={p:digest(WORK/p) for p in before}
assert before==after,'prior input drift'
emit('inputs-after.json',after)
checks={}
for pinfile,base in [('code-pins.json',SUBJECT),('review-packet-pins.json',SUBJECT),('input-pins.json',WORK)]:
    mapping=json.loads((SUBJECT/'evidence'/pinfile).read_text())
    assert all(digest(base/p)==h for p,h in mapping.items()),pinfile
    checks[pinfile]=len(mapping)
checks['tracked_inputs_unchanged']=len(before)
# Verify unchanged local copies, even after running their suites.
copied=[]
for directory in ('source','profiles','tests'):
    for p in sorted((SUBJECT/directory).rglob('*')):
        if p.is_file():
            assert digest(ROOT/p.relative_to(SUBJECT))==digest(p)
            copied.append(str(p.relative_to(SUBJECT)))
for n in ('adversarial.py','readback_peer.py','regressions.py'):
    assert digest(ROOT/'review'/n)==digest(SUBJECT/'review'/n)
    copied.append('review/'+n)
checks['byte_exact_copies']=copied
runtime=[];verification=[];changed=[]
for p in sorted((SUBJECT/'source').rglob('*.py')):
    rel=p.relative_to(SUBJECT);old=PRIOR/rel
    aa=old.read_text().splitlines(True);bb=p.read_text().splitlines(True)
    if aa==bb:continue
    delta=list(difflib.unified_diff(aa,bb,fromfile='a/'+str(rel),tofile='b/'+str(rel)))
    (verification if p.name=='verify_handoff.py' else runtime).extend(delta)
    changed.append(dict(path=str(rel),before_sha256=digest(old),after_sha256=digest(p),
        added_lines=sum(x.startswith('+') and not x.startswith('+++') for x in delta),
        deleted_lines=sum(x.startswith('-') and not x.startswith('---') for x in delta)))
assert ''.join(runtime)==(SUBJECT/'evidence/host-lifecycle.patch').read_text()
assert ''.join(verification)==(SUBJECT/'evidence/verification.patch').read_text()
assert changed==json.loads((SUBJECT/'evidence/changed-code-pins.json').read_text())
(ROOT/'evidence/reconstructed-host-lifecycle.patch').write_text(''.join(runtime))
(ROOT/'evidence/reconstructed-verification.patch').write_text(''.join(verification))
checks['exact_runtime_diff']=True;checks['exact_verification_diff']=True
checks['runtime_diff_sha256']=digest(SUBJECT/'evidence/host-lifecycle.patch')
checks['subject_code_manifest_sha256']=digest(SUBJECT/'evidence/code-pins.json')
old=definitions(SUBJECT/'source/original/client.py');new=definitions(SUBJECT/'source/bounded_client.py')
assert all(old[n]==new[n] for n in ('parse','status','reconcile'))
checks['parse_status_reconcile_inverse_ast_unchanged']=True
for name in ('worker.py','pinned.py','local_pipe_worker.py','original/client.py','original/manifest.py'):
    assert digest(SUBJECT/'source'/name)==digest(PRIOR/'source'/name)
for file,name in [('sources.py','LOCAL_PROFILES'),('worker.py','FIXED_PROFILES')]:
    assert assigned(SUBJECT/'source'/file,name)==assigned(PRIOR/'source'/file,name)
assert definitions(SUBJECT/'source/sources.py')['ssh_command']==definitions(PRIOR/'source/sources.py')['ssh_command']
checks['fixed_profiles_workers_and_source_command_unchanged']=True
for p in (SUBJECT/'profiles').iterdir():assert digest(p)==digest(PRIOR/'profiles'/p.name)
for p in (SUBJECT/'tests').glob('*.py'):assert digest(p)==digest(PRIOR/'tests'/p.name)
for name in ('adversarial.py','readback_peer.py'):assert digest(SUBJECT/'review'/name)==digest(OLD_REVIEW/'review'/name)
rescue=WORK/'2026-11-06-asus-android17-target-rescue/source'
external=json.loads((SUBJECT/'profiles/original-source-pins.json').read_text())
assert all(digest(rescue/p)==h for p,h in external.items())
checks['external_rescue_source_pins']=external
fix=WORK/'2026-11-06-asus-install-contract-boolean-fix'
pins=json.loads((fix/'source-pins.json').read_text());oldtext=(WORK/pins['original']).read_text()
oldguard="contract['mode']!='PARENT_APPROVED' or not contract['armed']"
newguard="contract['mode']!='PARENT_APPROVED' or contract['armed'] is not True"
assert oldtext.count(oldguard)==1
strict=oldtext.replace(oldguard,newguard)
assert hashlib.sha256(oldtext.encode()).hexdigest()==pins['before_sha256']
assert hashlib.sha256(strict.encode()).hexdigest()==pins['after_sha256']
delta=''.join(difflib.unified_diff(oldtext.splitlines(True),strict.splitlines(True),fromfile='a/source/parent_remote.py',tofile='b/source/parent_remote.py'))
assert delta==(fix/'strict-armed.patch').read_text()==(SUBJECT/'evidence/strict-armed.patch').read_text()
def guard_code(text):
    tree=ast.parse(text)
    nodes=[n for n in ast.walk(tree) if isinstance(n,ast.If) and any(isinstance(c,ast.Constant) and c.value=='armed' for c in ast.walk(n.test))]
    assert len(nodes)==1
    return nodes[0],compile(ast.fix_missing_locations(ast.Module(body=[nodes[0]],type_ignores=[])),'actual-guard','exec')
g,code=guard_code((SUBJECT/'source/parent_remote.py').read_text());gg,_=guard_code(strict)
assert ast.dump(g,include_attributes=False)==ast.dump(gg,include_attributes=False)
rows=[]
for value in (True,False,'false','true',1,0,None,[],{},[1]):
    try:exec(code,{'contract':{'mode':'PARENT_APPROVED','armed':value}});accepted=True
    except ValueError:accepted=False
    assert accepted==(value is True)
    rows.append(dict(value=value,type=type(value).__name__,accepted=accepted))
checks['strict_boolean']=dict(exact_isolated_patch=True,before_sha256=pins['before_sha256'],strict_only_after_sha256=pins['after_sha256'],guard_ast_exact=True,cases=rows)
# Verify coverage from actual class definitions and final observed case names.
prior_tree=ast.parse((OLD_REVIEW/'review/adversarial.py').read_text())
prior_names={n.name for c in prior_tree.body if isinstance(c,ast.ClassDef) and c.name=='Review' for n in c.body if isinstance(n,ast.FunctionDef) and n.name.startswith('review_')}
reg=json.loads((ROOT/'evidence/regression-results.json').read_text())
observed={r['case'] for r in reg['observations']}
assert prior_names<=observed and len(prior_names)==29
checks['prior_production_reproductions_covered']=sorted(prior_names)
checks['mode']='PLAN_ONLY';checks['hardware_budgets']='explicit UNQUALIFIED caller inputs';checks['physical_flash_go']=False
emit('integrity.json',checks)
code={str(p.relative_to(ROOT)):digest(p) for p in sorted(ROOT.rglob('*.py'))}
emit('review-code-pins.json',code)
print(json.dumps({k:v for k,v in checks.items() if k not in ('byte_exact_copies','strict_boolean','prior_production_reproductions_covered','external_rescue_source_pins')},indent=2))
