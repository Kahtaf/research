# SDK37 root-validator property paths

Question: does the final root-payload validator inspect SDK37 system_ext/product `etc/build.prop` files and reject conflicting ADB security values there?

Status: parent two-path correction, with an executable regression against the actual validator functions. Before evidence fails; after evidence passes. Tiny fixture ELF headers and APEX text exercise validator behavior only; they are not genuine product artifacts. No target code, device, network or build operation occurs.

Outputs: source/verify_root_payload.py, property-paths.patch, source-pins.json and evidence/{before,after}.json.

Continuation: apply the exact delta to the next unsealed build kit after matching its validator preimage. Do not mutate sealed kits. Actual completed-product property values, authenticated ADB, root transitions and enforcing SELinux still require genuine image/runtime validation. This does not add application SU management.
