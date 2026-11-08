# Retained recovery boot errors

Question: does normal stock Android expose a bounded retained kernel log that explains the failed recovery startup?

Status: completed at 2026-11-07 04:06:31 UTC. The bounded last_kmsg capture contains 261,993 NUL bytes and a possibly corrupted RAM-console header; it provides no valid startup trace. Current AEE console is empty and the three exact pstore paths are unavailable. This does not attribute a log to the failed recovery attempt or rule out data beyond the captured prefix. Parent read-only collection from six exact kernel diagnostic paths. No block-device reads/writes, reboot, metadata clearing or service configuration changes. Existing authenticated ADB, identity-guarded root helper and shared device lock are used.

Outputs: ignored private command output; public evidence contains path availability and only narrowly selected boot-error facts. A retained log is not attributed to a specific recovery attempt without matching evidence.

Continuation: use concrete retained startup errors if available. Otherwise continue the reviewed minimal RAM USB trial rather than inferring a failure from missing logs. Do not upload private raw output to a worker or VM.
