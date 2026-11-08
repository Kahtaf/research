#!/usr/bin/env python3
"""Publish four source-output expectations from admitted source/resolver receipts, never image bytes."""
import argparse
import json
import os
from pathlib import Path
from admission import (GENUINE,PATHS,NEW_REMOTE,OLD_REMOTE,document,ordinary,identity,need,sha,digest,
                       validate_expectations)
from engine import bounded
import hashlib


def main():
    bounded();p=argparse.ArgumentParser(description=__doc__)
    for name in ('complete','source-binding','resolution'):
        p.add_argument('--'+name,required=True,type=Path);p.add_argument('--'+name+'-pin',required=True)
    a=p.parse_args()
    try:
        refs={name:dict(path=str(getattr(a,name).absolute()),sha256=digest(getattr(a,name+'_pin')))
              for name in ('complete','source_binding','resolution')}
        complete,source,resolution=(document(refs[k])for k in ('complete','source_binding','resolution'))
        need(complete.get('elf_init_policy_neverallows_vintf_apex_host_checks_passed') is True and
             not complete.get('fixture_only',False),'Missing genuine host completion')
        need(source['schema']=='asus-fs-source-binding/v1' and source['scope']==GENUINE and
             resolution['schema']=='asus-public-metadata-resolution/v1' and resolution['scope']==GENUINE,
             'Synthetic/unrecognized source or resolution cannot publish product expectations')
        need(resolution['source_binding_sha256']==refs['source_binding']['sha256'] and
             resolution['complete_sha256']==refs['complete']['sha256'] and resolution['build_id']==source['build_id'],
             'Source/resolution/complete group mismatch')
        capture=Path(source['capture_root'])
        need(capture.is_absolute() and not any(capture.is_relative_to(Path(root))for root in (NEW_REMOTE,OLD_REMOTE)),
             'Known synthetic fixture cannot publish production expectations')
        installed=capture/'installed';files=[]
        for path in PATHS:
            fd,before=ordinary(str(installed/path.lstrip('/')),16777216)
            try:
                h=hashlib.sha256();count=0
                while True:
                    b=os.read(fd,65536)
                    if not b:break
                    count+=len(b);h.update(b)
                need(count>0 and identity(before)==identity(os.fstat(fd)),'Changed/empty frozen public output')
                files.append(dict(path=path,bytes=count,sha256=h.hexdigest()))
            finally:os.close(fd)
        common=dict(scope=GENUINE,build_id=source['build_id'],complete_sha256=refs['complete']['sha256'],
                    source_binding_sha256=refs['source_binding']['sha256'])
        content=dict(schema='asus-public-content/v1',**common,producer='coherent-installed-public-output-capture',files=files)
        meta=dict(schema='asus-resolved-public-metadata/v1',**common,producer='fs_config+selabel_lookup',
                  **{k:resolution[k]for k in ('fs_config_cpp_sha256','product_file_contexts_sha256',
                                            'fs_config_overrides_sha256','resolver_tools','files')},
                  resolution_receipts=[refs['resolution']])
        validate_expectations(content,meta,GENUINE,source['build_id'],refs['complete']['sha256'],refs['source_binding']['sha256'],source)
        out=capture/'expectation-receipts';out.mkdir()
        for name,value in [('content',content),('metadata',meta)]:
            file=out/(name+'.json');file.write_text(json.dumps(value,indent=2)+'\n')
        print(json.dumps(dict(state='EXPECTATION_INPUTS_PUBLISHED_PARENT_ADMISSION_STILL_REQUIRED',
                              references={n:dict(path=str(out/(n+'.json')),sha256=sha((out/(n+'.json')).read_bytes()))for n in ('content','metadata')},
                              image_read=False,production_header_emitted=False),indent=2));return 0
    except (ValueError,KeyError,TypeError,OSError) as error:
        print(json.dumps(dict(state='REFUSED',error=str(error),production_header_emitted=False)));return 2


if __name__=='__main__':raise SystemExit(main())
