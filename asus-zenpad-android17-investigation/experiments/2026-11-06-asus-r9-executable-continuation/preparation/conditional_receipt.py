from pathlib import Path
import base64,json,remote
R=Path(__file__).resolve().parents[1]
files={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for p in [R/'inputs/parent-bpf-changed-output-conditional-acceptance.json',R/'inputs/parent-r8-terminal-review.json']}
s='FILES='+repr(files)+'\n'+r'''
from pathlib import Path
import base64,json,hashlib
R=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
for rel,b in FILES.items():
 p=R/rel
 with p.open('xb') as f:f.write(base64.b64decode(b))
p=R/'inputs/plan.json';plan=json.loads(p.read_text());plan['bpf_runtime_conditional_method']=str(R/'inputs/parent-bpf-changed-output-conditional-acceptance.json');plan['parent_r8_factual_review']=str(R/'inputs/parent-r8-terminal-review.json');p.write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
p=R/'inputs/bpf-classification.json';matrix=json.loads(p.read_text());matrix['runtime_conditional_method_sha256']=hashlib.sha256(Path(plan['bpf_runtime_conditional_method']).read_bytes()).hexdigest();matrix['runtime_accepted']=False;matrix['baseline_scope']='Prior optional-platform-load failures and feature limitations retained; not all-feature readiness'
for row in matrix['rows']:
 row['selected_original_inventory_sha256']=row['qualification_row'].get('sha256')
 row['final_runtime_admitted_sha256']=None
 if row['runtime_requalification_required']:
  row['preparation_candidate_sha256']=row['current_sha256'];row['qualified_sha256']=None
  row['qualification_row_interpretation']='Original selected-output inventory only; no runtime qualification of these changed/new bytes'
  row['historical_runtime_tested_substitution_sha256']='25ccea3b8043240238381ee19d950ebc51629f06688b3a1af9d97e8a6e11ad6f' if row['install_path'].endswith('/netd.o') else None
 else:row['qualification_row_interpretation']='Exact unchanged qualified baseline, retaining prior optional-load failures and feature limitations'
p.write_text(json.dumps(matrix,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(matrix_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),runtime_conditional_method_sha256=matrix['runtime_conditional_method_sha256'],final_runtime_admitted=False)))
'''
r=remote.run(s);(R/'evidence/conditional-receipt-update.json').write_text(r);print(r)
