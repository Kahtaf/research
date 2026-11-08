from pathlib import Path
R=Path('/srv/android/asus-network-runtime/kernel');print('KERNELTOP',[p.name for p in R.iterdir()][:25])
for p in [R/'net/core/filter.c',R/'kernel/bpf/verifier.c',R/'linux/net/core/filter.c']:
 if p.exists():
  s=p.read_text();print('PATH',p)
  for term in ['sk_filter_charge','optmem_max','BPF_COMPLEXITY_LIMIT','too many states','processed']:
   a=s.find(term)
   if a>=0:print(s[max(0,a-200):a+700])
