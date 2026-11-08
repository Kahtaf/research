# Actual pre-root-fix Android17 early runtime

Question: How far do the pinned actual BOOT ramdisk and complete SYSTEM execute on qualified Linux4.9 with actual init/policy/services and genuine APEX/crypto guards?

Status: Completed bounded attempt. First fatal blocker: linkerconfig SIGABRT on duplicate `heapprofd_client_api.so` provider. Four bootstrap APEX activations and all four BoringSSL self-tests succeeded; fresh DATA mounted. The90s run ended waiting for keystore maintenance; no product/root/physical acceptance.

Outputs: [REPORT.md](REPORT.md), [HANDOFF.json](HANDOFF.json), [actual serial](run-runtime-1/serial.log), [qualification](evidence/qualification.json), [COW audit](evidence/cow-block-audit.json), [seal](evidence/seal.json), and retained scripts in `source/`.

Remote owned output: `/srv/android/asus-r9-actual-early-runtime-20261106`. Large disks and fresh entropy remain remote; entropy values/hashes are not exported. One actual runtime; two offline preparation boots; all three allowed glue corrections used.

Continuation: Read report/handoff and preserve every attempt. Investigate the actual linkerconfig conflict in separately owned work. Any further runtime needs a new authorized unit, admitted immutable pins, improved diagnostic capture and fresh DATA. Do not rerun preparation here, reuse this DATA, change current AOSP/root/VINTF work, or transfer prior IPC proof to this run.
