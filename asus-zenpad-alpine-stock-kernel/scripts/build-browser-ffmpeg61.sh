#!/bin/sh
# Run from this spike. Mounts only public staging and this dedicated output.
set -eu
cd "$(dirname "$0")/.."
image=alpine@sha256:f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf
name=asus-ffmpeg61-build-$(date +%s)-$$
mkdir -p artifacts/browser-ffmpeg61
# Existing outputs must be archived first; build script intentionally refuses overwrite via configure/extraction results.
test ! -e artifacts/browser-ffmpeg61/ffmpeg-7.1.5
printf '%s\n' "$image" > artifacts/browser-ffmpeg61/image.txt
docker run --rm --name "$name" --cpus 4 --memory 4g --mount "type=bind,src=$PWD/sources/browser-ffmpeg61-validation,dst=/src,readonly" --mount "type=bind,src=$PWD/artifacts/browser-ffmpeg61,dst=/out" "$image" sh /src/build.sh > artifacts/browser-ffmpeg61/build.log 2>&1
