"""Check the report's main denominators and aggregate-only evidence contract."""
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"


def read(name):
    return json.loads((EVIDENCE / f"{name}.json").read_text())


def main():
    assert set(p.name for p in EVIDENCE.glob("*.json")) == set(read("sources")) | {"sources.json"}
    earlier, followup = (read(n) for n in ("fresh-before-follow-up-freeze", "fresh-first-follow-up-batch"))
    for name, expected in (("Frozen Small", 95), ("Combined Small", 95), ("Gemini", 94)):
        a, b = (d["paired_bundles"][name] for d in (earlier, followup))
        assert (a["correct"] + b["correct"], a["n"] + b["n"]) == (expected, 95)
    assert earlier["support_paired"] == {"Empty": 90, "Eli": 4}
    assert followup["support_paired"] == {"Empty": 1}
    assert sum(d["paired_five_minute_groups_by_label"]["Eli"] for d in (earlier, followup)) == 1
    assert sum(d["paired_five_minute_groups_by_label"]["Pixel"] for d in (earlier, followup)) == 0

    development = read("development-screen-and-fallback")["date_held_out_development"]
    assert development["support"] == {"Eli": 51, "Pixel": 41, "Empty": 42}
    assert development["combined"]["correct"] == 133 and development["gemini_paired"]["correct"] == 122
    extra_empty = read("empty-retraining")
    assert sum(extra_empty["new_training_counts"].values()) == 5943
    assert extra_empty["new_training_counts"]["Empty"] - extra_empty["old_training_counts"]["Empty"] == 860

    initial = read("first-72h-shadow")
    assert initial["collection"]["processed"] == 1228 and initial["collection"]["candidates"] == 1265
    assert sum(cat["agreed"] for cat in initial["agreement"]["per_cat"].values()) == 18
    assert initial["independent_review"]["images_visually_inspected"] == 0
    assert initial["finished"]["reason"] == "deadline"
    followup = read("second-48h-startup")
    plan = followup["plan"]
    assert abs(plan["deadline_at"] - plan["started_at"] - 172800) < .001
    assert followup["status"] == "startup verified; outcome pending at snapshot"

    private_patterns = re.compile(
        r"/Users/|192\.168\.|AIza[0-9A-Za-z_-]{20}|/api/hassio_ingress/"
        r"|[0-9a-f]{24}\.jpg|BEGIN .*PRIVATE KEY"
    )
    excluded_suffixes = {".jpg", ".jpeg", ".png", ".onnx", ".pth", ".sqlite", ".env"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        assert path.suffix.lower() not in excluded_suffixes, path.name
        if path != Path(__file__).resolve():
            assert not private_patterns.search(path.read_text()), path.name
        if path.suffix == ".md":
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if "://" not in target and not target.startswith("#"):
                    assert (path.parent / target.split("#", 1)[0]).is_file(), (path.name, target)
    print("Research denominators, relative links, and aggregate-only privacy checks passed.")


if __name__ == "__main__":
    main()
