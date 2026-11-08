# ASUS stock access over authenticated Wi-Fi ADB

Question: can the port retain exact-device stock access despite the tablet's
finicky USB connector?

Status: the private LAN ADB endpoint authenticated with the existing host key;
serial, device, SDK, fingerprint, secure ADB and Enforcing state matched stock.
Parent validation of the separate on-demand root helper follows. The original
USB helper is unchanged. No OS block writer or permanent root daemon is added.

`scripts/root_shell_wifi.py` accepts trusted parent shell commands on stdin,
pins the exact LAN endpoint and hardware identity, checks the original root
binary hash, and restores Enforcing after the session. A mandatory per-call
nonce record prevents the exit trap from masking a failed command. This helper
carries text only; binary exports use separate binary-safe ADB transfers.

Endpoint: `IP_REDACTED:5555`, on the user's private LAN. The parent enabled
the stock authenticated ADB listener for this work. Stop it after use with
`adb -s IP_REDACTED:5555 usb`, then verify TCP access is gone. No GCP firewall,
public listener, new host key or device authorization key was created.

All device operations remain parent-owned. Do not run concurrently with another
root/flash/backup session. This is stock SDK24 access, not Android17 root proof.
