# Pending stock recovery request

Question: why did stock preflight find 20 changed bytes at para 64..84, and how
can the OEM-supported clear-BCB operation remove the stale wipe argument safely?

Status: no flash, reboot or metadata write. Android is running normally. The
command and status fields are zero; the recovery argument contains `recovery`
followed by `--wipe_data`. All other 524,268 bytes match the original normal para
backup. Keep the argument intact until the exact stock cleanup operation has
been reviewed. No raw metadata writer is supplied here.

Public software inputs and aggregate findings are here. Parent verified that
the actual stock `uncrypt` matches the saved OEM executable byte-for-byte.
Shell access was denied by SELinux; a temporary root-owned software copy was
captured and then removed. This did not alter boot metadata.

`source/read_para.py` defaults to PLAN_ONLY. Its execute mode captures two whole
read-only p12 snapshots through the pinned helper, checks exact geometry and
expected full hashes, and cleans only its owned staging. It cannot clear
metadata or flash. Raw captures/logs stay under ignored `private/`; public
receipts contain hashes only. Parent alone operates the device.

Continue with the exact stock clear-bcb audit, reviewed cleanup invocation and
fresh before/after captures. Require the original full para hash afterward,
then repeat the diagnostic preflight. No payloads need go to agents or cloud.
