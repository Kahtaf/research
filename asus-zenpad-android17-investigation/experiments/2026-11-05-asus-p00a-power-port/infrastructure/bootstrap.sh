#!/bin/bash
set -euo pipefail
exec >>/var/log/asus-build-bootstrap.log 2>&1
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y git gnupg flex bison build-essential zip curl zlib1g-dev \
  libc6-dev-i386 libncurses-dev lib32ncurses-dev x11proto-core-dev libx11-dev \
  lib32z1-dev libgl1-mesa-dev libxml2-utils xsltproc unzip fontconfig \
  python3 python3-venv python-is-python3 git-lfs rsync ccache bc device-tree-compiler \
  gcc-aarch64-linux-gnu g++-aarch64-linux-gnu lz4 libssl-dev libelf-dev \
  dwarves cpio jq repo
id android >/dev/null 2>&1 || useradd -m -s /bin/bash android
install -d -o android -g android /srv/android /srv/android/logs
if ! swapon --show=NAME --noheadings | grep -qx /swapfile; then
  if [ ! -e /swapfile ]; then
    fallocate -l 16G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
  fi
  swapon /swapfile
fi
grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >>/etc/fstab
sudo -u android git config --global user.name 'ASUS Android Port'
sudo -u android git config --global user.email 'asus-port@localhost'
sudo -u android git config --global color.ui false
sudo -u android git config --global protocol.version 2
date -u --iso-8601=seconds >/srv/android/bootstrap-complete
