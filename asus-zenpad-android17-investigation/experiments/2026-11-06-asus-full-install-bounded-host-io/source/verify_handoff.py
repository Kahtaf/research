"""Offline pins/invariant verification; reads only small source/profile/evidence files."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    inputs=json.loads((ROOT/'evidence/input-pins.json').read_text())
    for path,pin in inputs.items():
        if digest(ROOT.parent/path)!=pin:raise ValueError('original input changed: '+path)
    code=json.loads((ROOT/'evidence/code-pins.json').read_text())
    for path,pin in code.items():
        target=ROOT/path
        if not target.resolve().is_relative_to(ROOT):raise ValueError('new pin outside spike')
        if digest(target)!=pin:raise ValueError('new code pin changed: '+path)
        compile(target.read_bytes(),str(target),'exec')
    # Preserve the original verifier's external rescue source-pin binding.
    rescue=ROOT.parent/'2026-11-06-asus-android17-target-rescue/source'
    upstream=json.loads((ROOT/'profiles/original-source-pins.json').read_text())
    for name,pin in upstream.items():
        if digest(rescue/name)!=pin:raise ValueError('original rescue source changed: '+name)
    original=ROOT.parent/'2026-11-06-asus-rescue-remote-source'
    unchanged=['worker.py','pinned.py','journal.py','original/client.py','original/manifest.py']
    for name in unchanged:
        if digest(ROOT/'source'/name)!=digest(original/'source'/name):raise ValueError('immutable copy changed: '+name)
    for profile in (ROOT/'profiles').iterdir():
        if digest(profile)!=digest(original/'profiles'/profile.name):raise ValueError('profile changed')
    def definitions(path):
        return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(path.read_text()).body
                if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    before=definitions(ROOT/'source/original/client.py')
    after=definitions(ROOT/'source/bounded_client.py')
    for name in ('parse','status','reconcile'):
        if before[name]!=after[name]:raise ValueError('protocol/sequence/selection changed: '+name)
    def assignment(path,name):
        for node in ast.parse(path.read_text()).body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
                return ast.dump(node.value,include_attributes=False)
        raise ValueError('assignment missing')
    for filename,name in [('sources.py','LOCAL_PROFILES'),('worker.py','FIXED_PROFILES')]:
        if assignment(ROOT/'source'/filename,name)!=assignment(original/'source'/filename,name):raise ValueError('fixed admission changed')
    if definitions(ROOT/'source/sources.py')['ssh_command']!=definitions(original/'source/sources.py')['ssh_command']:
        raise ValueError('fixed source command changed')
    # Loading the unmodified pinned module checks its original external source pins.
    import pinned
    result=dict(original_inputs_unchanged=True,immutable_copies_unchanged=unchanged,
                fixed_profiles_and_chunk_exports_unchanged=True,rsc1_selection_and_sequence_ast_unchanged=True,
                new_code_pins_verified=True,original_external_rescue_pins_verified=True,mode='PLAN_ONLY',install_system='UNBOUND_REFUSED',install_boot='UNBOUND_REFUSED')
    return result


if __name__=='__main__':
    print(json.dumps(verify(),indent=2))
