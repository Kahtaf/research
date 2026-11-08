#!/bin/bash
# Durable, one-shot continuation. Blocks on the existing build lock, never polls.
set -euo pipefail
root=/srv/android/asus-build-continuation
prior=/srv/android/asus-device-product/logs/full-build-r5
record="$root/logs/continue-after-r5"
exec 8>"$root/logs/continuation.lock"
flock -n 8
[[ ! -e "$record.started" ]]
date -u --iso-8601=seconds > "$record.started"
finish() {
    result=$?
    trap - EXIT
    printf '%s\n' "$result" > "$record.exit-code"
    date -u --iso-8601=seconds > "$record.finished"
    exit "$result"
}
trap finish EXIT
echo 'Waiting for original r5 full-product lock.'
exec 9>/srv/android/asus-device-product/logs/full-product-build.lock
flock 9
[[ -s "$prior.finished" && -s "$prior.exit-code" ]]
if [[ "$(cat "$prior.exit-code")" != 0 || ! -s "$prior.complete" ]]; then
    echo 'r5 failed: inspect its original log before retrying. No integration performed.'
    exit 20
fi
cd "$root"
sha256sum --check evidence/queued-inputs.sha256
[[ ! -e /srv/android/asus-device-product/logs/full-build-r6.started ]]
# The integration/build each reacquire the same lock and fail closed on conflicts.
flock -u 9
exec 9>&-
python3 scripts/integrate_combined.py --apply
bash scripts/build_full_combined.sh r6 > /srv/android/asus-device-product/logs/full-build-r6.log 2>&1 &
child=$!
printf '%s\n' "$child" > /srv/android/asus-device-product/logs/full-build-r6.pid
wait "$child"
date -u --iso-8601=seconds > "$record.complete"
