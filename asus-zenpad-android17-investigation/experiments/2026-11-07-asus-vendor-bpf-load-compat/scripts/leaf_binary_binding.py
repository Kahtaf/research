from pathlib import Path
import struct,hashlib,json
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');sha=lambda b:hashlib.sha256(b).hexdigest()
def sections(b):
 off=struct.unpack_from('<Q',b,40)[0];sz,num,idx=struct.unpack_from('<HHH',b,58);rows=[struct.unpack_from('<IIQQQQIIQQ',b,off+i*sz) for i in range(num)];st=b[rows[idx][4]:rows[idx][4]+rows[idx][5]];return {st[x[0]:].split(b'\0',1)[0].decode():b[x[4]:x[4]+x[5]] for x in rows if x[1]!=8}
a=sections((R/'inputs/libbpf_android.so').read_bytes());b=sections((R/'attempt-compile-floor/libbpf_android.candidate.so').read_bytes());c=sections((R/'inputs/libbpf_android.candidate.so').read_bytes());d={n:dict(installed=sha(a[n]),guard_optimized_away_attempt=sha(b[n]),candidate=sha(c[n]),installed_equals_optimized_attempt=a[n]==b[n],installed_equals_candidate=a[n]==c[n]) for n in ['.text','.rodata','.dynsym','.dynstr']};(R/'evidence/leaf-binary-binding.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
