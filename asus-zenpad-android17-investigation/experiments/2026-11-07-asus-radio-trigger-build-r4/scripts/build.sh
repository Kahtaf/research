#!/bin/bash
set -eo pipefail
own=/srv/android/asus-radio-trigger-build-r4
kit=/srv/android/asus-reviewed-build-kit/r9-exec-r1
record="$own/logs/combined-build"
[[ "${REVIEWED_BUILD_LOCK_FD:-}" =~ ^[0-9]+$ ]]
python3 -B - <<'LOCK'
import os,resource,json
from pathlib import Path
limits=resource.getrlimit(resource.RLIMIT_AS)
assert limits==(resource.RLIM_INFINITY,resource.RLIM_INFINITY)
Path('/srv/android/asus-radio-trigger-build-r4/attempt/native-shell-address-space.json').write_text(json.dumps({'soft':limits[0],'hard':limits[1],'unlimited_value':resource.RLIM_INFINITY})+'\n')
assert os.fstat(int(os.environ['REVIEWED_BUILD_LOCK_FD'])).st_ino == 15018964
LOCK
cd /srv/android/lineage24
unset WITH_ADB_INSECURE SELINUX_IGNORE_NEVERALLOWS SOONG_ALLOW_MISSING_DEPENDENCIES ALLOW_MISSING_DEPENDENCIES
export NINJA_ARGS="-v"
source build/envsetup.sh
lunch lineage_p00a-trunk_staging-userdebug
rc=0
m -j8 systemimage bootimage || rc=$?
python3 -B - "$own" "$rc" <<'EXIT'
from pathlib import Path
import sys,json,datetime
p=Path(sys.argv[1])/'attempt/m-exit.json'
with p.open('x') as f:json.dump({'exit':int(sys.argv[2]),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':['m','-j8','systemimage','bootimage']},f);f.write('\n')
EXIT
python3 -B "$kit/scripts/capture_build_evidence.py" "$own" selected-images "$rc"
[[ "$rc" == 0 ]] || exit "$rc"
exit 0
