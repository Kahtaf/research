# Genuine SDK37 host metadata resolvers

Question: Can the actual SDK37 fs_config and selabel implementations be compiled into isolated fixed-path host query tools, with source-bound override/context behavior qualified?

Status: Complete: genuine SDK37 host resolver ELFs compiled and synthetic metadata/context QA passed. Reusable tools only; no production metadata/admission or SYSTEM access.

Outputs: [REPORT.md](REPORT.md), [acceptance.json](acceptance.json), [PARENT-CONTRACT.md](PARENT-CONTRACT.md), actual ELFs in `artifacts/`, primary-source/caller patch in `source/`, executable guard in `scripts/query.py`, and stdout/exit/dependency QA in `evidence/`. Large dependencies stay at `/srv/android/asus-sdk37-host-metadata-resolvers-20261106`; successful tools are `bin-r4/` with `inputs-r4/` closure, compiled from `source-r4/`. Canonical remote delivery is `handoff-r2/`; root `source/` is historical and preserved.

Continuation: Preserve earlier observer/mechanism spikes and all kits/fixtures. Never run AOSP/Ninja/kernel builds, mutate active source/out, select/capture product outputs, or substitute synthetic metadata for a genuine admitted product. Read final report before reuse.

Reverify local pins and unchanged earlier payloads with `python3 -B scripts/finalize.py`. Historical remote setup/QA scripts preserve attempts and are not rerunnable over existing directories. The guarded query is the reusable interface. A real metadata group still requires actual parent-admitted coherent inputs.
