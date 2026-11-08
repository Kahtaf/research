# Refresh the dedicated builder's existing 24-hour runtime

Question: can the dedicated labelled ASUS builder start a fresh runtime window
after all its owned build/runtime workers have completed?

Status: parent-controlled stop/start at the idle boundary. Authentication was
refreshed by the owner. Existing maxRunDuration=86400 and STOP action are retained;
restarting resets the existing relative deadline. No resource is deleted or
recreated and no labels or disks are changed.

`evidence/refresh.json` records each actual command/result. A failed or timed-out
command is not retried automatically. Inspect current API state before continuing.
Do not rerun this one-shot script. Tablet CHECK runs locally and is independent.
