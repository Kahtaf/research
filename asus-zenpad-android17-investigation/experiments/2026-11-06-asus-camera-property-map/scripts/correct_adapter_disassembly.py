from pathlib import Path
import subprocess,json
r=Path('/srv/android/asus-camera-property-map-20261106');llvm=Path('/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b/bin')
commands=json.loads((r/'commands.json').read_text())
for arch in ['arm','arm64']:
 a=[str(llvm/'llvm-objdump'),'-d','--demangle',str(r/arch/'libasus_camera_legacy_property_map.so')]
 p=subprocess.run(a,capture_output=True,text=True,check=True,timeout=20);(r/arch/'disassembly.txt').write_text(p.stdout);commands.append({'argv':a,'cwd':str(r),'rc':0,'stdout':p.stdout,'stderr':p.stderr})
(r/'commands.json').write_text(json.dumps(commands,indent=2));print('Corrected new adapter disassembly uses ELF mapping symbols, including ARM state for new ARM32 code. OEM/provider Thumb-state receipts are unchanged.')
