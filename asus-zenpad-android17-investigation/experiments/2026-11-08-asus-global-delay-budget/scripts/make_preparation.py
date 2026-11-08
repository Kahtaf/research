from pathlib import Path
import difflib,hashlib,json
R=Path(__file__).resolve().parents[1];old=(R/'source/ancestor/arch/arm64/lib/delay.c').read_text();identity=json.loads((R/'evidence/identity.json').read_text());u=identity['kernel_run_uuid']
a='''\tcycles_t start = get_cycles();

\twhile ((get_cycles() - start) < cycles)
\t\tcpu_relax();'''
b='''\tcycles_t start = get_cycles();
\tcycles_t last;
\tunsigned long iterations = 0;

\twhile (((last = get_cycles()) - start) < cycles) {
\t\tcpu_relax();
\t\tif (++iterations == (1UL << 24)) {
\t\t\tdump_stack();
\t\t\tpanic("ASUS49-DELAY-BUDGET run=UUID start=%#llx last=%#llx requested=%lu iterations=%lu caller=%p caller_symbol=%pS",
\t\t\t      (unsigned long long)start, (unsigned long long)last,
\t\t\t      cycles, iterations, __builtin_return_address(0),
\t\t\t      __builtin_return_address(0));
\t\t}
\t}'''.replace('UUID',u)
assert old.count(a)==1;new=old.replace(a,b);p=R/'source/modified/arch/arm64/lib/delay.c';p.parent.mkdir(parents=True);p.write_text(new)
eold=(R/'source/ancestor/arch/arm64/kernel/asus_entry_tag.h').read_text();enew=eold.replace(identity['helper_run_uuid'],u);assert enew!=eold and len(enew)==len(eold)
p=R/'source/modified/arch/arm64/kernel/asus_entry_tag.h';p.parent.mkdir(parents=True);p.write_text(enew)
identity['entry_tag']=json.loads(enew.split(' ',2)[2].split('\n')[0]);identity['expected_release']='4.9.337-asus-p00a-experimental-minplat'
(R/'evidence/identity.json').write_text(json.dumps(identity,indent=2)+'\n')
changes={}
for n in ['arch/arm64/lib/delay.c','arch/arm64/kernel/asus_entry_tag.h']:
 a=(R/'source/ancestor'/n).read_bytes();z=(R/'source/modified'/n).read_bytes();changes[n]=dict(preimage=hashlib.sha256(a).hexdigest(),postimage=hashlib.sha256(z).hexdigest(),data=z.hex())
(R/'source/kernel.diff').write_text(''.join(''.join(difflib.unified_diff((R/'source/ancestor'/n).read_text().splitlines(True),(R/'source/modified'/n).read_text().splitlines(True),fromfile='r3/'+n,tofile='delay-budget/'+n)) for n in changes))
s='''from pathlib import Path
import base64,hashlib,json,os,shutil
B=Path('/srv/android/asus-minimal-platform-build-r3-20261108');R=Path('/srv/android/asus-global-delay-budget-20261108');K=R/'kernel';O=R/'out'
changes=CHANGES
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not R.exists(),'One isolated prefix only'
assert sha(B/'out/.config')=='01d6729f825798899e21192e6c33f96a80b47ccbedd5dc6cab10f78c1f9c7f31'
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='d164cbbee409d192caf9b0135238f0382c2f66ed31e622cc0bdb4f815baa8cec'
for n,v in changes.items():assert sha(B/'kernel'/n)==v['preimage'],n
R.mkdir();(R/'evidence').mkdir();(R/'tmp').mkdir()
# Ordinary independent copies; no links, make clean, utime/touch or command-file manipulation.
shutil.copytree(B/'kernel',K,symlinks=True)
shutil.copytree(B/'out',O,symlinks=True)
assert (O/'source').is_symlink();(O/'source').unlink();(O/'source').symlink_to(K)
for n,v in changes.items():(K/n).write_bytes(bytes.fromhex(v['data']))
changed=[];counts=0
for parent,ds,ns in os.walk(K):
 for name in ns:
  p=Path(parent)/name;rel=p.relative_to(K);before=B/'kernel'/rel
  if p.is_symlink():assert before.is_symlink() and os.readlink(p)==os.readlink(before)
  else:
   assert p.stat().st_ino!=before.stat().st_ino
   counts+=1
   if sha(p)!=sha(before):changed.append(str(rel))
assert set(changed)==set(changes),changed
rec=dict(status='ISOLATED_SOURCE_PREPARED',ancestor=str(B),prefix=str(R),independent_source_files_verified=counts,source_changes={n:{k:v for k,v in c.items() if k!='data'} for n,c in changes.items()},config_sha256=sha(O/'.config'),owned_source_symlink=str((O/'source').resolve()),hardlinks_used=False,timestamp_or_command_manipulation=False)
(R/'evidence/preparation.json').write_text(json.dumps(rec,indent=2)+'\\n')
print(json.dumps(rec))
'''.replace('CHANGES',repr(changes))
(R/'scripts/03_prepare.py').write_text(s)
print((R/'source/kernel.diff').read_text())
