"""Validate exact final zRAM label using real merged contexts and compiled policy."""
import ctypes
import ctypes.util
from pathlib import Path
import stat
import subprocess
from integrate import need,sha

EXPECTED='u:object_r:swap_block_device:s0'

def lookup(contexts,path,mode):
    lib=ctypes.CDLL(ctypes.util.find_library('selinux') or 'libselinux.so.1',use_errno=True)
    class Opt(ctypes.Structure):_fields_=[('type',ctypes.c_int),('value',ctypes.c_char_p)]
    # SELABEL_CTX_FILE=0, SELABEL_OPT_PATH=3.
    lib.selabel_open.argtypes=[ctypes.c_uint,ctypes.POINTER(Opt),ctypes.c_uint];lib.selabel_open.restype=ctypes.c_void_p
    lib.selabel_lookup_raw.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_char_p),ctypes.c_char_p,ctypes.c_int]
    lib.selabel_close.argtypes=[ctypes.c_void_p];lib.freecon.argtypes=[ctypes.c_char_p]
    opts=(Opt*1)(Opt(3,str(contexts).encode()));handle=lib.selabel_open(0,opts,1)
    need(bool(handle),'Genuine libselinux context open failed')
    context=ctypes.c_char_p()
    try:
        need(lib.selabel_lookup_raw(handle,ctypes.byref(context),path.encode(),mode)==0,'Genuine SELinux lookup failed: '+path)
        result=context.value.decode();lib.freecon(context);return result
    finally:lib.selabel_close(handle)

def verify(partition,policy,tool,output):
    output.mkdir();contexts=[]
    vendor=partition['vendor']/'etc/selinux/vendor_file_contexts'
    entries=[l.split() for l in vendor.read_text().splitlines() if l.strip() and not l.lstrip().startswith('#')]
    need([x for x in entries if x[0]=='/dev/block/zram0']==[['/dev/block/zram0',EXPECTED]],'Final vendor contexts lack exact reviewed zRAM entry')
    for label,base in partition.items():
        prefix='plat' if label=='system' else label
        contexts.append(base/('etc/selinux/'+prefix+'_file_contexts'))
    combined=output/'merged_file_contexts';combined.write_bytes(b'\n'.join(p.read_bytes() for p in contexts)+b'\n')
    args=[str(tool),'-p',str(policy),'-o',str(output/'merged_file_contexts.bin'),str(combined)]
    r=subprocess.run(args,capture_output=True,text=True)
    (output/'compile.log').write_text(r.stdout+r.stderr)
    need(r.returncode==0,'Merged contexts invalid against real compiled policy')
    value=lookup(combined,'/dev/block/zram0',stat.S_IFBLK)
    need(value==EXPECTED,'Actual selected zRAM context differs: '+value)
    return dict(selected_context=value,policy_sha256=sha(policy),context_inputs={str(p):sha(p) for p in contexts},merged_contexts_sha256=sha(combined),context_compiler_sha256=sha(tool),argv=args,exit_code=r.returncode,allow_or_permissive_changes=False,physical_activation_verified=False)
