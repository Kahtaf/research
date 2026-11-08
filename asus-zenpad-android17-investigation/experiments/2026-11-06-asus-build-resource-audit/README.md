# ASUS builder resource and cleanup audit

Question: do all created resources remain labeled and covered by cleanup while the Android17 build runs?

Status: read-only live API audit passed. VM,600GBboot disk and regional reserved IPv4 all carry experiment/owner/purpose/creator/expiry labels. The VM remains RUNNING with24hour max duration and STOP action. No cloud mutation or teardown was executed.

Finding fixed: the original teardown.sh removed VM/disk but omitted the subsequently reserved static address. The script now checks all three experiment labels and exact single attached disk, removes the reserved address after VM deletion, and lists all three resource kinds. Existing script still represents explicit destructive teardown; it was not run. Bash syntax passed; exact read-only attachment-query output was independently verified. Preimage/postimage are retained in evidence. No synthetic deletion test or cloud lifecycle action is claimed.

Outputs: evidence/{instance,disk,address,attachment,teardown-attachment-query}.json and teardown.before.sh/teardown.after.sh. Authoritative cleanup script remains ../2026-11-05-asus-p00a-power-port/infrastructure/teardown.sh. Preserve cloud build outputs until the user goal and export requirements are finished. Expiry labels and automatic STOP do not delete disk/address resources.

Continuation: continue r8/runtime work. At eventual explicit teardown, use the reviewed script only after required outputs are exported. This audit created no resources and changed no runtime scheduling.
