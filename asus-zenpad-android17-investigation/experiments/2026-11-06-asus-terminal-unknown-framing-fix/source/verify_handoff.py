"""Offline small-code/profile integrity; never opens images or starts transport."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    original=ROOT.parent/'2026-11-06-asus-full-install-bounded-host-io'
    inputs=json.loads((ROOT/'evidence/input-pins.json').read_text())
    for path,pin in inputs.items():
        if digest(ROOT.parent/path)!=pin:raise ValueError('preserved original/review input changed: '+path)
    code=json.loads((ROOT/'evidence/code-pins.json').read_text())
    for relative,pin in code.items():
        path=ROOT/relative
        if not path.resolve().is_relative_to(ROOT):raise ValueError('code pin outside spike')
        if digest(path)!=pin:raise ValueError('new code changed: '+relative)
        compile(path.read_bytes(),str(path),'exec')
    immutable=['worker.py','pinned.py','local_pipe_worker.py','original/client.py','original/manifest.py']
    for name in immutable:
        if digest(ROOT/'source'/name)!=digest(original/'source'/name):raise ValueError('immutable source changed: '+name)
    for path in (ROOT/'profiles').iterdir():
        if digest(path)!=digest(original/'profiles'/path.name):raise ValueError('fixed profile/chunk export changed')
    for path in (ROOT/'tests').glob('*.py'):
        if digest(path)!=digest(original/'tests'/path.name):raise ValueError('original suite changed')
    review=ROOT.parent/'2026-11-06-asus-full-install-bounded-host-io-review'
    for name in ('adversarial.py','readback_peer.py'):
        if digest(ROOT/'review'/name)!=digest(review/'review'/name):raise ValueError('original reproduction changed')
    def definitions(path):
        return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body
                if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    before=definitions(ROOT/'source/original/client.py');after=definitions(ROOT/'source/bounded_client.py')
    for name in ('parse','status','reconcile'):
        if before[name]!=after[name]:raise ValueError('parser/sequence/inverse changed: '+name)
    def assignment(path,name):
        for node in ast.parse(path.read_text()).body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
                return ast.dump(node.value,include_attributes=False)
        raise ValueError('assignment missing')
    for file,name in [('sources.py','LOCAL_PROFILES'),('worker.py','FIXED_PROFILES')]:
        if assignment(ROOT/'source'/file,name)!=assignment(original/'source'/file,name):raise ValueError('fixed source admission changed')
    if definitions(ROOT/'source/sources.py')['ssh_command']!=definitions(original/'source/sources.py')['ssh_command']:
        raise ValueError('fixed source command changed')
    rescue=ROOT.parent/'2026-11-06-asus-android17-target-rescue/source'
    for name,pin in json.loads((ROOT/'profiles/original-source-pins.json').read_text()).items():
        if digest(rescue/name)!=pin:raise ValueError('external rescue source pin changed')
    import pinned
    return dict(original_implementation_and_review_unchanged=True,original_suite_and_reproductions_unchanged=True,
                new_code_pins_verified=True,immutable_source_copies=immutable,
                fixed_profiles_and_chunk_exports_unchanged=True,original_parser_reconciliation_inverse_ast_unchanged=True,
                original_external_source_pins_verified=True,mode='PLAN_ONLY',hardware_budgets='UNQUALIFIED',
                unknown_install_profiles='UNBOUND_REFUSED',physical_flash_go=False)


if __name__=='__main__':print(json.dumps(verify(),indent=2))
