"""Bounded read-only native graph index. This never runs Ninja or any command."""
import os
from pathlib import Path
import re
import sqlite3
from safeio import need, permitted, relative, fingerprint, Refusal
from ninja import Scopes, logical

class Graph:
    def __init__(self, tree, paths, database, limits):
        need(0 < len(paths) <= 128, 'GRAPH_INVENTORY', 'bounded graph file count')
        need(limits['index_bytes'] >= 3*4096, 'INDEX_SIZE', 'SQLite schema needs three pages')
        self.tree = tree
        self.paths = paths
        self.limits = limits
        self.pins = {}
        self.records = {}
        self.evidence_bytes = 0
        self.stats = []
        self.includes = []
        self.counts = {"edge": 0, "rule": 0, "variable": 0}
        self.max_block_bytes = 0
        self.max_line_bytes = 0
        self.db = sqlite3.connect(database)
        self.db.execute('PRAGMA page_size=4096')
        self.db.execute('PRAGMA cache_size=-8192')
        self.db.execute('PRAGMA temp_store=FILE')
        self.db.execute('PRAGMA journal_mode=OFF')
        self.db.execute('PRAGMA max_page_count='+str(limits['index_bytes']//4096))
        self.db.execute('CREATE TABLE blocks (kind TEXT, name TEXT, file TEXT, line INTEGER, text TEXT)')
        self.db.execute('CREATE INDEX lookup ON blocks(kind,name)')
        total = 0
        for path in paths:
            pin = tree.digest(path, limits['graph_file_bytes'])
            total += pin['bytes']
            need(total <= limits['graph_total_bytes'], 'GRAPH_SIZE', path)
            self.pins[path] = pin
            with tree.open(path) as f:
                current, start, number, block_bytes = [], 0, 0, 0
                before_counts = self.counts.copy()
                for raw in iter(lambda: f.readline(limits['graph_block_bytes'] + 1), b''):
                    number += 1
                    need(len(raw) <= limits['graph_block_bytes'], 'GRAPH_BLOCK', path)
                    self.max_line_bytes = max(self.max_line_bytes, len(raw))
                    text = raw.decode('utf-8')
                    tail = current[-1].rstrip('\r\n') if current else ''
                    continuation = bool((len(tail)-len(tail.rstrip('$')))%2)
                    if current and not continuation and text[:1] not in (' ', '\t'):
                        self.store(path, start, ''.join(current))
                        current = []
                        block_bytes = 0
                    if not current:
                        start = number
                    current.append(text)
                    block_bytes += len(raw)
                    need(block_bytes <= limits['graph_block_bytes'], 'GRAPH_BLOCK', path)
                    self.max_block_bytes = max(self.max_block_bytes, block_bytes)
                if current:
                    self.store(path, start, ''.join(current))
            need(pin == tree.digest(path, limits['graph_file_bytes']), 'DRIFT', path)
            self.db.commit()
            index_bytes = Path(database).stat().st_size
            need(index_bytes <= limits['index_bytes'], 'INDEX_SIZE', path)
            self.stats.append({'path': path, 'bytes': pin['bytes'], 'lines': number,
                               'rows': {k: self.counts[k]-before_counts[k] for k in self.counts},
                               'cumulative_index_bytes': index_bytes})
        self.db.commit()
        self.scopes = Scopes(self, self.paths, self.includes)
        for include in self.includes:
            relative(include['path'])
            need(include['path'] in self.pins, 'GRAPH_INCLUDE', include['path'])

    def store(self, path, line, raw):
        lines = logical(raw)
        if not lines:
            return
        head = lines[0]
        if head.startswith(('subninja ', 'include ')):
            self.includes.append({'graph': path, 'line': line, 'path': head.split(' ', 1)[1].strip(), 'kind': head.split(' ',1)[0]})
            need(len(self.includes) <= 128, 'GRAPH_INVENTORY', 'too many graph include directives')
        kind, names = None, []
        if head.startswith('build ') and ': ' in head:
            kind = 'edge'
            names = [x for x in head[6:].split(': ', 1)[0].split() if x != '|']
        elif head.startswith('rule '):
            kind, names = 'rule', [head[5:].strip()]
        elif re.match(r'^[\w.\-]+\s*=', head):
            kind, names = 'variable', [head.split('=', 1)[0].strip()]
        for name in names:
            try:
                self.db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)', (kind, name, path, line, raw))
            except sqlite3.OperationalError as error:
                if getattr(error, 'sqlite_errorcode', None) == sqlite3.SQLITE_FULL:
                    raise Refusal('INDEX_SIZE', 'SQLite hard page ceiling exhausted') from error
                raise
            self.counts[kind] += 1

    def rows(self, kind, name):
        rows=[];size=0
        for row in self.db.execute('SELECT file,line,text FROM blocks WHERE kind=? AND name=? LIMIT 513',(kind,name)):
            size+=len(row[2].encode())
            need(size<=16*1024**2,'GRAPH_EVIDENCE_SIZE','scoped query '+name)
            rows.append(row)
            need(len(rows)<513,'GRAPH_SCOPE','definition count '+name)
        return rows

    def record(self, kind, name, file, line, raw):
        key=kind+':'+name
        if key in self.records and (self.records[key]['graph'],self.records[key]['line'])!=(file,line):key+='@'+file+':'+str(line)
        if key not in self.records:
            self.evidence_bytes+=len(raw.encode())
            need(self.evidence_bytes<=16*1024*1024,'GRAPH_EVIDENCE_SIZE',name)
        self.records[key]={'kind':kind,'name':name,'graph':file,'line':line,'raw':raw}
        return raw

    def block(self, kind, name):
        rows=self.rows(kind,name)
        need(rows and len(rows)<20 and len({text for _,_,text in rows})==1,'GRAPH_UNKNOWN',kind+' '+name)
        return self.record(kind,name,*rows[0])

    def has_edge(self, name):
        return self.db.execute("SELECT 1 FROM blocks WHERE kind='edge' AND name=? LIMIT 1", (name,)).fetchone() is not None

    def edge(self, target):
        relative(target)
        rows=self.rows('edge',target)
        need(rows and len(rows)<20 and len({raw for _,_,raw in rows})==1,'GRAPH_UNKNOWN','edge '+target)
        self.record('edge',target,*rows[0])
        return self.scopes.edge(target,rows[0])

    def recheck(self):
        for path, pin in self.pins.items():
            need(pin == self.tree.digest(path, self.limits['graph_file_bytes']), 'DRIFT', path)

    def close(self):
        self.db.close()
