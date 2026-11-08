#!/usr/bin/env python3
import io,pathlib,subprocess,tarfile,sys
from remote import SSH
r=pathlib.Path(__file__).resolve().parents[1];src=r/'staged/device/asus/p00a/radio';b=io.BytesIO()
with tarfile.open(fileobj=b,mode='w',format=tarfile.GNU_FORMAT) as t:
 for p in sorted(src.rglob('*')):
  if p.is_file():t.add(p,arcname='userspace/'+str(p.relative_to(src)),recursive=False)
subprocess.run(SSH+['tar -x -C /srv/android/asus-radio-kernel-port'],input=b.getvalue(),check=True)
cmd='''cd /srv/android/asus-radio-kernel-port && mkdir -p userspace/bin && {
set -e
aarch64-linux-gnu-gcc --version | head -1
aarch64-linux-gnu-gcc -std=c11 -Wall -Wextra -Werror -O2 -static -Wl,--build-id=sha1 -o userspace/bin/p00a-wmt-arm64 userspace/src/p00a_wmt.c userspace/src/wmt_protocol.c userspace/src/bt_record.c
gcc -std=c11 -Wall -Wextra -Werror -O2 -o userspace/bin/p00a-wmt-host userspace/src/p00a_wmt.c userspace/src/wmt_protocol.c userspace/src/bt_record.c
file userspace/bin/p00a-wmt-arm64
aarch64-linux-gnu-readelf -h userspace/bin/p00a-wmt-arm64
sha256sum userspace/bin/p00a-wmt-arm64
if userspace/bin/p00a-wmt-host --load; then exit 5; fi
if userspace/bin/p00a-wmt-host --serve; then exit 6; fi
if userspace/bin/p00a-wmt-host --unknown; then exit 7; fi
command -v qemu-aarch64 || true
} > logs/userspace-build.log 2>&1; result=$?; echo $result > logs/userspace-build.exit; cat logs/userspace-build.log; exit $result'''
sys.exit(subprocess.call(SSH+[cmd]))
