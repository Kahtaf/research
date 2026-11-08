#!/bin/sh
set -eu
spike_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$spike_dir/debloat.py" restore --run "$spike_dir/runs/20261104T211525.925216Z"
