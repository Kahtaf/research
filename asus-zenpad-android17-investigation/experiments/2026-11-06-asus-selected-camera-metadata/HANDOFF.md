# Handoff

Completed bounded investigation: inspected stock metadata cannot supply the selected OV5670/OV2680 HAL3 contract. COMMON explicitly supplies HAL1; selected/default COMMON request constructors are absent and the actual request path returns -ENOENT, leaving null default settings. This does not prove hardware impossibility.

Read `report/REPORT.md` and `evidence/mapping.json`. Evidence includes 292 stock ELF inventories, exact lookup names/addresses, dynamic-source separation, 107 ARM32 + 68 ARM64 instruction tests, and an SDK37 compile-only schema witness.

Reproduce locally, without SSH or devices:

```sh
fixture/venv/bin/python scripts/dispatch_fixture.py
fixture/venv/bin/python scripts/dispatch64_fixture.py
fixture/venv/bin/python scripts/schema_witness.py
```

Run from this spike. To recreate the disposable venv, install the versions recorded in fixture-results.json. Do not run collection scripts unless renewed remote extraction is needed. No native vendor constructors are run by fixtures; their external operations are stubs.

Next implementation boundary is an isolated, provenance-backed selected-sensor metadata/template source contract, followed separately by parent-owned pipeline/hardware qualification. No product enable, force property, constructor alias, empty metadata success, generic old system libraries or fake GraphicBuffer alias. Independent graphics/PropertyMap/closure/ioctl blockers remain; none is a new prerequisite for the first RAM kernel probe.
