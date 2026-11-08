"""Fail closed until execution-time dependency identity can be proved for r8 reuse."""
import json
from pathlib import Path
import sys

GATE=('CACHE_LINEAGE_INCOMPLETE: r8 completed commands and Ninja joins alone do not '
      'prove execution-time transitive input/graph/rsp/toolchain identity. No timestamp '
      'relaxation or forced rebuild is admitted. A reviewed lineage extension is required.')

def check_record(observed,baseline):
    """Admission predicate for a future bound lineage row; never manufactures proof."""
    required={'attempt_started_sha256','integration_sha256','native_receipt_sha256',
              'command','ninja','output_sha256','source_sha256','graph_sha256',
              'toolchain_sha256','dependencies_sha256','build_id','dependency_closure_complete'}
    if not required<=set(baseline) or baseline['dependency_closure_complete'] is not True:
        raise ValueError('Missing execution-time dependency closure')
    if not baseline['command'] or not baseline['dependencies_sha256']:
        raise ValueError('Missing completed command/dependency identity')
    for key in required-{'dependency_closure_complete'}:
        if observed.get(key)!=baseline[key]:raise ValueError('Inherited identity changed: '+key)
    if observed.get('completed') is not True or observed.get('failed_action') is not False:
        raise ValueError('Failed or pending action cannot qualify')
    return True

def require_ready(plan):
    # The actual r8 capture lacks the required input-identity receipts. This sealed
    # kit intentionally has no switch, environment override, or affirmative state.
    raise ValueError(GATE)

if __name__=='__main__':
    require_ready(json.loads((Path(sys.argv[1])/'inputs/plan.json').read_text()))
