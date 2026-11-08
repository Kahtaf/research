#!/usr/bin/env python3
"""Final host checks of completed product bytes, never a device operation."""
import pathlib,subprocess,hashlib,json,sys,struct,shutil,re
from verify_google_payload import verify as verify_google
R=pathlib.Path('/srv/android/asus-build-continuation');A=pathlib.Path('/srv/android/lineage24');B=A/'out/host/linux-x86/bin';P=A/'out/target/product/p00a'
revision=sys.argv[1];assert re.fullmatch(r'r[0-9]+',revision)
O=R/('full-validation-'+revision);O.mkdir();records=[]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
def run(args):
    name='command-'+str(len(records));log=O/(name+'.log')
    with log.open('xb') as f:p=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT)
    records.append({'argv':list(map(str,args)),'exit':p.returncode,'log':str(log),'log_sha256':sha(log)});(O/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
    assert p.returncode==0,(args,p.returncode,log)
image=P/'system.img';image_stat=image.stat();build=json.loads(pathlib.Path('/srv/android/asus-device-product/logs/full-build-'+revision+'.images.json').read_text())
integration=json.loads((R/'evidence/active-integration.json').read_text())
config=pathlib.Path(integration['generated_defconfig']['path']);kernel_release=pathlib.Path(integration['kernel_release']['path'])
assert sha(config)==integration['generated_defconfig']['sha256'] and sha(kernel_release)==integration['kernel_release']['sha256']
assert sha(A/'device/asus/p00a/prebuilt/Image.gz-dtb')==integration['kernel_sha256']
assert sha(image)==build['system']['sha256']
raw=O/'system-partition.raw'
with image.open('rb') as f:magic=f.read(4)
if magic==bytes.fromhex('3aff26ed'):run([B/'simg2img',image,raw])
else:run(['cp','--reflink=auto',image,raw])
assert raw.stat().st_size==build['system']['expanded_bytes']<=3753902080
with raw.open('r+b') as f:f.truncate(3753902080)
run([B/'e2fsck','-f','-n',raw])
manifest=R/'inputs/google-inline-source-manifest.json';assert sha(manifest)=='12b6926954dd58f924237d36471e60e72b654e97844ff2560f9f5a9629f05b96'
google=verify_google(json.loads(manifest.read_text()),P,raw,B/'debugfs');(O/'google-signed-bytes.json').write_text(json.dumps(google,indent=2)+'\n')
# Match the SDK37 target-files checker: host APEX extraction includes APEX VINTF.
# This is metadata validation, never an assertion of target apexd execution.
apex=O/'apex';apex.mkdir();odm=P/'system/vendor/odm'
if not odm.exists():odm=O/'empty-odm';odm.mkdir()
dirmap={'/system':P/'system','/vendor':P/'system/vendor','/product':P/'system/product','/system_ext':P/'system/system_ext','/odm':odm,'/apex':apex}
command=[B/'apexd_host','--tool_path',A/'out/host/linux-x86','--apex_path',apex]
for part,path in dirmap.items():
    if part!='/apex':command+=['--'+part[1:]+'_path',path]
run(command)
command=[B/'checkvintf','--check-compat']
for part,path in dirmap.items():command+=['--dirmap',part+':'+str(path)]
command+=['--kernel',str(kernel_release)+':'+str(config),'--property','ro.product.first_api_level=23','--property','ro.boot.product.hardware.sku=','--property','ro.boot.product.vendor.sku=']
run(command)
after=image.stat();assert (image_stat.st_size,image_stat.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
raw_sha=sha(raw);raw.chmod(0o444)
report={'source_system_image_sha256':build['system']['sha256'],'raw_system_partition_path':str(raw),'raw_system_partition_bytes':raw.stat().st_size,'raw_system_partition_sha256':raw_sha,'writer_must_materialize_all_zero_ranges':True,'host_ext4_check_passed':True,'google_signed_and_metadata_files_match':len(google['checked']),'vintf_including_apex_metadata_and_kernel_checked':True,'kernel_config_sha256':sha(config),'integration_receipt_sha256':sha(R/'evidence/active-integration.json'),'physical_boot_validated':False,'target_apex_activation_validated':False}
(O/'complete.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
