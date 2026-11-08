#!/usr/bin/env python3
"""Read-only exact kernel patch pre/postimage verification for parent staging."""
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser();p.add_argument('kernel',type=Path);p.add_argument('--post',action='store_true');args=p.parse_args()
S=Path(__file__).resolve().parents[1];rows=json.loads((S/'patches/pre-post-hashes.json').read_text());root=args.kernel.resolve()
for rel,row in rows.items():
 f=root/rel;assert f.resolve().is_relative_to(root) and not f.is_symlink(),rel
 expected=row['after' if args.post else 'before']
 actual=hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else None
 assert actual==expected,f'{rel}: expected {expected}, actual {actual}'
print('PASS',len(rows),'postimages' if args.post else 'preimages')
