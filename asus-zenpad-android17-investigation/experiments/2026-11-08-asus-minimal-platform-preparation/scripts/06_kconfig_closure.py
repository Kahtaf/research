from pathlib import Path
import os,re,json,hashlib,base64
K=Path('/srv/android/asus-minimal-platform-preparation-20261108/kernel')
syms='CPU_IDLE|NET|NETDEVICES|INET|NETFILTER|USB_SUPPORT|USB_GADGET|USB_PHY|FB|ANDROID_DEFAULT_SETTING'
found={}
for parent,ds,ns in os.walk(K):
 ds[:]=[d for d in ds if d!='.git']
 for n in ns:
  if not n.startswith('Kconfig'):continue
  p=Path(parent)/n;lines=p.read_text(errors='replace').splitlines()
  hits=[i for i,l in enumerate(lines) if re.search(r'\bselect\s+(?:'+syms+r')\b|^config ANDROID_DEFAULT_SETTING\b',l)]
  if hits:found[str(p.relative_to(K))]=[dict(line=i+1,context='\n'.join(lines[max(0,i-5):min(len(lines),i+7)])) for i in hits]
files={}
# Only return the actual platform/default selector definitions, not unrelated architectures.
for n in found:
 if n.startswith(('arch/arm64/','drivers/misc/mediatek/')) or n in ['init/Kconfig','drivers/Kconfig','arch/Kconfig'] or 'android' in n.lower():
  b=(K/n).read_bytes();files['source/baseline/'+n]=dict(data=base64.b64encode(b).decode(),sha256=hashlib.sha256(b).hexdigest())
print(json.dumps(dict(files=files,selectors={n:h for n,h in found.items() if n in [p.removeprefix('source/baseline/') for p in files]})))
