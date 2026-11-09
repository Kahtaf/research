#!/usr/bin/env python3
"""Accept one successful stock module-init ioctl plus a live WMT class."""
from pathlib import Path
import re, sys

def validate_trace(trace):
    lines=trace.splitlines()
    requests=[(index,line) for index,line in enumerate(lines)
              if re.search(r'\bioctl\([^,\n]+,\s*0x80047704\s*,',line)]
    if len(requests)!=1:
        raise SystemExit(f'WMT_NOT_READY module-init request count={len(requests)}')
    index,line=requests[0]
    if '<unfinished ...>' in line:
        prefix=re.match(r'^\s*(?:\[pid\s+)?(\d+)',line)
        if prefix is None:
            raise SystemExit('WMT_NOT_READY unfinished request without process identity')
        pid=prefix.group(1)
        resumed=[item for item in lines[index+1:]
                 if re.match(r'^\s*(?:\[pid\s+)?'+pid+r'(?:\]|\s)',item)
                 and '<... ioctl resumed>' in item]
        if len(resumed)!=1:
            raise SystemExit('WMT_NOT_READY missing or ambiguous ioctl completion')
        line=resumed[0]
    if not re.search(r'=\s*0(?:\s|$)',line):
        raise SystemExit('WMT_NOT_READY module-init ioctl did not return zero')


def main():
    validate_trace(Path(sys.argv[1]).read_text())
    classes=list(Path('/sys/class').glob('*/stpwmt/dev'))
    if len(classes)!=1:
        raise SystemExit(f'WMT_NOT_READY stpwmt class count={len(classes)}')
    numbers=classes[0].read_text().strip()
    if not re.fullmatch(r'[0-9]+:[0-9]+',numbers):
        raise SystemExit('WMT_NOT_READY invalid stpwmt device numbers')
    print('WMT_MODULE_INIT_VERIFIED stpwmt='+numbers)

if __name__=='__main__':main()
