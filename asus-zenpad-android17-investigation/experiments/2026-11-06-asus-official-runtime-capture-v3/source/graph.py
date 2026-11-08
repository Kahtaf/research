"""Bounded read-only native graph index. This never runs Ninja or any command."""
import os
from pathlib import Path
import re
import sqlite3
from safeio import need, permitted, relative, fingerprint

class Graph:
    def __init__(self, tree, paths, database, limits):
        self.tree = tree
        self.paths = paths
        self.limits = limits
        self.pins = {}
        self.records = {}
        self.evidence_bytes = 0
        self.db = sqlite3.connect(database)
        self.db.execute('PRAGMA cache_size=-8192')
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
                current, start, number = [], 0, 0
                for raw in f:
                    number += 1
                    need(len(raw) <= limits['graph_block_bytes'], 'GRAPH_BLOCK', path)
                    text = raw.decode('utf-8')
                    continuation = bool(current and current[-1].rstrip('\n').endswith('$'))
                    if current and not continuation and text[:1] not in (' ', '\t'):
                        self.store(path, start, ''.join(current))
                        current = []
                    if not current:
                        start = number
                    current.append(text)
                    need(sum(map(len, current)) <= limits['graph_block_bytes'], 'GRAPH_BLOCK', path)
                if current:
                    self.store(path, start, ''.join(current))
            need(pin == tree.digest(path, limits['graph_file_bytes']), 'DRIFT', path)
            self.db.commit()
            need(Path(database).stat().st_size <= limits['index_bytes'], 'INDEX_SIZE', path)
        self.db.commit()

    def store(self, path, line, raw):
        logical = re.sub(r'\$\n[ \t]*', '', raw).splitlines()
        if not logical:
            return
        head = logical[0]
        kind, names = None, []
        if head.startswith('build ') and ': ' in head:
            kind = 'edge'
            names = [x for x in head[6:].split(': ', 1)[0].split() if x != '|']
        elif head.startswith('rule '):
            kind, names = 'rule', [head[5:].strip()]
        elif re.match(r'^[\w.\-]+\s*= ', head):
            kind, names = 'variable', [head.split('=', 1)[0].strip()]
        for name in names:
            self.db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)', (kind, name, path, line, raw))

    def block(self, kind, name):
        rows = list(self.db.execute('SELECT file,line,text FROM blocks WHERE kind=? AND name=? LIMIT 20', (kind,name)))
        unique = {text for _,_,text in rows}
        need(rows and len(rows) < 20 and len(unique) == 1, 'GRAPH_UNKNOWN', f'{kind} {name}')
        file, line, raw = rows[0]
        key=kind+':'+name
        if key not in self.records:
            self.evidence_bytes+=len(raw.encode())
            need(self.evidence_bytes<=16*1024*1024,'GRAPH_EVIDENCE_SIZE',name)
        self.records[key] = {'kind': kind, 'name': name, 'graph': file, 'line': line, 'raw': raw}
        return raw

    def has_edge(self, name):
        return self.db.execute("SELECT 1 FROM blocks WHERE kind='edge' AND name=? LIMIT 1", (name,)).fetchone() is not None

    def expand(self, text, local=None, stack=()):
        local = local or {}
        need(len(stack) < 30, 'GRAPH_VARIABLE', 'variable cycle/depth')
        def replace(match):
            name = match.group(1) or match.group(2)
            if name in ('in', 'out'):
                return '$' + name
            need(name not in stack, 'GRAPH_VARIABLE', name)
            value = local.get(name)
            if value is None:
                value = self.block('variable', name).split('=', 1)[1].strip()
            return self.expand(value, local, stack+(name,))
        # Ninja escapes supported here; escaped whitespace in a selected path is refused later.
        sentinel = '\x01'
        text = text.replace('$$', sentinel)
        result = re.sub(r'\$\{([^}]+)\}|\$([A-Za-z0-9_.\-]+)', replace, text)
        result = result.replace('$:', ':').replace('$ ', ' ').replace(sentinel, '$')
        return result

    def edge(self, target):
        relative(target)
        raw = self.block('edge', target)
        lines = re.sub(r'\$\n[ \t]*', '', raw).splitlines()
        head = lines[0]
        local = {}
        for line in lines[1:]:
            if line.strip() and not line.lstrip().startswith('#'):
                key, sep, value = line.strip().partition('=')
                need(sep, 'GRAPH_SYNTAX', target)
                local[key.strip()] = value.strip()
        outputs, rest = head[6:].split(': ', 1)
        tokens = self.expand(rest, local).split()
        need(tokens, 'GRAPH_SYNTAX', target)
        rule = tokens[0]
        expanded_rule = None
        if rule != 'phony':
            rule_raw = self.block('rule', rule)
            # Keep the rule plus all command-variable definitions; do not execute or interpret shell.
            rule_local = {}
            for line in re.sub(r'\$\n[ \t]*', '', rule_raw).splitlines()[1:]:
                key,sep,value = line.strip().partition('=')
                if sep:
                    rule_local[key.strip()] = value.strip()
            rule_local.update(local)
            expanded_rule = self.expand(re.sub(r'\$\n[ \t]*', '', rule_raw), rule_local)
        deps = []
        category = 'explicit'
        for token in tokens[1:]:
            if token in ('|', '||', '|@'):
                category = {'|':'implicit', '||':'order_only', '|@':'validation'}[token]
            else:
                need('$' not in token, 'GRAPH_VARIABLE', token)
                deps.append({'path': token, 'kind': category})
        return {'output': target, 'rule': rule, 'outputs': outputs.split(), 'dependencies': deps, 'raw': raw, 'expanded_rule':expanded_rule}

    def recheck(self):
        for path, pin in self.pins.items():
            need(pin == self.tree.digest(path, self.limits['graph_file_bytes']), 'DRIFT', path)

    def close(self):
        self.db.close()
