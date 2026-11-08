# Retained Linux 4.9 boot trace

Question: can a diagnostic-only e9 startup logger safely produce retained RAM
that the exact stock Android `/proc/last_kmsg` reader accepts?

Status: implementation staged for parent review; all affected objects compile.
Exact normal-boot and recovery kernel bytes corroborate the reader ABI. Runtime
guards require the known reservation and valid OEM layout. Hardware retention
and physical readback remain untested. Work stayed within the 25-minute bound.

Important outputs:

- [Report and continuation](REPORT.md): compatibility evidence, safe range,
  cache/barrier reasoning, observable boundary and physical limitations.
- [Actual patch](retained-boot-trace.patch) and [opt-in config](diagnostic.config).
- `patched/`: complete resulting files; `source/`: original/source evidence.
- `evidence/stock-reader.disasm`, `layout-check.json`, `compile.json`,
  `final-logger-compile.json`, `patch-check.json`: focused verification receipts.

Continuation: parent reviews the patch, then owns one isolated build/trial.
Read the report before applying. No full Image build, image/candidate, flash,
device operation, lifecycle/process management or active/frozen source change
was performed. The existing device-operation lock remains with the parent.
