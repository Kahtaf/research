from pathlib import Path
import json,hashlib,subprocess,re
providers={'arm': {'libc++.so': {'path': '/srv/android/asus-camera-arm32-route/sdk37-libs/libc++.so', 'bytes': 848140, 'sha256': '7643c0eee93812b9cc2e7834f947b1065989a8ea75b443f8f3d9a9f0064fa6e8'}, 'libc.so': {'path': '/srv/android/asus-camera-arm32-route/sdk37-libs/libc.so', 'bytes': 1033968, 'sha256': '5c8ad4f3ba393584deb319428deb7e67a9d959426fe9acee1a616cc5d7cb0b66'}, 'libcutils.so': {'path': '/srv/android/asus-camera-arm32-route/sdk37-libs/libcutils.so', 'bytes': 62272, 'sha256': '63dcfb0ab9ce50dddbe70a1842a1f5a5b9b526a5c1d22cc055d35505d2e0db05'}, 'libdl.so': {'path': '/srv/android/asus-camera-arm32-route/sdk37-libs/libdl.so', 'bytes': 5464, 'sha256': 'a15285a05344c501e44112dfa7e84913875a07a5dd76e2ade80bdb579cb84035'}, 'liblog.so': {'path': '/srv/android/asus-camera-arm32-route/sdk37-libs/liblog.so', 'bytes': 42568, 'sha256': '473bb94ce06678bffd72eb2c34d2f105d540cdedba6e5cc9c4f2c2d073449f9d'}, 'libm.so': {'path': '/srv/android/asus-camera-arm32-route/sdk37-libs/libm.so', 'bytes': 125764, 'sha256': '16fb57b8affea6b02630c09a58928672665c1ceefdbcfd71f01d147914306052'}, 'libutils.so': {'path': '/srv/android/asus-camera-arm32-route/sdk37-libs/libutils.so', 'bytes': 82164, 'sha256': '7441b9292d84e08e18a58eda1a0f50789818e47f2b22bd0065900d6065f95924'}}, 'arm64': {'libc++.so': {'path': '/srv/android/asus-camera-source-abi-route/sdk37-libs/libc++.so', 'bytes': 1152760, 'sha256': 'cb118e98c74d3454858921123b9b51ba13df9cad7dfa141dd892c453661a4d78'}, 'libc.so': {'path': '/srv/android/asus-camera-source-abi-route/sdk37-libs/libc.so', 'bytes': 1258616, 'sha256': '151cc98631ea0621083d98704fed429c75514884ed16c55e91840da3b8d91a2a'}, 'libcutils.so': {'path': '/srv/android/asus-camera-source-abi-route/sdk37-libs/libcutils.so', 'bytes': 93768, 'sha256': '9ed4cd5c59ca17c3f041cccbf27909a7e3a217b66def421f46987e1eb06de7a4'}, 'libdl.so': {'path': '/srv/android/asus-camera-source-abi-route/sdk37-libs/libdl.so', 'bytes': 13976, 'sha256': 'f074638d52d74bea9ee0add172f776f95025ad2268a28a7cb817ded90f6eb4bd'}, 'liblog.so': {'path': '/srv/android/asus-camera-source-abi-route/sdk37-libs/liblog.so', 'bytes': 65664, 'sha256': '3fdf6471b1193fb21e2bbe81fda62e05a8633e1712bbe12fd35e544ed74ec57f'}, 'libm.so': {'path': '/srv/android/asus-camera-source-abi-route/sdk37-libs/libm.so', 'bytes': 232592, 'sha256': '8e2e84d5196c3502c2bbeb1d2378002772bd8b145d2d27ba078114a5ceeb00bd'}, 'libutils.so': {'path': '/srv/android/asus-camera-source-abi-route/sdk37-libs/libutils.so', 'bytes': 135952, 'sha256': 'd2f70c971b5b3b5b8a17ff899deadab16fc9d0fd68511354ce16ac489160ce3c'}}}
crts={'/srv/android/asus-camera-arm32-route/abi-out/crtbegin_so.o': {'sha256': '387d779a2c1280a3eb2525977b0ab802974b60749cecb7ede9c8cc80dce0f109', 'bytes': 6620}, '/srv/android/asus-camera-arm32-route/abi-out/crtend_so.o': {'sha256': '833ab0e4dde9ccf99ab54c74c101290aafd4fa103703b6ce07c047335f48f799', 'bytes': 496}, '/srv/android/asus-camera-source-abi-route/abi-out/crtbegin_so.o': {'sha256': 'a4d1062890a43a69a9a0ec31d6b180e15bdfdbd16d1248dd38f3b0e3b2315219', 'bytes': 8504}, '/srv/android/asus-camera-source-abi-route/abi-out/crtend_so.o': {'sha256': '67526086a5d71ae54a431a6419a06c5d87cf951e4b5d58f978d4cc378b08855e', 'bytes': 912}}
adapters={'arm': {'path': '/srv/android/asus-camera-property-map-20261106/arm/libasus_camera_legacy_property_map.so', 'sha256': 'd371807e43c770306100670d2cd2dad1e6a00262b1f2483f266cbd72ecef4405'}, 'arm64': {'path': '/srv/android/asus-camera-property-map-20261106/arm64/libasus_camera_legacy_property_map.so', 'sha256': 'b5b8b38f304b51e4b79d8f46ef0eb082d80cc6b4cbeee10a53f099c80bb8d6e3'}}
def check(p,x):
 d=Path(p).read_bytes();assert hashlib.sha256(d).hexdigest()==x['sha256'];assert 'bytes' not in x or len(d)==x['bytes'];return len(d)
def read(p):
 a=['/usr/bin/readelf','-h','-d','--dyn-syms','--wide',p];p=subprocess.run(a,capture_output=True,text=True,timeout=10);assert p.returncode==0,p.stderr;return p.stdout
def sym(text):
 out=[]
 for l in text.splitlines():
  m=re.match(r'\s*\d+:\s+([0-9a-fA-F]+)\s+(\d+)\s+(\w+|<OS specific>: 10)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\S+)',l)
  if m:out.append(dict(zip(['value','size','type','binding','visibility','section','name'],m.groups())))
 return out
def needed(t):return re.findall(r'Shared library: \[(.*?)\]',t)
result={}
for arch,libs in providers.items():
 exports={};pins={};graph={}
 for n,x in libs.items():
  pins[n]={'sha256':x['sha256'],'bytes':check(x['path'],x)};t=read(x['path']);exports[n]=[v for v in sym(t) if v['section']!='UND' and v['binding'] in ['GLOBAL','WEAK'] and v['visibility'] in ['DEFAULT','PROTECTED']];graph[n]=needed(t)
 ad=adapters[arch];check(ad['path'],ad);t=read(ad['path']);direct=needed(t);resolution={}
 assert ('ELF32' if arch=='arm' else 'ELF64') in t
 for imp in [v for v in sym(t) if v['section']=='UND' and v['binding']=='GLOBAL']:
  n=imp['name'];base,sep,ver=n.partition('@');matches=[]
  for lib in direct:
   for e in exports[lib]:
    eb,es,ev=e['name'].partition('@');ev=ev.lstrip('@')
    if eb==base and (ev==ver if sep else (not es or '@@' in e['name'])):matches.append({'provider':lib,'export':e['name']})
  
  if not matches:
   print('UNMATCHED',arch,n)
   for line in read(libs['libc.so']['path']).splitlines():
    if base in line:print(line)
  assert matches,n
  resolution[n]=matches
 result[arch]={'adapter_sha256':ad['sha256'],'direct_needed':direct,'strong_imports':resolution,'providers':pins,'needed_graph':graph}
for p,x in crts.items():check(p,x)
print(json.dumps({'status':'PASS fresh reads of selected frozen direct providers/CRT and adapter ELF; exact version matching','widths':result,'crt_pins':crts,'android_execution':False},indent=2))
