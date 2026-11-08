# Android 17 root readiness

Question: does the actual SDK37 product include a usable root route after stock
Android's on-demand helper is no longer available?

Status: source and real build-configuration route verified; compiled-output and
runtime checks remain pending. No product changes or device operations occurred.

The actual full-r5 dumpvars include `adb_root` and `com.android.adbd`, select
`userdebug`, retain debuggability and preserve `ro.adb.secure=1`. Both declarations
of that property are 1. An initial parent check incorrectly assumed there would
be exactly one declaration; the corrected check rejects any value other than 1.

The Lineage daemon requires its `adbroot_service`, not only a debuggable build.
The product contains the real `adb_root` service. Its init script creates
`/data/adbroot`, and its constructor loads the enabled setting from there,
defaulting to disabled. The admin user's Developer Options controller changes
that setting through the system service. The service is in class main; root is
therefore not a substitute for the independent pre-framework rescue route.

After framework boot, enable **Rooted debugging** in Developer Options, then use
the authorized host's `adb root`. The daemon retains authentication, keeps UID0
and switches to the platform debug `su` domain. `adb unroot` returns it to the
ordinary shell route. This is host root access; no app-facing superuser manager
is supplied or claimed by this audit.

Important outputs:

- `evidence/actual-product-root-inputs.json`: actual dumpvars hash and checked
  module/variant/authentication inputs.
- `evidence/capture-r1.json`, `extra-source-pins.json`: source provenance and
  absence of final installed outputs at capture time.
- `source/`: exact SDK37 daemon, root service, init, policy and Settings inputs.
- `patches/require-adb-root-service.patch`: one-line addition to the future host
  validator's required packages; unapplied, with before/after hashes in
  `evidence/validator-patch.json`. The real current package list already passes
  this requirement. This guards later integration against dropping the service.

Continue after the complete product build: verify installed `adb_root`, its init
script, the platform policy and the genuine adbd APEX, plus effective generated
`ro.debuggable=1`, `ro.secure=1`, `ro.adb.secure=1`. The final host validator must
include `adb_root` among required packages. During actual first boot, require
the real service to register, enable the setting through Settings, and confirm
`adb shell id` reports UID0 after the authenticated restart. Confirm `adb unroot`
returns UID2000. Use a fresh explicit transport after each restart; do not infer
success from disconnection. Hardware operation, app superuser management and
physical root remain unproved.

Platform debug `su` is a permissive domain in the upstream userdebug policy;
this is distinct from global SELinux state, which must remain Enforcing. The
audit did not alter policy or add a permissive domain. Do not claim every domain
is enforcing based solely on `getenforce`.
