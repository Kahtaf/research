#!/usr/bin/env python3
"""Separate host read-only e2fsck step, using only the admitted complete.raw_system.path."""
import argparse,json,os
from pathlib import Path
from admission import load_production,need,identity
from engine import ROOT,TOOLS,bounded,pinned_runtime,headers_and_identity,check_owned_output,command,environment


def main():
    bounded();p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('PLAN_ONLY','EXECUTE'),default='PLAN_ONLY')
    p.add_argument('--admission',required=True,type=Path);p.add_argument('--admission-pin',required=True)
    p.add_argument('--output',type=Path);a=p.parse_args()
    try:
        admitted=load_production(a.admission,a.admission_pin);pinned_runtime();headers_and_identity(admitted)
        cmd=[str(TOOLS/'bin/e2fsck'),'-f','-n',admitted.raw_path]
        if a.mode=='PLAN_ONLY':print(json.dumps(dict(state='PLAN_ONLY',executed=False,argv=cmd,full_SYSTEM_accepted=False)));return 0
        need(a.output is not None,'Fresh owned fsck output is required');out=check_owned_output(a.output);out.mkdir(parents=True);(out/'tmp').mkdir()
        before=identity(os.stat(admitted.raw_path,follow_symlinks=False))
        terminal=command(cmd,out/'e2fsck.log',environment(out));after=identity(os.stat(admitted.raw_path,follow_symlinks=False))
        passed=terminal==dict(exit=0,timed_out=False) and before==after
        result=dict(scope=admitted.scope,host_fsck_passed=passed,terminal=terminal,before=before,after=after,
                    admission_sha256=admitted.admission_sha256,expectations_sha256=admitted.expectations_sha256,
                    whole_image_rehashed=False,physical_GO=False,full_SYSTEM_accepted=False)
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if passed else 1
    except (ValueError,KeyError,TypeError,OSError) as e:print(json.dumps(dict(state='REFUSED',error=str(e),full_SYSTEM_accepted=False)));return 2


if __name__=='__main__':raise SystemExit(main())
