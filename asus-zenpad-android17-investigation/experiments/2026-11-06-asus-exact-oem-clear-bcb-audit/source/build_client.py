"""Serial compilation of one ARM64 object, then static link. Never execute ELF."""
from pathlib import Path
import subprocess,hashlib,json
S=Path(__file__).resolve().parents[1]
CC=Path('/usr/bin/clang');LD=Path('/OWNER_HOME/.rustup/toolchains/1.97.1-aarch64-apple-darwin/lib/rustlib/aarch64-apple-darwin/bin/rust-lld')
log=[]
commands=[[CC,'--version'],[LD,'-flavor','gnu','--version'],[CC,'--target=aarch64-linux-gnu','-Os','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-pic','-fno-pie','-mgeneral-regs-only','-Wall','-Wextra','-Werror','-c',S/'source/clear_bcb_client.c','-o',S/'artifacts/clear_bcb_client.o'],[LD,'-flavor','gnu','-m','aarch64elf','-static','--build-id=none','-e','_start','-o',S/'artifacts/clear-bcb-client',S/'artifacts/clear_bcb_client.o']]
try:
 for cmd in commands:
  args=list(map(str,cmd));p=subprocess.run(args,capture_output=True,text=True,timeout=30)
  log.append(dict(argv=args,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,log[-1]
finally:
 pins={str(p):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [CC,LD,S/'source/clear_bcb_client.c',S/'artifacts/clear_bcb_client.o',S/'artifacts/clear-bcb-client'] if p.exists()}
 (S/'evidence/client-build.json').write_text(json.dumps(dict(commands=log,files=pins),indent=2)+'\n')
print(json.dumps(pins[str(S/'artifacts/clear-bcb-client')]))
