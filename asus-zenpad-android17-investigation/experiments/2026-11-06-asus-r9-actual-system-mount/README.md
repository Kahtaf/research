# Actual r9 SYSTEM Linux 4.9 mount

Question: Is the actual completed Android 17 SYSTEM raw artifact filesystem-readable with the retained genuine Linux 4.9 virtual kernel?

Status: Complete: actual SYSTEM read-only mount/read/xattr/unmount PASS on pinned virtual Linux 4.9.337; parent explicitly admitted this narrow artifact test. Original r9 overall exit 1 and actual ro.debuggable=0 root-check failure remain failures.

Outputs: [REPORT.md](REPORT.md), [result.json](evidence/result.json), [serial.log](evidence/serial.log), observed metadata, commands, pins, scripts and guest source are retained here. VM writes are restricted to `/srv/android/asus-r9-actual-system-mount-20261106` (128 MiB maximum); the 3,753,902,080-byte raw is reused read-only in place.

Continuation: Read REPORT.md and result evidence when complete. This test does not replace the production observer admission gate or qualify Android init/services, physical hardware, product acceptance or flashing. Preserve all prior fixtures and this run; do not rerun over existing output.
