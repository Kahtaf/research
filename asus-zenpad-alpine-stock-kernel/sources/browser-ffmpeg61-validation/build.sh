#!/bin/sh
set -eux
apk add --no-cache build-base pkgconf python3
cd /out
apk info -v > builder-packages.txt
cc --version > compiler.txt
uname -a > builder-kernel.txt
printf '%s  %s\n' de668509caf9e35e3cd162473441fdb29538c6d96ed080292b3cf9e6fc5d558f /src/input/ffmpeg-7.1.5.tar.xz | sha256sum -c -
tar xf /src/input/ffmpeg-7.1.5.tar.xz
cd ffmpeg-7.1.5
./configure --prefix=/opt/asus-ffmpeg61 --enable-shared --disable-static --enable-pic --disable-autodetect --enable-pthreads --disable-programs --disable-doc --disable-avdevice --disable-avformat --disable-avfilter --disable-swresample --disable-swscale --disable-postproc --disable-network --disable-iconv --disable-everything --enable-decoder=aac,h264,hevc,vp8,vp9,vp6f --enable-parser=aac,h264,hevc,vp8,vp9 --extra-ldflags='-Wl,--as-needed -Wl,-z,now -Wl,-z,relro'
make -j4
mkdir -p /out/lib /out/license
cp libavcodec/libavcodec.so.61 /out/lib/
cp libavutil/libavutil.so.59 /out/lib/
cp COPYING.LGPLv2.1 LICENSE.md /out/license/
cp config.h config_components.h ffbuild/config.log ffbuild/config.mak /out/
sha256sum /out/lib/* > /out/SHA256SUMS
apk add --no-cache ffmpeg7
ffmpeg -version > /out/reference-version.txt
ffmpeg -v error -i /src/input/media-video-only.mp4 -map 0:v:0 -c copy -bsf:v h264_mp4toannexb -f h264 /out/fixture.h264
ffmpeg -v error -i /src/input/media-with-audio.mp4 -map 0:a:0 -c copy -f adts /out/fixture.aac
cc -I/out/ffmpeg-7.1.5 /src/harness.c -ldl -o /out/harness
LD_LIBRARY_PATH=/out/lib /out/harness /out/fixture.h264 /out/fixture.aac > /out/harness.txt
ffmpeg -v error -i /out/fixture.h264 -map 0:v:0 -f framemd5 /out/reference-video.framemd5
ffmpeg -v error -i /out/fixture.aac -map 0:a:0 -c:a pcm_s16le -f s16le /out/reference-audio.pcm
python3 /src/gates.py
