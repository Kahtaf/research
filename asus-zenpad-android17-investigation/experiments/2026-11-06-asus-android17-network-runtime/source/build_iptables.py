from pathlib import Path
import shutil,subprocess as s,os,json,sys
R=Path('/srv/android/asus-network-runtime');T=Path('/srv/android/lineage24');I=R/'inputs/iptables';O=R/'iptables-build';O.mkdir(exist_ok=True);os.environ['TMPDIR']=str(R/'tmp')
if not I.exists():shutil.copytree(T/'external/iptables',I,ignore=shutil.ignore_patterns('.git'),symlinks=True)
# Use the checked-in Android static extension generators and a bounded real extension set.
extensions=['standard','bpf','owner','tcp','udp','comment','mark','MARK','connmark','CONNMARK']
generated=[]
for name in extensions:
 source=I/'extensions'/('libxt_'+name+'.c');p=O/source.name;p.write_bytes(s.check_output(['sh',str(I/'extensions/filter_init'),str(source)]));generated.append(p)
for suffix in ['', '4','6']:
 p=O/('initext'+suffix+'.c');p.write_bytes(s.check_output(['bash',str(I/'extensions/gen_init'),suffix]+([str(x) for x in generated] if not suffix else [])));generated.append(p) if suffix else None
srcs=[I/'libxtables/xtables.c',I/'libxtables/xtoptions.c',I/'libiptc/libip4tc.c',I/'libiptc/libip6tc.c']+[I/'iptables'/f for f in ['xtables-legacy-multi.c','iptables-xml.c','xshared.c','iptables-save.c','iptables-restore.c','iptables-standalone.c','iptables.c','ip6tables-standalone.c','ip6tables.c']]+[O/('libxt_'+name+'.c') for name in extensions]+[O/('initext'+suffix+'.c') for suffix in ['', '4','6']]
cmd=['aarch64-linux-gnu-gcc','-static','-O2','-D_LARGEFILE_SOURCE=1','-D_LARGE_FILES','-D_FILE_OFFSET_BITS=64','-D_REENTRANT','-DENABLE_IPV4','-DENABLE_IPV6','-DNO_SHARED_LIBS=1','-DALL_INCLUSIVE','-DXTABLES_INTERNAL','-DXTABLES_LIBDIR="xtables_libdir_not_used"','-I'+str(I),'-I'+str(I/'include'),'-I'+str(I/'iptables'),'-I'+str(I/'libiptc'),*[str(p) for p in srcs],'-lm','-o',str(R/'artifacts/iptables')]
p=s.run(cmd,capture_output=True,text=True);(R/'evidence'/('iptables-build-'+sys.argv[1]+'.json')).write_text(json.dumps(dict(command=cmd,exit=p.returncode,output=p.stdout+p.stderr),indent=2)+'\n');print(p.returncode,p.stderr);raise SystemExit(p.returncode)
