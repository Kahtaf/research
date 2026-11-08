#!/bin/bash
set -euo pipefail
cd /srv/android
mkdir -p lineage24 logs
cd lineage24
repo init -u https://github.com/LineageOS/android.git \
  -b e4b71068f6ee045ff30e4865a8d82f4047eb78ea --depth=1 --no-clone-bundle --git-lfs
git -C .repo/manifests rev-parse HEAD >../logs/manifest-commit.txt
repo sync -c -j8 --no-clone-bundle --no-tags --fail-fast
repo forall -j8 -c 'git diff --quiet HEAD -- && git diff --cached --quiet HEAD --'
repo manifest -r -o ../logs/resolved-manifest.xml
date -u --iso-8601=seconds >../logs/platform-sync-complete
