# USB retained-log collector

Question: retrieve the completed recovery trial log through working USB without relying on the offline TCP endpoint.

Status: one transport specialization of the existing exact-device temporary-root helper, legacy shell boundary and complete log collector. No recovery entry or image write. Original inputs are unchanged. The preceding TCP collection failed at get-serialno before any root command; preserved evidence remains in the orchestration spike.

Outputs: scripts/root_shell_usb.py, scripts/usb-adb, scripts/collect.py, and evidence/source-pins.json. Raw collected data stays in ignored artifacts/private. Continuation: run scripts/collect.py with the verified new stock boot UUID and existing trial receipt; inspect fresh completion, enforcing restoration and retained markers.

## Actual capture

USB collection exited 0 on stock boot `07b983d4-92fd-4abd-ad7f-4afb6e017571`; complete 523,020 bytes SHA-256 `bfe6ab5610e470fcc3fd814f606469d4b2230f4e6235cfbd187e188a67084b8f`. No v2 checkpoint. Temporary root helper exited 0 and verified Enforcing restoration. No image write or reboot.
