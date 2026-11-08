from pathlib import Path
import json,subprocess
roots=['/srv/android/asus-linux49-vintf-port-20261106','/srv/android/asus-reviewed-build-kit','/srv/android/asus-r9-independent-packaging-r2','/srv/android/asus-r9-postbuild-validation-r2']
r={}
for root in roots:
 p=Path(root);r[root]={'top':sorted(x.name for x in p.iterdir()) if p.exists() else []}
 q=subprocess.run(['find',root,'-maxdepth','5','-type','f','(','-name','checkvintf','-o','-name','assemble_vintf','-o','-name','kconfig_xml_fixup',')'],capture_output=True,text=True,timeout=12);r[root]['tools']=q.stdout
print(json.dumps(r,indent=2))
