#!/bin/bash
set -eo pipefail
cd /srv/android/lineage24
unset WITH_ADB_INSECURE SELINUX_IGNORE_NEVERALLOWS SOONG_ALLOW_MISSING_DEPENDENCIES ALLOW_MISSING_DEPENDENCIES
export NINJA_ARGS="-v"
python3 -B - <<'PY'
import os,resource
assert resource.getrlimit(resource.RLIMIT_AS)==(resource.RLIM_INFINITY,resource.RLIM_INFINITY)
assert os.fstat(int(os.environ['REVIEWED_BUILD_LOCK_FD'])).st_ino==15018964
PY
source build/envsetup.sh
lunch lineage_p00a-trunk_staging-userdebug
rc=0
m -j8 systemimage || rc=$?
python3 -B - "$rc" <<'PY'
from pathlib import Path
import datetime,json,sys
p=Path('/srv/android/asus-bpf-name-product-build-20261107/evidence/m-exit.json')
with p.open('x') as f: json.dump({'exit':int(sys.argv[1]),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':['m','-j8','systemimage']},f);f.write('\n')
PY
exit "$rc"
