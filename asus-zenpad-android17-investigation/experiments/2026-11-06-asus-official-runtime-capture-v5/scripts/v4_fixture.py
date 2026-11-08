"""Qualification-only adapter. Production capture never imports/reuses this index."""
import hashlib,json,os,sqlite3,stat
from pathlib import Path
from graph import Graph
from ninja import Scopes
from safeio import need,fingerprint

class V4Fixture(Graph):
    def __init__(self, root):
        self.root=Path(root);old=self.root.parent/'preparation-v4'
        self.binding=json.loads((self.root/'inputs/v4-binding.json').read_bytes())
        self.extract=json.loads((self.root/'evidence/v4-extracted-records.json').read_bytes())
        self.old=old;self.index=old/'graph-qualification-003/graph-index.sqlite'
        need(old.resolve()==old and self.index.resolve()==self.index,'FIXTURE_BINDING','canonical v4')
        self.fd=os.open(self.index,os.O_RDONLY|os.O_NOFOLLOW);self.before=fingerprint(os.fstat(self.fd))
        self.pins=self.extract['frozen_graph_pins'];self.paths=list(self.pins);self.tree=None
        self.limits=json.loads((self.root/'inputs/profile-r8.json').read_bytes())['limits'];self.records={};self.evidence_bytes=0
        self.db=sqlite3.connect('file:'+str(self.index)+'?mode=ro&immutable=1',uri=True)
        self.db.execute('PRAGMA cache_size=-8192');self.db.execute('PRAGMA query_only=ON')
        self.includes=[{'graph':x.get('graph',x.get('file')),'path':x['path'],'line':x['line'],'kind':x['kind']} for x in self.extract['includes']]
        self.supplemental=[];self.scope_replay_complete=False
        supplement=self.root/'evidence/supplemental-bindings.json'
        if supplement.exists():
            extra=json.loads(supplement.read_bytes());need(extra['index_identity']==self.before and extra['status']=='COMPLETE','FIXTURE_BINDING','supplement identity/coverage')
            self.supplemental=extra['records'];self.binding_scan=extra;self.scope_replay_complete=True
        self.scopes=Scopes(self,self.paths,self.includes);self.recheck()
    def rows(self,kind,name):
        rows=super().rows(kind,name)
        if kind=='variable':
            for record in self.supplemental:
                if record['name']==name and not any((f,line)==(record['graph'],record['line']) for f,line,raw in rows):
                    rows.append((record['graph'],record['line'],record['raw']))
        need(len(rows)<513 and sum(len(r[2].encode()) for r in rows)<=16*1024**2,'GRAPH_SCOPE','supplement budget')
        return rows
    def recheck(self):
        final_bytes=(self.old/'FINALIZED.json').read_bytes()
        need(hashlib.sha256(final_bytes).hexdigest()==self.binding['finalized_sha256'],'FIXTURE_BINDING','v4 final seal')
        final=json.loads(final_bytes)
        need(final['index_sha256']==self.binding['index_sha256'] and final['tool_seal_sha256']==self.binding['tool_seal_sha256'],'FIXTURE_BINDING','sealed index hash')
        need(self.before==self.extract['index_identity']==fingerprint(os.fstat(self.fd))==fingerprint(self.index.lstat()),'FIXTURE_BINDING','exact held index identity')
        need(self.before[3]==self.binding['index_bytes'] and stat.S_ISREG(self.before[2]) and max(self.before[4:])<=(self.old/'FINALIZED.json').stat().st_mtime_ns,'FIXTURE_BINDING','no post-seal mutation')
        for path,pin in self.pins.items():need(fingerprint((self.old/'graph-qualification-003/frozen'/path).lstat())==pin['identity'],'FIXTURE_BINDING',path)
    def close(self):
        if self.scope_replay_complete:
            need({name for name,file in self.scopes.lookups}<=set(self.binding_scan['consulted_names']),'GRAPH_SCOPE','new unscanned variable dependency')
            needed_scopes=set()
            for name,file in self.scopes.lookups:
                scope=self.scopes.context[file][0]
                while scope is not None:
                    needed_scopes.add(scope);scope=self.scopes.parents[scope]
            needed_files={file for file,(scope,prefix) in self.scopes.context.items() if scope in needed_scopes}
            need(needed_files<=set(self.binding_scan['scanned_graphs']),'GRAPH_SCOPE','new unscanned scope')
        self.recheck();self.db.close();os.close(self.fd)
