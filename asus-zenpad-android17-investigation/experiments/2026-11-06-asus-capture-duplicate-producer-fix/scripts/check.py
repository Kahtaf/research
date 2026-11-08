"""Exercise real graph indexing/selection with tiny duplicate-producer graphs."""
from pathlib import Path
import importlib.util
import json
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT.parent/'2026-11-06-asus-official-runtime-capture-v5'
sys.path.insert(0,str(ORIGINAL/'source'))
from safeio import Tree, Refusal
spec=importlib.util.spec_from_file_location('candidate_graph',Path(sys.argv[1]));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cp='rule cp\n  command = cp $in $out\n'
cases=[('unique',cp+'build out/a: cp src/a\n',{},True),
       ('same-file identical duplicate',cp+'build out/a: cp src/a\nbuild out/a: cp src/a\n',{},False),
       ('different-scope identical duplicate',cp+'build out/a: cp src/a\nsubninja out/child.ninja\n',{'child.ninja':'rule cp\n  command = arbitrary-generator $in $out\nbuild out/a: cp src/a\n'},False),
       ('different raw duplicate',cp+'build out/a: cp src/a\nbuild out/a: cp src/b\n',{},False)]
rows=[]
for name,text,extras,expected in cases:
    with tempfile.TemporaryDirectory(dir=ROOT/'evidence') as tmp:
        root=Path(tmp);(root/'out').mkdir();(root/'out/main.ninja').write_text(text)
        for rel,data in extras.items():(root/'out'/rel).write_text(data)
        limits=json.loads((ORIGINAL/'inputs/profile-r8.json').read_text())['limits']
        limits.update(graph_file_bytes=1024**2,graph_total_bytes=4*1024**2,index_bytes=8*1024**2)
        tree=Tree(root);graph=None
        try:
            graph=m.Graph(tree,['out/main.ninja']+['out/'+p for p in extras],root/'index.sqlite',limits)
            graph.edge('out/a');accepted=True
        except Refusal:accepted=False
        finally:
            if graph is not None:graph.close()
            tree.close()
        rows.append({'case':name,'accepted':accepted,'expected':expected,'pass':accepted==expected})
print(json.dumps({'cases':rows,'all_pass':all(r['pass'] for r in rows),'scope':'real tiny graph index only; other v5 parser findings remain open'},indent=2))
raise SystemExit(0 if all(r['pass'] for r in rows) else 1)
