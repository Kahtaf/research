#!/usr/bin/env python3
"""Run on the Linux builder; prove the archive's colliding names survived."""
import collections,hashlib,json,tarfile
from pathlib import Path
root=Path('/srv/android/asus-hardware')
groups=collections.defaultdict(list)
with tarfile.open(root/'downloads/mt8163-dc63af1.tar.gz') as t:
    for member in t.getmembers():
        if member.isfile():
            groups[member.name.casefold()].append(member)
    rows=[]
    for members in groups.values():
        if len(members)<2:
            continue
        inodes=set();paths=[]
        for member in members:
            rel=Path(*Path(member.name).parts[1:]);p=root/'sources/kernel'/rel
            expected=hashlib.sha256(t.extractfile(member).read()).hexdigest()
            assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,str(rel)
            inodes.add(p.stat().st_ino);paths.append(str(rel))
        assert len(inodes)==len(members),paths
        rows.append(paths)
summary={'status':'passed','case_colliding_groups_preserved':len(rows),'groups':rows}
assert len(rows)==12
(root/'logs/case-files-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print('All 12 case-colliding source groups have distinct inodes and original archive bytes.')
