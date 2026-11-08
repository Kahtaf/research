#!/bin/bash
set -eo pipefail
own=/srv/android/asus-combined-build-execution-r2
kit=/srv/android/asus-reviewed-build-kit/r9-exec-r1
record="$own/logs/combined-build"
[[ "${REVIEWED_BUILD_LOCK_FD:-}" =~ ^[0-9]+$ ]]
python3 -B - <<'LOCK'
import os
assert os.fstat(int(os.environ['REVIEWED_BUILD_LOCK_FD'])).st_ino == 15018964
LOCK
cd /srv/android/lineage24
unset WITH_ADB_INSECURE SELINUX_IGNORE_NEVERALLOWS SOONG_ALLOW_MISSING_DEPENDENCIES ALLOW_MISSING_DEPENDENCIES
export NINJA_ARGS="-v"
source build/envsetup.sh
lunch lineage_p00a-trunk_staging-userdebug
rc=0
m -j4 systemimage bootimage || rc=$?
python3 -B "$kit/scripts/capture_build_evidence.py" "$own" selected-images "$rc"
[[ "$rc" == 0 ]] || exit "$rc"
exit 0
