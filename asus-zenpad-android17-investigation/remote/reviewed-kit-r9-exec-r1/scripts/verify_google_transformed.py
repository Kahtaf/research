"""The two unsigned Google outputs are checked independently of 30 exact files."""
import hashlib
import struct
import subprocess
import zipfile
from pathlib import Path
from integrate import need, sha
from verify_product_r3 import installed, elf

def allocated_sections(path):
    data=path.read_bytes()
    need(len(data)>=64 and data[:6]==b'\x7fELF\x02\x01','Invalid JNI ELF section table')
    offset=struct.unpack_from('<Q',data,40)[0]
    width,count,names=struct.unpack_from('<HHH',data,58)
    need(width==64 and 0<names<count and offset+width*count<=len(data),'Invalid JNI section bounds')
    rows=[struct.unpack_from('<IIQQQQIIQQ',data,offset+n*width) for n in range(count)]
    strings=rows[names];table=data[strings[4]:strings[4]+strings[5]];result={}
    for name,kind,flags,address,start,size,link,info,align,entrysize in rows:
        if not flags&2:continue
        need(name<len(table) and b'\0' in table[name:],'Invalid JNI section name')
        label=table[name:].split(b'\0',1)[0].decode()
        need(label not in result,'Duplicate allocated JNI section')
        need(kind==8 or start+size<=len(data),'Invalid JNI allocated section bounds')
        result[label]={'type':kind,'flags':flags,'address':address,'size':size,'sha256':None if kind==8 else hashlib.sha256(data[start:start+size]).hexdigest()}
    need('.text' in result and result['.text']['size']>0,'JNI ELF has no executable text')
    return result

def verify(manifest, product, raw, debugfs, readelf, aosp):
    payload=manifest['payload_members']
    targets={p:v for p,v in payload.items() if p.endswith(('.jar','.so'))}
    need(len(payload)==32 and set(targets)=={
        'system/product/framework/com.google.android.dialer.support.jar',
        'system/product/lib64/libjni_latinimegoogle.so'},'Google 32-payload selection changed')
    result=[]
    for relative,source in targets.items():
        path=product/relative
        row=installed(product,relative,raw,debugfs)
        row['release_source']=source
        origins=[rel for rel,entry in manifest['outputs'].items() if entry.get('zip_member')==relative and entry['sha256']==source['sha256']]
        need(len(origins)==1,'Ambiguous Google source provenance')
        original=aosp/'vendor/gapps'/origins[0]
        need(original.is_file() and sha(original)==source['sha256'],'Pinned Google source changed: '+relative)
        row['source_path']=str(original)
        if relative.endswith('.so'):
            elf(path)
            source_sections=allocated_sections(original)
            need(allocated_sections(path)==source_sections,'Google JNI executable/data differs from release')
            row['allocated_sections']=source_sections
            proc=subprocess.run([str(readelf),'-h','-l','-d',str(path)],capture_output=True,text=True)
            need(proc.returncode==0 and 'DYNAMIC' in proc.stdout and 'NEEDED' in proc.stdout,'Google JNI has no real dynamic-link metadata')
            need('libc.so' in proc.stdout,'Google JNI libc dependency missing')
            row['elf_metadata']=proc.stdout
        else:
            with zipfile.ZipFile(path) as archive:
                need(archive.testzip() is None,'Google JAR CRC failure')
                entries=archive.namelist()
                need(len(entries)==len(set(entries)),'Duplicate Google JAR member')
                executable=[x for x in entries if x.endswith('.dex') or x.endswith('.class')]
                with zipfile.ZipFile(original) as release:
                    original_code={name:hashlib.sha256(release.read(name)).hexdigest() for name in release.namelist() if name.endswith(('.dex','.class'))}
                need(original_code,'Google source JAR has no bytecode')
                if executable:
                    actual_code={name:hashlib.sha256(archive.read(name)).hexdigest() for name in executable}
                    need(actual_code==original_code,'Google JAR bytecode differs from release')
                    row['release_bytecode_unchanged']=True
                else:
                    # Dexpreopt can remove dex from an installed jar. Require its
                    # actual companion outputs in SYSTEM; runtime remains unproved.
                    row['dexpreopt_companions']=[]
                    for ext in ['.odex','.vdex']:
                        rel=str(Path(relative).parent/'oat/arm64'/(Path(relative).stem+ext))
                        compiled=product/rel
                        row['dexpreopt_companions'].append(installed(product,rel,raw,debugfs))
                        if ext=='.odex':elf(compiled)
                        else:
                            with compiled.open('rb') as f:need(f.read(4)==b'vdex','Invalid Google dexpreopt VDEX')
                    row['release_bytecode_unchanged']=None
                for name in executable:
                    data=archive.read(name)
                    if name.endswith('.dex'):
                        need(len(data)>=112 and data[:4]==b'dex\n' and struct.unpack_from('<I',data,32)[0]==len(data),'Invalid Google JAR dex')
                    else:need(data[:4]==bytes.fromhex('cafebabe'),'Invalid Google JAR class')
                row['jar_members']=entries
        row['release_bytes_unchanged']=row['sha256']==source['sha256']
        result.append(row)
    return {'checked':result,'unsigned_outputs':2,'final_system_bytes_checked':True,'runtime_validated':False}
