from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'sources/kernel';BACKUP=ROOT/'sources/original-files'
def replace(path,old,new):
 p=SOURCE/path;s=p.read_text();assert old in s,(path,old[:80]);assert s.count(old)==1,(path,s.count(old))
 saved=BACKUP/path
 if not saved.exists():saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(p.read_bytes())
 p.write_text(s.replace(old,new,1))
def write_new(path,content):
 p=SOURCE/path;assert not p.exists(),path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
