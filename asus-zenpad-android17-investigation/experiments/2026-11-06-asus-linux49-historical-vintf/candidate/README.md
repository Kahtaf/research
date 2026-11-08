# Staged integration

Apply `integration.patch` at the Android source root only during parent-owned integration. It adds one device-local matrix/kernel-config module, preserves the full historical P HAL catalog and all genuine P kernel predicates, installs the extra matrix, and explicitly declares the retrofit target/kernel FCM 3. Original shipping API remains 23. No existing SDK37 matrix or HAL declaration is removed.

The exact copied config and full runtime release pass the actual SDK37 checker. Q is a rejected diagnostic with real config gaps. See `../REPORT.md` and `../evidence/constraint-audit.json` before integration. Missing feature declarations and runtime behavior remain explicit; host compatibility is not functional acceptance. No kernel-source/config patch is needed for the tested P profile. Do not apply this patch during the concurrent root-fix build.
