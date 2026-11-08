# Stock Wi-Fi ADB persistence

Question: does stock Android save `persist.adb.tcp.port=5555` to its actual
property file, so recovery probes can reconnect without USB?

Status: saved configuration confirmed. The normal Enforcing shell showed a blank
value, while temporary root saw5555 before this operation and the exact root-owned
0600 property file contains four5555 bytes. A blank shell read did not prove loss
of persistence. The only configuration operation set the same existing value. The transient
listener remains 5555 and authenticated. No ADB server reset, boot-image edit,
root daemon, unauthenticated debugging, or recovery reboot is part of this work.

Parent uses the existing identity-checked temporary-root helper, preserves
Enforcing on exit, and inspects only this named port configuration file. A
successful immediate set/read is not a persistence claim. The next actual
recovery probe can establish behavior across reboot without an extra test boot.

Continuation: read the actual evidence before choosing a reconnect method.
Leave the two delegated kernel/startup scopes independent.

Actual receipt: `evidence/persistence.json`; root output: `evidence/root-setting.txt`. The next physical diagnostic will first use host-side TCP reconnect without another device tcpip reset, to observe the actual post-boot listener.
