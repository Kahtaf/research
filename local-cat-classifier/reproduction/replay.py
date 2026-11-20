"""Run exported Small on saved bundles and compare with saved Gemini answers."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

from images import LABELS, image_tensor


CATS = {"Eli", "Pixel"}


def softmax(values):
    p = np.exp(values - values.max())
    return p / p.sum()


def confident(p):
    best = int(p.argmax())
    return LABELS[best], float(p[best])


def aggregate(frames):
    labels = [label for label, score in frames if score >= .8]
    cats = set(labels) & CATS
    if len(cats) == 1:
        return cats.pop()
    if labels == ["Empty"] * 3:
        return "Empty"
    return "Unknown"


def fallback_frame(logits):
    present, pixel = 1 / (1 + np.exp(-np.clip(logits, -80, 80)))
    if present < .5:
        return "Empty", float(1 - present)
    return "Pixel" if pixel > .5 else "Eli", float(min(present, max(pixel, 1 - pixel)))


class Runtime:
    def __init__(self, model):
        card = json.loads((model / "model.json").read_text())
        file = model / "model.onnx"
        if hashlib.sha256(file.read_bytes()).hexdigest() != card["sha256"] or card["labels"] != LABELS:
            raise ValueError("Model checksum or label contract differs")
        options = ort.SessionOptions()
        options.intra_op_num_threads = options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(file), options, providers=["CPUExecutionProvider"])

    def infer(self, image, size, outputs):
        tensor = image_tensor(image, size)[None]
        values = self.session.run(outputs, {"image": tensor})
        sizes = {"logits": 3, "logits160": 3, "fallback_logits": 2}
        for key, value in zip(outputs, values, strict=True):
            if value.shape != (1, sizes[key]) or not np.isfinite(value).all():
                raise ValueError("Unexpected inference output")
        return tuple(value[0] for value in values)

    def bundle(self, paths):
        if len(paths) != 3:
            raise ValueError("Expected exactly three tracker crops")
        images = []
        for path in paths:
            with Image.open(path) as image:
                if image.width * image.height > 4_000_000:
                    raise ValueError("Oversized crop")
                contrast = image.convert("L").resize((96, 96))
                if np.ptp(np.percentile(np.array(contrast), [10, 90])) < 5:
                    raise ValueError("Blank or low-contrast crop")
                images.append(image.convert("RGB"))
        for image in images:
            logits, = self.infer(image, 160, ["logits160"])
            label, probability = confident(softmax(logits))
            if label != "Empty" or probability < .99:
                break
        else:
            return "Empty", "screen"
        both = [self.infer(image, 320, ["logits", "fallback_logits"]) for image in images]
        prediction = aggregate([confident(softmax(primary)) for primary, _ in both])
        if prediction == "Unknown":
            return aggregate([fallback_frame(branch) for _, branch in both]), "fallback"
        return prediction, "primary"


def correct(expected, actual):
    return actual == expected or (expected == "Empty" and actual == "Unknown")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("bundles", type=Path, help="JSONL with independently reviewed truth and saved Gemini answer")
    args = parser.parse_args()
    runtime = Runtime(args.model)
    all_rows, paired = Counter(), Counter()
    outcomes = {name: {label: Counter() for label in LABELS} for name in ("Small", "Gemini")}
    paths, errors = Counter(), Counter()
    group_delta = defaultdict(int)
    read = [json.loads(line) for line in args.bundles.read_text().splitlines() if line.strip()]
    for row in read:
        truth = row["truth"]
        if truth not in LABELS:
            errors["ambiguous_truth"] += 1
            continue
        try:
            guess, path = runtime.bundle([args.bundles.parent / item for item in row["paths"]])
        except (ValueError, OSError):
            errors["unusable_crops"] += 1
            continue
        paths[path] += 1
        all_rows[truth] += 1
        gemini = row.get("gemini")
        if gemini in (*LABELS, "Unknown"):
            paired[truth] += 1
            outcomes["Small"][truth][guess] += 1
            outcomes["Gemini"][truth][gemini] += 1
            if row.get("event_id"):
                group_delta[(truth, row["event_id"])] += correct(truth, guess) - correct(truth, gemini)
    correct_count = {model: sum(n for label, counts in confusion.items()
                      for result, n in counts.items() if correct(label, result))
                     for model, confusion in outcomes.items()}
    group_results = {label: Counter() for label in LABELS}
    for (label, _), delta in group_delta.items():
        group_results[label]["Small wins" if delta > 0 else "Gemini wins" if delta < 0 else "ties"] += 1
    print(json.dumps({"all": all_rows, "paired": paired, "correct": correct_count,
                      "paired_confusion": outcomes, "paired_group_results": group_results,
                      "paths": paths, "excluded": errors}, indent=2))


if __name__ == "__main__":
    main()
