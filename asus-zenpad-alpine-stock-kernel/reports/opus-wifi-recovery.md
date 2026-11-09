# Android Wi-Fi reconnect after native Alpine trial

Status: read-only evidence review, 2026-11-08. No device operations. Contains no network identities, MACs or credentials; raw captures stay in `private/live/`.

## Diagnosis (ranked by evidence)

1. **Screen-off PNO path fails on this driver, so the framework never selects a network. Strong evidence.**
   - WifiConnectivityManager logs `screenOn=false` on every restore cycle. Each cycle uses `startDisconnectedPnoScan` and never `startSingleScan`/QNS.
   - On each restart the stock supplicant logs `wlan0: Failed to schedule PNO`, then `SupplicantWifiScannerImpl: Failed to start PNO scan` and `PnoScanListener onFailure`. The `PnoScanListener onSuccess` lines only acknowledge the request; they don't mean a scan ran.
   - The boot-time connection happened with `screenOn=true` through single scan, a QNS candidate and a connect. The screen turned off a few minutes later. The link stayed up until the trial broke it, so the device never had to reconnect with the screen off until now.
   - On Android 7, the framework picks the network and the stock supplicant doesn't connect on its own. Its state goes from SCANNING to DISCONNECTED even though the scan results include the saved network.
2. **Saved-network state was not damaged. Strong negative evidence.** All saved profiles show `NETWORK_SELECTION_ENABLED` with zero disable counters. `mOperationalMode 1`. No auth failure. `list_networks` shows no DISABLED flags. A config rollback is not needed.
3. **Driver/WMT was not left broken. Moderate evidence.** After restore, scans return fresh results with the expected BSSIDs. `wlan.driver.status=ok`, and the WMT launcher PID is unchanged. The radio receives normally. Only the selection trigger is missing.
4. Airplane mode is on, but Wi-Fi is explicitly enabled. This doesn't block station mode. Low relevance.

## Why the native supplicant associated but Android doesn't

Alpine wpa_supplicant 2.11 had enabled network blocks and did its own scan and network selection. That path doesn't depend on Android's screen state or on PNO/sched_scan. Android's supplicant waits for WifiStateMachine/QNS. With the screen off, QNS only runs from PNO results, and this MT8163 driver can't schedule PNO. More disable/enable cycles repeat the same screen-off PNO path, which is why they didn't help.

## Smallest next action

Wake the screen so WifiConnectivityManager gets `screenOn=true` and falls back to periodic single scans and QNS:

```
adb shell input keyevent KEYCODE_WAKEUP
```

Wait about 15 s, then check with `wpa_cli -p /data/misc/wifi/sockets -iwlan0 status` and `getprop dhcp.wlan0.ipaddress`.

If the screen is already on and it still doesn't reconnect, the fallback is a framework-visible supplicant nudge: `wpa_cli ... reconnect`. Use `select_network <id>` only after that. Neither needs config writes.

## Guardrails for later trials

- Keep the screen awake for the whole trial and its restore, for example with `svc power stayon true`, and reset it afterwards. Add `screenOn=true` to the restore preconditions.
- In the restore check, check for association (`wpa_state=COMPLETED` plus an IPv4 lease), not just `p2p_supplicant` running and `wlan.driver.status=ok`.
- Standalone cold boot from RAM is still blocked: LK on locked fastboot refuses `fastboot boot`, and recovery is an old 4.9 diagnostic image. No boot or system partition writes were made.
