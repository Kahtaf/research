#!/bin/bash
# This checkout was created solely for the experiment. Preserve our four edited
# files, then reconstruct every platform worktree from the already pinned HEAD.
set -euo pipefail
cd /srv/android/lineage24
backup=/srv/android/asus-android17/platform-edits-before-checkout-repair
mkdir -p "$backup"
for file in prebuilts/misc/protobuf_vendorcompat/Android.bp external/skia/Android.bp external/google-highway/Android.bp external/XMP-Toolkit-SDK/Android.bp; do
  mkdir -p "$backup/$(dirname "$file")"
  cp "$file" "$backup/$file"
done
repo init -u https://github.com/LineageOS/android.git \
  -b e4b71068f6ee045ff30e4865a8d82f4047eb78ea --depth=1 --no-clone-bundle --git-lfs
repo forall -j8 -c 'git reset --hard HEAD'
repo forall -j8 -c 'git diff --quiet HEAD -- && git diff --cached --quiet HEAD --'
repo manifest -r -o /srv/android/logs/resolved-manifest-after-repair.xml
date -u --iso-8601=seconds >/srv/android/logs/platform-checkout-repaired
