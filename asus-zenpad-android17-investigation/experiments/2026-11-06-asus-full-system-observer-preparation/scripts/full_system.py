#!/usr/bin/env python3
"""Production interface: externally admitted real product only; PLAN_ONLY by default."""
import argparse
import json
from pathlib import Path
from admission import load_production
from engine import ROOT, bounded, generate, execute, headers_and_identity, pinned_runtime


def main():
    bounded()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('PLAN_ONLY','GENERATE','EXECUTE'),default='PLAN_ONLY')
    parser.add_argument('--admission', type=Path)
    parser.add_argument('--admission-pin')
    parser.add_argument('--output', type=Path)
    args=parser.parse_args()
    try:
        if args.admission is None or args.admission_pin is None:
            raise ValueError('Missing externally pinned genuine parent admission; no production input emitted')
        admitted=load_production(args.admission,args.admission_pin)
        if args.mode=='PLAN_ONLY':
            raw,original=headers_and_identity(admitted);tools=pinned_runtime()
            print(json.dumps(dict(state='ADMITTED_PLAN_ONLY',scope=admitted.scope,executed=False,
                                  production_input_emitted=False,raw_header=raw,original_header=original,
                                  expectations_sha256=admitted.expectations_sha256,
                                  immutable_tool_manifest_sha256=tools,
                                  full_SYSTEM_accepted=False,physical_GO=False),indent=2))
            return 0
        if args.output is None:
            raise ValueError('Fresh owned output directory is required')
        generated=generate(admitted,args.output)
        if args.mode=='GENERATE':
            print(json.dumps(dict(state='GENERATED_NOT_EXECUTED',generation=generated,
                                  full_SYSTEM_accepted=False,physical_GO=False),indent=2));return 0
        result=execute(admitted,args.output);print(json.dumps(result,indent=2))
        return 0 if result['filesystem_observer_passed'] else 1
    except (ValueError,KeyError,TypeError,OSError) as error:
        emitted=bool(args.output is not None and args.output.is_relative_to(ROOT/'runs') and (args.output/'expectations.h').is_file())
        print(json.dumps(dict(state='REFUSED',mode=args.mode,error=str(error),
                              production_input_emitted=emitted,full_SYSTEM_accepted=False,physical_GO=False)))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
