"""Exercise training, ONNX export, and replay using generated crops and no network."""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image

from images import LABELS


HERE = Path(__file__).resolve().parent


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--weights", choices=("imagenet", "random"), default="random")
    args = cli.parse_args()
    with TemporaryDirectory() as directory:
        root = Path(directory)
        dataset = []
        bundles = []
        rng = np.random.default_rng(42)
        for day in (1, 3):
            for index, name in enumerate(LABELS):
                paths = []
                for frame in range(3):
                    image = rng.integers(0, 170, (64, 80, 3), np.uint8)
                    image[:, 5:20, index] += 65
                    path = f"{day}-{name}-{frame}.png"
                    Image.fromarray(image).save(root / path)
                    start = f"2026-01-{day:02d}T12:00:00Z"
                    end = f"2026-01-{day:02d}T12:00:30Z"
                    dataset.append((path, name, f"{day}-{name}", start, end))
                    paths.append(path)
                if day == 3:
                    bundles.append({"truth": name, "event_id": f"{day}-{name}", "gemini": "Unknown" if name == "Empty" else name,
                                    "paths": paths})
        with (root / "images.csv").open("w", newline="") as handle:
            out = csv.writer(handle)
            out.writerow(["path", "label", "event_id", "start", "end"])
            out.writerows(dataset)
        (root / "bundles.jsonl").write_text("".join(json.dumps(row) + "\n" for row in bundles))
        train = subprocess.check_output(
            [sys.executable, str(HERE / "train.py"), str(root / "images.csv"),
             "--output", str(root / "model"), "--weights", args.weights,
             "--holdout-start", "2026-01-03T00:00:00Z"], text=True,
        )
        replay = subprocess.check_output(
            [sys.executable, str(HERE / "replay.py"), str(root / "model"),
             str(root / "bundles.jsonl")], text=True,
        )
        training, result = json.loads(train), json.loads(replay)
        assert training["weights"] == args.weights and training["holdout_frames"] == 9
        assert result["all"] == result["paired"] == {name: 1 for name in LABELS}
        assert all(sum(r.values()) == 1 for r in result["paired_group_results"].values())
        assert not result["excluded"] and sum(result["paths"].values()) == 3
        print("Generated crops proved grouping, frozen-head fit, packed ONNX export, and paired inference.")


if __name__ == "__main__":
    main()
