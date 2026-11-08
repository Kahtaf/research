# First-boot radio trigger repair

Question: will the new DATA image's persisted radio opt-in actually start the radio loader on its first boot?

Status: exact two-line device-only correction staged, not integrated. The current native build is untouched.

Actual SDK37 `system/core/init/action.cpp:211-217` checks property predicates when the post-fs-data event is matched and refuses to match a property change to an action with a nonempty event trigger. Persistent DATA properties are loaded later within that event, at `system/core/rootdir/init.rc:766`. The old radio/BT event-qualified actions therefore miss a persisted opt-in that was not already set before DATA was read. `property_service.cpp:1456-1468` loads the values and then sets `ro.persistent_properties.ready=true`.

`radio-trigger.patch` replaces only the two loader-start predicates with a property-only conjunction on actual persistent-property readiness and the existing opt-in. Directory initialization, hardware activation gates, calibration checks, service definitions, and all policies stay unchanged. It also handles opt-in changes after first boot. No ready property is forged.

Continuation: after the currently running native build is genuinely terminal, apply only against the exact before hash; use the ordinary incremental systemimage/bootimage build and refresh final installed rc/source identities. Do not mutate an active build or restart it for this change. No broad suite or additional review round is required. Physical radio operation remains unproved.
