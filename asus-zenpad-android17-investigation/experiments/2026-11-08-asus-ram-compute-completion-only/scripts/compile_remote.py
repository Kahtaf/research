"""One helper compile only; read-only pins for reused kernel context."""
from pathlib import Path
import gzip,hashlib,json,subprocess,sys,traceback
R=Path(__file__).resolve().parents[1]
B=Path('/srv/android/asus-normal-ram-compute-control-20261108-03f2153c')
E=R/'evidence';A=R/'artifacts'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+'\n')
def run(cmd,name):
 p=subprocess.run(cmd,capture_output=True,text=True)
 (E/(name+'.stdout')).write_text(p.stdout);(E/(name+'.stderr')).write_text(p.stderr)
 p.check_returncode()
 return p.stdout
assert not (E/'build-status.json').exists(),'one compile only'
s=dict(status='started',helper_compiles=0,kernel_builds=0)
save('build-status.json',s)
try:
 K=Path('/srv/android/asus-pid1-fifo-loop-control-20261108-f53fadc2')
 frozen=[K/'out/arch/arm64/boot/Image.gz-dtb',K/'out/.config',B/'source/init.c',B/'artifacts/init']
 pins={str(p):dict(sha256=sha(p),inode=p.stat().st_ino,mtime_ns=p.stat().st_mtime_ns) for p in frozen}
 assert sha(frozen[0])=='948539cd11744e1f3bbed55389c2118c940d8206ce7e6ea1e89dce54f0b99954'
 assert sha(frozen[1])=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
 assert sha(frozen[2])=='b70b0768fcd5619317a78f922e4f5fb7bdeffd1707a26eb9928886011a0c22e2'
 assert sha(frozen[3])=='f8d201a6b72b13a4068584f8a5e73526f8eef669eabc96975ca69547506d3b26'
 expected=json.loads((E/'remote-source-pins.json').read_text())
 kpins={n:dict(sha256=sha(K/n),inode=(K/n).stat().st_ino,mtime_ns=(K/n).stat().st_mtime_ns) for n in expected}
 for n,h in expected.items():assert sha(K/n)==h
 compiler=Path('/usr/bin/aarch64-linux-gnu-gcc')
 assert sha(compiler)=='cd90adc7801f4595267f61a5d25bd3a0c6beb2f9f1f107ab919a97a12972dc9a'
 cmd=[str(compiler),'-static','-Os','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Wall','-Wextra','-o',str(A/'init.unstripped'),str(R/'source/init.c')]
 s['helper_compiles']=1;save('build-status.json',s);run(cmd,'helper-compile')
 strip=['aarch64-linux-gnu-strip','-o',str(A/'init'),str(A/'init.unstripped')];run(strip,'helper-strip')
 sys.path.insert(0,str(R/'source'));import bootformat as b
 entries={n:(0o040755,0,0,b'') for n in ['dev','proc','sys']};entries['init']=(0o100755,0,0,(A/'init').read_bytes())
 payload=gzip.compress(b.make_cpio(entries),compresslevel=9,mtime=0)
 receipt=dict(command=cmd,strip=strip,compiler_sha256=sha(compiler),source_sha256=sha(R/'source/init.c'),binary_sha256=sha(A/'init'),binary_bytes=(A/'init').stat().st_size,payload_bytes=len(payload),guard_end='0x4403f007',fits=0x44000000+len(payload)<=0x4403f007,helper_compiles=1,kernel_builds=0)
 save('compiler-receipt.json',receipt)
 assert receipt['fits'],'STOP: gzip exceeds unchanged guard; no recompile/rebuild'
 (A/'initramfs.cpio.gz').write_bytes(payload)
 dis=''
 for sym in ['main','observe','compute_loop','monotonic_clock','event','finish']:
  dis+=run(['aarch64-linux-gnu-objdump','-d','--disassemble='+sym,str(A/'init.unstripped')],'dis-'+sym)
 (E/'helper-scoped.disasm').write_text(dis)
 kd=''
 for sym in ['stext','asus_retained_trace_write']:
  kd+=run(['aarch64-linux-gnu-objdump','-d','--disassemble='+sym,str(K/'out/vmlinux')],'kernel-'+sym)
 (E/'reused-kernel-scoped.disasm').write_text(kd)
 for n,v in pins.items():
  p=Path(n);assert sha(p)==v['sha256'] and p.stat().st_ino==v['inode'] and p.stat().st_mtime_ns==v['mtime_ns']
 for n,v in kpins.items():
  p=K/n;assert sha(p)==v['sha256'] and p.stat().st_ino==v['inode'] and p.stat().st_mtime_ns==v['mtime_ns']
 save('remote-reuse.json',dict(pins=pins,kernel_source_pins=kpins,pre_post_unchanged=True,no_kernel_build_or_copy=True))
 s['status']='complete'
except BaseException as exc:
 s.update(status='failed',error=repr(exc));traceback.print_exc()
finally:save('build-status.json',s)
print(json.dumps(s));sys.exit(s['status']!='complete')
