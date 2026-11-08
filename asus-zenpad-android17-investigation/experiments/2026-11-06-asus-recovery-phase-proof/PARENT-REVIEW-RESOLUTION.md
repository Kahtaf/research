# Parent review resolution: narrow source acceptance only

This addendum supersedes the unqualified detection/replacement wording in the original REPORT.md and HANDOFF.json. Original reports, reviewed source, patch, policy, helper and frozen image are preserved byte-for-byte.

Persistent changed p10 bytes refuse a later full proof only when that proof actually reads the changed bytes. Changes after the corresponding final read, or restored before a later observation, may escape the samples and commit may succeed. The fixed-graph no-writer premise must remain true throughout all hash reads and through the terminal receipt. Metadata validation is never a content-change detector or continuous observation.

Descriptor validation detects closed descriptors and replacements that change the checked node/path/label/geometry/metadata binding. It does not prove open-file-description identity, access flags or CLOEXEC; an equivalent same-node replacement may pass. Source-based absence of concurrent descriptor-table rebinding is part of the fixed graph premise. No optional flag-check code was added or claimed to detect all replacement.

Independent review found no ordinary reachable concurrent p10 writer under the inspected fixed init/proxy/daemon/helper/effective-policy graph. Accept this bounded source optimization only within that exact premise.57host methods and144effective-policy rows passed; these are host/source evidence, not Android block I/O/SELinux transition/timing/durability proof. The delayed-mutation and final-sample counterexample witnesses remain authoritative limitations.

Future image integration remains held. The two-role helper cannot admit five roles; the new design proposal still needs independent review, actual image admission and implementation. Any final manifest/core/helper/policy/init/source change must re-establish writer exclusion, binding and receipt semantics against its own exact bytes. The frozen2role image, flags and arming remain unchanged. No runtime target build, deployment, physical GO or throughput/timing claim follows.
