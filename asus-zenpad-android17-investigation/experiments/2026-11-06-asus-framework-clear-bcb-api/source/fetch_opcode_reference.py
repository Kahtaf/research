from pathlib import Path
import urllib.request,base64,hashlib,json
S=Path(__file__).resolve().parents[1]
u='https://android.googlesource.com/platform/art/+/android-7.0.0_r1/runtime/dex_instruction_list.h?format=TEXT'
with urllib.request.urlopen(u,timeout=20) as r:b=base64.b64decode(r.read(256*1024))
assert b'#define DEX_INSTRUCTION_LIST' in b
(S/'source/reference-dex_instruction_list.h').write_bytes(b)
(S/'evidence/opcode-reference.json').write_text(json.dumps(dict(url=u,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),use='Opcode/formats only; no OEM transaction or behavior inferred from AOSP'),indent=2)+'\n')
