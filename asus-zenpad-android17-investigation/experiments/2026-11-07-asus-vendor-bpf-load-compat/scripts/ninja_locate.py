from pathlib import Path
A=Path('/srv/android/lineage24/out/soong');p=A/'build.lineage_p00a.ninja';print(p.stat().st_size)
with p.open() as f:
 for line in f:
  if 'libbpf_android' in line: print(line[:600])
print('subninjas')
with p.open() as f:
 for line in f:
  if 'subninja' in line and 'bpf' in line: print(line)
