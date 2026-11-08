"""Offline assertions against exact retained 4.9 build sources, never a live probe."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1]
sections={'storage_common.c':[(182,209),(383,419),(440,469)],'f_mass_storage.c':[(776,796),(3132,3196),(3443,3483)],'configfs.c':[(270,345),(578,618)]}
texts={n:(R/'inputs'/n).read_text() for n in sections}
for needle in ['ro = curlun->initially_ro;', 'filp_open(filename, O_RDONLY | O_LARGEFILE, 0)', 'curlun->initially_ro = ro;'] :assert needle in texts['storage_common.c']
for needle in ['if (curlun->ro)', 'SS_WRITE_PROTECTED', 'config.removable = true;', '"lun.0"', 'CONFIGFS_ATTR(fsg_lun_opts_, ro)', 'DECLARE_USB_FUNCTION_INIT(mass_storage, fsg_alloc_inst, fsg_alloc)']:assert needle in texts['f_mass_storage.c']
assert "instance_name = strchr(func_name, '.');" in texts['configfs.c']
release=re.search(r'UTS_RELEASE "([^"]+)"',(R/'inputs/utsrelease.h').read_text()).group(1)
version=re.search(r'UTS_VERSION "([^"]+)"',(R/'inputs/compile.h').read_text()).group(1)
r={'status':'EXACT_BUILD_SOURCE_OFFLINE_CONTRACT','runtime_verified':False,'function':'mass_storage.ram','lun':'lun.0','set_before_file':['removable=1','cdrom=0','ro=1'],'backing_file':'/dev/probe.img','initially_ro_open':'O_RDONLY|O_LARGEFILE','do_write_when_ro':'SS_WRITE_PROTECTED','expected_udc':'musb-hdrc','UDC_expectation_origin':'retained Android17 probe/init.rc; not a new observation','expected_uname':{'sysname':'Linux','release':release,'version':version,'machine':'aarch64'},'excerpts':{n:{'sha256':hashlib.sha256((R/'inputs'/n).read_bytes()).hexdigest(),'lines':[{'start':a,'end':b,'text':'\n'.join(texts[n].splitlines()[a-1:b])} for a,b in ranges]} for n,ranges in sections.items()}}
(R/'evidence/source-contract.json').write_text(json.dumps(r,indent=2)+'\n')
print('exact retained driver source contract PASS')
