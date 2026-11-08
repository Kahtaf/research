FROM ubuntu:24.04
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    build-essential bc flex bison libssl-dev libelf-dev device-tree-compiler \
    binutils-aarch64-linux-gnu gcc-aarch64-linux-gnu cpio xz-utils file python3 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /audit
