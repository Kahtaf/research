# Parent small-fix handoff

New source SHA256: 27b8fbf665e8efd5b41b6485184393f112eb7c6fe6854a6821d0f14a84f785d8.

P1: PipeStream now receives a distinct cheap before_write callback, invoked after each writable-event wait immediately before os.write. The request callback checks current host epoch/both180second binding ages and the original observation deadline. All blocking source/install/USB/server checks precede it. Guard also checks freshness after its server probe. A partial or failed request never permits activation/retry; UNKNOWN consumption is preserved. There is no claim of atomic clock/USB continuity across scheduler interruptions.

P3: README now asserts transport.LOADED_SOURCE_SHA against the exact new source hash. The broken prior attribute was removed.

38guarded tests passed, including six new checks: final-server-probe expiry, writable-event-wait expiry, wall-only expiry, actual callback ordering after select, valid fresh dispatch finishing after binding age180, and the real README assertion. No late finish-time age rule was added. Parent/child audit hooks block real ADB, AF_INET/network, arbitrary subprocess and writes outside this spike.101fixturechildren were reaped. Peak parent660701184bytes; Darwin rejected hard AS limit, documented as observed rather than hard-bound. CPU limit60seconds; no portable Darwin one-core affinity claim. Larger owned regular-file fixtures were hash-recorded then removed after each test, retaining receipts/requests/logs.

Original source/tests/README and target/measure/deployment inputs remain unchanged. Only this new spike was edited. No actual ADB/network/device/root/VM/cloud/build operation or physical timing measurement occurred. Exact fixed source patch and parent-tests.json/log are under evidence. No physical GO or commissioning approval. Obtain a fresh independent review before relying on this revision for the supervised session.
