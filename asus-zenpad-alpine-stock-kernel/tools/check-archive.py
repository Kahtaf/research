#!/usr/bin/env python3
"""Verify the source-only archive without running its experimental scripts."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
MAX_FILE=262144
MAX_TOTAL=2097152
DENIED_SUFFIXES={'.img','.raw','.ext4','.apk','.so','.a','.o','.pyc','.sqlite','.db','.pem','.key','.png','.jpg','.mp4','.m4a','.wav','.gz','.xz','.zip','.tar'}
SECRET_PATTERNS=[re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}'),re.compile(r'\bgithub_pat_[A-Za-z0-9_]+'),re.compile(r'\bAKIA[A-Z0-9]{16}\b'),re.compile(r'\bAIza[A-Za-z0-9_-]{30,}'),re.compile(r'\bssh-(?:ed25519|rsa) [A-Za-z0-9+/]{30,}'),re.compile(r'\bH5NPCX[A-Z0-9]+\b'),re.compile(r'\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b'),re.compile(r'\b192\.168\.\d{1,3}\.\d{1,3}\b')]
def main():
 manifest=json.loads((ROOT/'ARCHIVE-MANIFEST.json').read_text())
 expected={row['path']:row for row in manifest['files']}
 assert len(expected)==len(manifest['files']),'Duplicate manifest path'
 actual={str(p.relative_to(ROOT)):p for p in ROOT.rglob('*') if p.is_file()}
 # This research repository generates _summary.md after commit; it is not a checkpoint input.
 extras=set(actual)-set(expected)-{'ARCHIVE-MANIFEST.json','_summary.md'}
 assert not extras,('Unlisted archive files',sorted(extras))
 assert set(expected)<=set(actual),'Missing archive input'
 total=0
 for name,p in actual.items():
  parts=Path(name).parts
  assert not set(parts)&{'.git','private','downloads','artifacts','node_modules','__pycache__'},('Excluded directory',name)
  assert p.suffix not in DENIED_SUFFIXES,('Artifact extension',name)
  assert p.name not in {'.env','id_rsa','id_ed25519','authorized_keys','known_hosts'},('Private file',name)
  if p.is_symlink():
   row=expected.get(name,{})
   assert row.get('type')=='symlink' and p.readlink().as_posix()==row['link_target'],('Unlisted symlink',name)
   assert p.resolve().is_relative_to(ROOT) and p.resolve().relative_to(ROOT).as_posix() in expected,('Escaping symlink',name)
   b=p.readlink().as_posix().encode()
  else:b=p.read_bytes()
  total+=len(b)
  assert len(b)<=MAX_FILE,('Oversize',name,len(b))
  text=b.decode('utf-8');assert '\x00' not in text,('Binary content',name)
  for pattern in SECRET_PATTERNS:assert not pattern.search(text),('Sensitive pattern',name)
  if name in expected:
   row=expected[name]
   assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],('Changed file',name)
  if p.suffix=='.json':json.loads(text)
 assert total<=MAX_TOTAL,('Oversize archive',total)
 print(json.dumps({'status':'SOURCE_ONLY_ARCHIVE_OK','manifest_files':len(expected),'total_bytes':total,'largest_file_bytes':max(p.stat().st_size for p in actual.values()),'tablet_access':False,'experimental_scripts_executed':False}))
if __name__=='__main__':main()
