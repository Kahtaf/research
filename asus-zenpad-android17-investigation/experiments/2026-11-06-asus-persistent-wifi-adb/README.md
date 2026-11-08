# Persistent authenticated Wi-Fi ADB

Question: can one brief USB connection restore the user's preferred Wi-Fi transport and keep it available after stock Android restarts?

Status: parent enabling the existing authenticated ADB endpoint. No recovery/BOOT/SYSTEM/userdata image operation. The USB wait is bounded; only the exact ASUS serial is accepted. TCP ADB must still report secure ADB and the original stock identity.

Outputs: private command receipts and a public connection outcome. No credential or private calibration access.

Continuation: use the authenticated Wi-Fi endpoint for subsequent transfers and recovery-only flashing, without requiring a physical USB pin. Recovery itself currently has no Wi-Fi, so its report still needs USB. Stock persistence does not imply Wi-Fi is available in experimental Android17 or recovery.
