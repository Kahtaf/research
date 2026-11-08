from pathlib import Path
import subprocess,json,hashlib,shutil
R=Path(__file__).resolve().parents[1];B=R.parent/'2026-11-06-asus-android17-build-continuation';old=R.parent/'2026-11-06-asus-android17-os-rescue';out=R/'evidence/reproduction';out.mkdir(exist_ok=True);log=[]
def run(a):
 p=subprocess.run([str(x) for x in a],capture_output=True,text=True);log.append({'argv':[str(x) for x in a],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,p.stderr
src=R/'source/probe';src.mkdir(exist_ok=True)
for n in ['diag.c','test_diag.c','policy_patch.c','check_genfs.c']:shutil.copyfile(B/'probe'/n,src/n)
clang='/usr/bin/clang';lld=Path.home()/'.rustup/toolchains/1.97.1-aarch64-apple-darwin/lib/rustlib/aarch64-apple-darwin/bin/rust-lld';lib=old/'artifacts/tools-final/libsepol'
run([clang,'--target=aarch64-linux-gnu','-Os','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-pic','-fno-pie','-mgeneral-regs-only','-Wall','-Wextra','-Werror','-c',src/'diag.c','-o',out/'diag.o'])
run([lld,'-flavor','gnu','-m','aarch64elf','-static','--build-id=none','-e','_start','-o',out/'diag',out/'diag.o'])
assert (out/'diag').read_bytes()==(R/'source/ramdisk/sbin/recovery').read_bytes()
for n in ['policy_patch','check_genfs']:
 run([clang,'-O2','-I',lib/'include',src/(n+'.c'),lib/'src/libsepol.a','-o',out/n])
run([out/'policy_patch',old/'artifacts/candidate-final/stock-sepolicy',out/'sepolicy'])
assert (out/'sepolicy').read_bytes()==(R/'source/ramdisk/sepolicy').read_bytes()
run([out/'check_genfs',out/'sepolicy'])
run([clang,'-O1','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',src/'test_diag.c','-o',out/'test_diag'])
run([out/'test_diag'])
run([clang,'--version']);run([lld,'-flavor','gnu','--version'])
(R/'evidence/reproduction.json').write_text(json.dumps({'helper_byte_identical':True,'policy_byte_identical':True,'scope':'local helper and policy only; no kernel rebuild or physical execution','commands':log},indent=2)+'\n');print('Helper and policy reproduced byte-identically; supplied mock ASan/UBSan tests pass.')
