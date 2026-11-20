"""Refresh the public-facing aggregate snapshots from a private source checkout."""

import argparse
import hashlib
import json
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence"
PRIVATE = Path("private/cat-classifier/multiday")
RETRAIN = PRIVATE / "2026-11-19-retraining"
GROUPED = PRIVATE / "2026-11-20-ha-labeled-grouped"
LOCAL = PRIVATE / "2026-11-20-local-identity"
SNAPSHOTS = {
    "export-summary": RETRAIN / "export-summary.json",
    "gemini-pilot": RETRAIN / "gemini-pilot/summary.json",
    "grouped-dataset": GROUPED / "dataset-summary.json",
    "development-original-models": GROUPED / "larger-test/summary.json",
    "development-aggregation": LOCAL / "rule-versus-gemini.json",
    "development-visit-groups": LOCAL / "paired-group-audit.json",
    "development-screen-and-fallback": LOCAL / "combined-heldout-replay.json",
    "foreground-shortcut": LOCAL / "shortcut-results.json",
    "low-resolution": LOCAL / "lower-resolution.json",
    "int8-attempt": LOCAL / "quantization.json",
    "packed-weights": LOCAL / "packing.json",
    "combined-runtime": LOCAL / "combined-results.json",
    "linux-runtime": LOCAL / "linux-runtime-summary.json",
    "fresh-before-follow-up-freeze": LOCAL / "prospective-comparison-replay.json",
    "fresh-first-follow-up-batch": LOCAL / "prospective-comparison-results.json",
    "gemini-label-expansion": RETRAIN / "gemini-label-expansion/summary.json",
    "empty-retraining": RETRAIN / "gemini-label-expansion/training-comparison.json",
    "first-72h-shadow": Path("apps/cat_classifier/reports/shadow-2026-11-19-assessment.json"),
}


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("home_infra_checkout", type=Path)
    args = parser.parse_args()
    paths = {}
    for name, locator in SNAPSHOTS.items():
        raw = (args.home_infra_checkout / locator).read_bytes()
        aggregate = json.loads(raw)
        if "mismatched_bundles" in aggregate:
            aggregate["mismatched_bundle_count"] = len(aggregate.pop("mismatched_bundles"))
        if name.startswith("fresh-"):
            aggregate.pop("last_reviewed_epoch", None)
        save(EVIDENCE / f"{name}.json", aggregate)
        paths[f"{name}.json"] = {"locator": str(locator), "source_sha256": hashlib.sha256(raw).hexdigest()}

    locator = PRIVATE / "deploy-small-empty-48h/start.json"
    raw = (args.home_infra_checkout / locator).read_bytes()
    startup = json.loads(raw)
    save(EVIDENCE / "second-48h-startup.json", {
        "status": "startup verified; outcome pending at snapshot",
        "plan": startup["plan"],
        "app_version": startup["classifier"]["version"],
        "tracker_healthy": startup["tracker_health"],
        "first_full_scan_completed": bool(startup["status"]["last_full_scan_at"]),
        "first_scan_errors": startup["status"]["scan_error_count"],
    })
    paths["second-48h-startup.json"] = {"locator": str(locator), "source_sha256": hashlib.sha256(raw).hexdigest()}
    save(EVIDENCE / "sources.json", paths)


if __name__ == "__main__":
    main()
