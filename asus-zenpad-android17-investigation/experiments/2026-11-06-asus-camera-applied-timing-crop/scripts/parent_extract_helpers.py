"""Parsing helpers adapted from accepted register witness; no extraction side effects."""
import hashlib
import json
import re
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def masked(text):
    """Preserve offsets/newlines while masking comments and literals."""
    pattern = r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(pattern, lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), text, flags=re.S)


def block(text, start):
    clean = masked(text)
    brace = clean.index('{', start)
    depth = 0
    for pos in range(brace, len(clean)):
        if clean[pos] == '{':
            depth += 1
        elif clean[pos] == '}':
            depth -= 1
            if not depth:
                return start, pos + 1
    raise ValueError('Unterminated source block')


def function(text, name):
    matches = list(re.finditer(r'^static\s+\w+\s+' + re.escape(name) + r'\s*\([^;{}]*\)\s*\{', masked(text), re.M))
    assert len(matches) == 1, (name, len(matches))
    return block(text, matches[0].start())


def receipt(text, span, source):
    start, end = span
    data = text[start:end].encode()
    return {'source': source, 'start_line': text.count('\n', 0, start) + 1,
            'end_line': text.count('\n', 0, end) + 1, 'sha256': sha(data), 'bytes': len(data)}


