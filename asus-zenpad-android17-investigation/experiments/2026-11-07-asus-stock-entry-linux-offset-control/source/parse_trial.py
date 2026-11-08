"""Parse a complete parent-saved retained log; never contact hardware."""
from pathlib import Path
import argparse
import json
import re

ROOT = Path(__file__).resolve().parents[1]
RUN = json.loads((ROOT / 'evidence/identity.json').read_text())['run_uuid']
TAG = re.search(r'#define ASUS_ENTRY_TAG "(.*)"',
                (ROOT / 'source/asus_entry_tag.h').read_text()).group(1).replace(r'\n', '\n').encode()
RECORD = re.compile(
    rb'ASUS-ENTRY-DIAG ' + RUN.encode() +
    rb' magic=([0-9a-fA-F]{16}) x0=([0-9a-fA-F]{16}) el=([0-9a-fA-F]+)'
    rb' sctlr=([0-9a-fA-F]{16}) status=([0-9a-fA-F]+)(?=\r?\n|$)')


def parse(data):
    records = [dict(zip(('magic', 'x0', 'el', 'sctlr', 'status'),
                        (int(v, 16) for v in match.groups())))
               for match in RECORD.finditer(data)]
    # The expected tag is used only for matching bytes actually present in the log.
    # It is never printed as an observed tag or synthesized into the evidence.
    tag_offsets = [m.start() for m in re.finditer(re.escape(TAG), data)]
    commit = any(r['magic'] == 0x454559535452454e and r['status'] == 0xffff
                 for r in records)
    return dict(run_uuid=RUN, records=records, record_commit=commit,
                actual_complete_fresh_OEM_tag=bool(tag_offsets),
                actual_tag_offsets=tag_offsets,
                dual_positive=commit and bool(tag_offsets),
                result='DUAL_POSITIVE_STOCK_CONTROL' if commit and tag_offsets
                else 'STOP_NO_4_9_BUILD_ADMITTED',
                limitation='Log parser only. Parent must establish log provenance, complete capture, '
                'one stock trial and stock return. This is not 4.9 entry proof.')


if __name__ == '__main__':
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('complete_retained_log', type=Path)
    path = args.parse_args().complete_retained_log
    print(json.dumps(parse(path.read_bytes()), indent=2))
