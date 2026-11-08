# ASUS P00A Linux 4.9 VINTF port

Question: What is the smallest honest device-specific legacy-kernel VINTF profile for the experimental SDK37 port using the physical 4.9.337 BMC156 kernel?

Status: incompatible; complete legacy profile not established. Corrected test input is source-proved and staged; actual baseline and explicit-FCM-7 diagnostic both exit 65. Applicable genuine 4.9 profile provenance remains missing. No accepted product matrix patch or integration.

Important outputs:

- [Report](REPORT.md) explains exact source semantics, first API 23, remaining blocker and continuation.
- [Candidate input patch](candidate/checkvintf-inputs.patch) and [command](candidate/checkvintf-command.json).
- [Kernel identity proof](evidence/kernel-identity.json), [actual baseline log](evidence/00-resolved-baseline.log), [rejected diagnostic log](evidence/01-explicit-target7.log).
- [Machine report](evidence/final-report.json) and [65-input preservation audit](evidence/final-prepost.json).

Continuation: obtain a pinned genuine applicable 4.9 base+conditional requirement source and justified retrofit target, then stage only an additive device-specific profile against the copied metadata. Do not integrate the rejected target-7 diagnostic. Do not repeat the one-time snapshot setup. The existing VM prefix is `/srv/android/asus-linux49-vintf-port-20261106` (about 1.4 MiB allocated), with copied VINTF/APEX metadata and config. The recorded check command uses one CPU, 1 GiB address-space limit and finite timeouts through `scripts/remote_run.py`; `scripts/final_verify.py` is a read/hash audit except its own-prefix receipt. No build, source/out/image mutation, device action or cloud lifecycle work was performed. Parent owns acceptance, integration, runtime and physical GO.
