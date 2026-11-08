from pathlib import Path
import json,subprocess
R=Path('/srv/android/asus-minimal-platform-build-r3-20261108');O=R/'out'
i=json.loads((R/'evidence/identity.json').read_text());raw=(O/'arch/arm64/boot/Image').read_bytes();nm=subprocess.check_output(['aarch64-linux-gnu-nm','-an',str(O/'vmlinux')],text=True);syms={l.split()[2]:int(l.split()[0],16) for l in nm.splitlines() if len(l.split())==3};tag=i['entry_tag'].encode()
selected={n:hex(v) for n,v in syms.items() if n in ['_text','asus_entry_tag','asus_entry_tag_end','entry_marker']}
actual={n:raw[v-syms['_text']:v-syms['_text']+len(tag)].decode(errors='replace') for n,v in syms.items() if n in ['asus_entry_tag','entry_marker']}
print(json.dumps(dict(literal_count=raw.count(tag),symbols=selected,literals=actual,header=(R/'kernel/arch/arm64/kernel/asus_entry_tag.h').read_text())))
