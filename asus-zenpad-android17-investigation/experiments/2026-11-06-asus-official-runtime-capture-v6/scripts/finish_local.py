"""Prepare static review material and verify unchanged local ancestor pins."""
import difflib,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];V=R.parent/'2026-11-06-asus-official-runtime-capture-v5';E=R/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):
 p=R/n;p.write_text(json.dumps(v,indent=2)+'\n')
v5pins=json.loads((V/'tool-pins.json').read_bytes());assert all(sha(V/n)==h for n,h in v5pins.items())
review=R.parent/'2026-11-06-asus-coherent-capture-v5-review'
assert sha(review/'REPORT.md')==sha(R/'inputs/review/REPORT.md')
assert sha(review/'findings.json')==sha(R/'inputs/review/findings.json')
changed=[n for n in sorted(v5pins) if (R/n).is_file() and sha(R/n)!=v5pins[n]]
protected=[str(p.relative_to(R)) for p in (R/'source').glob('*.py') if p.name not in ('ninja.py','graph.py','capture.py')]
protected+=['inputs/'+n for n in ('selector.json','profile-r8.json','provenance-contract.json','fixed-r8-metadata.json','host-metadata-resolver-reference.json','qualified-host-metadata-tools.json','public-source-evidence.json','public-source-paths.json')]
protected+=['manifest.schema.json','host-metadata-source-plan.schema.json','METADATA-SOURCE-CONTRACT.md','tests/test_capture.py','tests/test_provenance.py','tests/test_metadata_roles.py']
assert all(sha(R/n)==sha(V/n) for n in protected)
assert sha(R/'source/graph.py')==json.loads((R/'inputs/parent-duplicate/source-pins.json').read_bytes())['postimage_sha256']
write('evidence/static-preservation.json',{'v5_tool_seal_sha256':sha(V/'tool-pins.json'),'v5_all_pinned_local_bytes_unchanged':True,'review_local_report_findings_unchanged':True,'remote_ancestor_accessed':False,'protected_byte_identical':{n:sha(R/n) for n in protected},'changed_shared_files':changed})
diff=''.join(''.join(difflib.unified_diff((V/'source'/n).read_text().splitlines(True),(R/'source'/n).read_text().splitlines(True),fromfile='v5/source/'+n,tofile='v6/source/'+n)) for n in ('capture.py','graph.py','ninja.py'))
(R/'minimal-v5-v6.patch').write_text(diff)
commit=json.loads((R/'inputs/ninja-1.12.1-pins.json').read_bytes())['commit']
write('inputs/ninja-semantics.json',{'upstream_version':'1.12.1','upstream_commit':commit,'pinned_sources':'inputs/ninja-1.12.1-pins.json','semantics':[
'ParseEdge creates a child BindingEnv iff actual local bindings occur; a defined-empty local binding counts. Comments alone do not create one.',
'EdgeEnv builtins in/in_newline/out precede BindingEnv::LookupWithFallback. Own binding presence, including empty, precedes rule EvalString; absent own then rule then parent LookupVariable.',
'No build-local environment: current file lexical environment is the own environment. A subninja parent is enclosing, not own. Include shares the current environment.',
'File/build values are eager and never rescanned. Build locals evaluate against the enclosing file environment, not sibling local bindings. Rule fields are lazy with bounded cycle checking.',
'Commands consult the final lexical file environment. ParseEdge resolves unescaped effective dyndep at the edge parse cutoff; any nonempty result refuses without opening a payload.',
'Undefined optional variables are empty; defined-empty still shadows. $$ produces one literal dollar; malformed escapes and cycles refuse.'
],'limitations':['No native engine or dynamic-dependency payload implementation. Nonempty effective dyndep is GRAPH_DYNDEP.','Repeated inclusion and variable-expanded indexed output names retain prior explicit refusals. No whole-graph Ninja validity claim.','This is source-pinned fixture qualification; no active real graph, output or engine was inspected.']})
print(json.dumps({'protected_files':len(protected),'production_delta_files':3,'diff_bytes':len(diff.encode())}))
