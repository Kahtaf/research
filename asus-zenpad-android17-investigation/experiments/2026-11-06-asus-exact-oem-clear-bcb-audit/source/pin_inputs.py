"""Copy only explicit public software and public aggregate receipts into spike."""
from pathlib import Path
import hashlib,json
S=Path(__file__).resolve().parents[1];W=S.parent
items=[('2026-11-06-asus-pending-recovery-request/source/uncrypt','uncrypt','3f7e8c8ed7272540315eaef0af405a57ac701db121dd5c842a8b04be721b2671','exact live public software; matches prior OEM system extraction'),('2026-11-06-asus-pending-recovery-request/source/uncrypt.rc','uncrypt.rc','63b33e2a2271d0c598bca842d0e6b03564004ed1e0e2995e8dd8ed5616455e82','exact live public software'),('2026-11-06-asus-stock-userdata-recovery/inputs/boot__fstab.mt8163','fstab.mt8163','9f22f786ac2fdbaa10d0d40a7f2a962a3c7008cd22c8c54d4c4454232a6bf46c','prior boot public extraction; boot image hash 7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316; live verification remains parent gate'),('2026-11-06-asus-stock-userdata-recovery/inputs/system__build.prop','build.prop',None,'prior exact OEM public system extraction'),('2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/net/unix/af_unix.c','reference-kernel-af_unix.c',None,'ASUS Kernel_V4_7_0.zip, SHA d8b9d77a7e8b5151c2b68c96e784842a25b167cf8a7044188e7044a5fdbcd41c; 3.18.22 source OLDER than stock 3.18.35; ABI/peer semantics reference only, NOT exact running kernel proof')]
base='2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/include/uapi/asm-generic/'
for f in ['stat.h','fcntl.h','unistd.h','socket.h']:items.append((base+f,'reference-kernel-'+f,None,'same older ASUS 3.18.22 public source; Linux AArch64 ABI reference'))
records=[]
for src,dst,pin,provenance in items:
 b=(W/src).read_bytes();digest=hashlib.sha256(b).hexdigest()
 if pin:assert digest==pin
 (S/'source/oem'/dst).write_bytes(b);records.append(dict(source=src,file='source/oem/'+dst,bytes=len(b),sha256=digest,provenance=provenance))
for name in ['parent-findings.json','before-capture-ac7cd9c04571db33.json']:
 src=W/'2026-11-06-asus-pending-recovery-request/evidence'/name;b=src.read_bytes();(S/'evidence'/('parent-'+name)).write_bytes(b);records.append(dict(source=str(src.relative_to(W)),file='evidence/parent-'+name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),provenance='parent aggregate receipt only; private paths named but never followed'))
(S/'evidence/input-pins.json').write_text(json.dumps(records,indent=2)+'\n')
