from pathlib import Path
import json,os,hashlib,struct,stat
R=Path('/srv/android/asus-r9-actual-early-runtime-20261106');s=(R/'source/cow_verify.py').read_text().split('# Exact existing genuine xattr storage')[0].replace('os.O_RDWR','os.O_RDONLY');exec(compile(s,'cow_readonly_definitions','exec'))
d={'origin':'read-only admitted actual raw via sealed COW; no changing source/out metadata','selected_actual_files':{},'linker_metadata':{}}
for p in ['system/bin/init','system/bin/apexd','system/bin/linkerconfig','system/bin/servicemanager','system/system_ext/bin/hwservicemanager','system/bin/keystore2','system/vendor/bin/hw/android.hardware.keymaster@4.0-service','system/bin/boringssl_self_test32','system/bin/boringssl_self_test64','system/vendor/bin/boringssl_self_test32','system/vendor/bin/boringssl_self_test64','system/apex/com.android.runtime.apex','system/vendor/etc/selinux/precompiled_sepolicy','system/build.prop']:
 try:d['selected_actual_files'][p]=describe(p)
 except (KeyError,AssertionError) as ex:d['selected_actual_files'][p]={'unreadable_with_bounded_parser':type(ex).__name__}
for p in ['system/etc/linker.config.pb','system/vendor/etc/linker.config.pb','system/system_ext/etc/linker.config.pb','system/product/etc/linker.config.pb','system/etc/public.libraries.txt','system/vendor/etc/public.libraries.txt','system/etc/llndk.libraries.txt','system/etc/llndk.libraries.37.txt','system/etc/init/keystore2.rc','system/vendor/etc/init/ACCOUNT_REDACTED','system/etc/init/apexd.rc']:
 try:
  b=contents(lookup(p));assert len(b)<131072
  import re
  row={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'heapprofd_byte_offsets':[m.start() for m in re.finditer(b'heapprofd_client_api.so',b)],'ascii_strings':[x.decode('ascii') for x in re.findall(rb'[\x20-\x7e]{4,}',b)]}
  if not p.endswith('.pb'):row['text']=b.decode()
  else:row['hex']=b.hex()
  d['linker_metadata'][p]=row
 except KeyError:d['linker_metadata'][p]={'exists':False}
# Validate genuine waits in unchanged actual init.rc, plus the observer capture limitation.
init=contents(lookup('system/etc/init/hw/init.rc')).decode();d['genuine_waits_present']={x:x in init for x in ['wait_for_prop apexd.status activated','wait_for_prop keystore.module_hash.sent true','exec_start apexd-bootstrap','perform_apex_config']}
d['build_props_selected']=[x for x in contents(lookup('system/build.prop')).decode().splitlines() if x.startswith(('ro.debuggable=','ro.secure=','ro.build.type=','ro.build.version.sdk='))]
(R/'evidence/blocker-inspection.json').write_text(json.dumps(d,indent=2));print(json.dumps({'selected_file_count':len(d['selected_actual_files']),'metadata_heapprofd':{k:v.get('heapprofd_byte_offsets') for k,v in d['linker_metadata'].items()},'build_props_selected':d['build_props_selected'],'genuine_waits':d['genuine_waits_present']},indent=2))
