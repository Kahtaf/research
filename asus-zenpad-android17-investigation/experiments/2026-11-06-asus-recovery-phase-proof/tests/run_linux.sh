#!/bin/sh
set -eu
cd /work
export SANITIZER_CGROUP=1
export ASAN_OPTIONS=detect_leaks=1:halt_on_error=1
export UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1
cat /sys/fs/cgroup/memory.max > evidence/linux-memory-limit.txt
cat /sys/fs/cgroup/cpuset.cpus.effective > evidence/linux-cpus.txt
cat /sys/fs/cgroup/cpu.max > evidence/linux-cpu-quota.txt
cc -std=c11 -D_GNU_SOURCE -O1 -g -fsanitize=address,undefined,bounds -fno-sanitize-recover=all -fstack-protector-strong tests/session.c -o tests/session-after
cc -std=c11 -D_GNU_SOURCE -O1 -g -fsanitize=address,undefined,bounds -fno-sanitize-recover=all -fstack-protector-strong -DBASELINE tests/session.c -o tests/session-before
python3 -B tests/test_sessions.py > evidence/linux-sessions-after.stdout 2> evidence/linux-sessions-after.stderr
python3 -B tests/test_sessions.py --baseline > evidence/linux-sessions-before.stdout 2> evidence/linux-sessions-before.stderr
cc -std=c11 -D_GNU_SOURCE -O1 -g -fsanitize=address,undefined,bounds -fno-sanitize-recover=all tests/guard.c -o tests/guard
python3 -B tests/test_guard.py > evidence/linux-guard.stdout 2> evidence/linux-guard.stderr
cc -std=c11 -D_GNU_SOURCE -O1 -g -fsanitize=address,undefined,bounds -fno-sanitize-recover=all tests/handoff.c -o tests/handoff
python3 -B tests/test_handoff.py > evidence/linux-handoff.stdout 2> evidence/linux-handoff.stderr
python3 -B tests/generate_bodies.py
cc -std=c11 -O1 -g -fsanitize=address,undefined,bounds -fno-sanitize-recover=all -Isource tests/model.c -o tests/model-after
cc -std=c11 -O1 -g -fsanitize=address,undefined,bounds -fno-sanitize-recover=all -DBASELINE -Isource tests/model.c -o tests/model-before
python3 -B tests/test_model.py > evidence/full-geometry-counts.json
make -C context/libsepol/src libsepol.a DISABLE_CIL=y CC=cc CFLAGS='-O1 -Wno-error' -j1 > evidence/linux-policy-build.stdout 2> evidence/linux-policy-build.stderr
cc -O1 -Icontext/libsepol/include tests/policy_reachability.c context/libsepol/src/libsepol.a -o tests/policy-reachability
./tests/policy-reachability context/restore-sepolicy > evidence/policy-reachability.txt
cat /sys/fs/cgroup/memory.peak > evidence/linux-memory-peak.txt
