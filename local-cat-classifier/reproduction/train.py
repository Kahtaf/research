"""Fit scene-specific MobileNetV3 Small heads and export one ONNX bundle model."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import torch
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small


from images import LABELS, image_tensor


def epoch(value):
    stamp = datetime.fromisoformat(value)
    if stamp.tzinfo is None:
        raise ValueError("Timestamps must include a timezone")
    return stamp.astimezone(timezone.utc).timestamp()


def load_split(manifest, boundary, embargo):
    with manifest.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    seen = {}
    for row in rows:
        if row["label"] not in LABELS or not row["event_id"]:
            raise ValueError("Use reviewed frame labels and nonempty event IDs")
        row["start"], row["end"] = epoch(row["start"]), epoch(row["end"])
        if row["end"] < row["start"]:
            raise ValueError("Frame interval ends before it starts")
        row["path"] = manifest.parent / row["path"]
        with Image.open(row["path"]) as image:
            rgb = image.convert("RGB")
            row["pixel"] = hashlib.sha256(str(rgb.size).encode() + rgb.tobytes()).hexdigest()
        known = seen.setdefault(row["pixel"], row["label"])
        if known != row["label"]:
            raise ValueError("Exact decoded pixels have conflicting labels")

    holdout = [row for row in rows if row["start"] >= boundary]
    held_pixels = {row["pixel"] for row in holdout}
    held_events = {row["event_id"] for row in holdout}
    training = [row for row in rows if row["end"] < boundary - embargo
                and row["event_id"] not in held_events and row["pixel"] not in held_pixels]

    def unique(items):
        return list({row["pixel"]: row for row in reversed(items)}.values())[::-1]

    training, holdout = unique(training), unique(holdout)
    if set(row["label"] for row in training) != set(LABELS) or not holdout:
        raise ValueError("Need all training classes and an untouched holdout")
    return training, holdout


def embeddings(encoder, items, size):
    parts = []
    with torch.inference_mode():
        for offset in range(0, len(items), 8):
            images = []
            for row in items[offset:offset + 8]:
                with Image.open(row["path"]) as image:
                    images.append(image_tensor(image, size))
            parts.append(encoder(torch.from_numpy(np.stack(images))).numpy())
    return np.concatenate(parts)


def fit(features, labels):
    scale = StandardScaler().fit(features)
    head = LogisticRegression(C=.01, class_weight="balanced", max_iter=3000, random_state=17)
    head.fit(scale.transform(features), labels)
    return scale, head


def fitted_linear(heads, rows):
    weights, biases = [], []
    for scale, model in heads:
        adjusted = model.coef_ / scale.scale_
        weights.append(adjusted)
        biases.append(model.intercept_ - adjusted @ scale.mean_)
    weights, biases = np.concatenate(weights), np.concatenate(biases)
    layer = torch.nn.Linear(weights.shape[1], rows)
    with torch.no_grad():
        layer.weight.copy_(torch.from_numpy(weights))
        layer.bias.copy_(torch.from_numpy(biases))
    return layer


def pack_large_weights(model):
    """Store weights as FP16 and cast back to FP32 before their original consumers."""
    casts = []
    for value in model.graph.initializer:
        if value.data_type != TensorProto.FLOAT:
            continue
        array = numpy_helper.to_array(value)
        if not np.isfinite(array).all():
            raise ValueError("Non-finite ONNX weight")
        if array.nbytes < 1024 or np.abs(array).max() > np.finfo(np.float16).max:
            continue
        name = value.name
        packed = name + "__fp16"
        value.CopyFrom(numpy_helper.from_array(array.astype(np.float16), packed))
        casts.append(helper.make_node("Cast", [packed], [name], to=TensorProto.FLOAT))
    original = list(model.graph.node)
    del model.graph.node[:]
    model.graph.node.extend(casts + original)


def export(encoder, heads, out):
    class BundleHeads(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = encoder
            self.fine = fitted_linear([heads["fine"]], 3)
            self.coarse = fitted_linear([heads["coarse"]], 3)
            self.fallback = fitted_linear(heads["fallback"], 2)

        def forward(self, image):
            features = self.encoder(image)
            return self.fine(features), self.coarse(features), self.fallback(features)

    file = out / "model.onnx"
    # Keep the legacy exporter for the verified dynamic spatial input contract.
    torch.onnx.export(
        BundleHeads().eval(), torch.zeros(1, 3, 320, 320), str(file),
        input_names=["image"], output_names=["logits", "logits160", "fallback_logits"],
        dynamic_axes={"image": {2: "height", 3: "width"}}, opset_version=18, dynamo=False,
    )
    model = onnx.load(file)
    pack_large_weights(model)
    onnx.checker.check_model(model, full_check=True)
    onnx.save(model, file)
    card = {"sha256": hashlib.sha256(file.read_bytes()).hexdigest(), "labels": LABELS,
            "coarse_empty_threshold": .99, "fallback_logit_order": ["visible_cat", "Pixel_given_visible_cat"]}
    (out / "model.json").write_text(json.dumps(card, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--holdout-start", type=epoch, required=True)
    parser.add_argument("--embargo-seconds", type=int, default=300)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--weights", choices=("imagenet", "random"), default="imagenet",
                        help="random is for wiring tests only")
    args = parser.parse_args()
    if args.embargo_seconds < 0:
        parser.error("Embargo must be nonnegative")
    training, holdout = load_split(args.manifest, args.holdout_start, args.embargo_seconds)
    torch.manual_seed(17)
    torch.set_num_threads(2)
    weights = MobileNet_V3_Small_Weights.IMAGENET1K_V1 if args.weights == "imagenet" else None
    encoder = mobilenet_v3_small(weights=weights)
    encoder.classifier = torch.nn.Identity()
    encoder.eval().requires_grad_(False)
    fine, coarse = (embeddings(encoder, training, size) for size in (320, 160))
    labels = np.array([r["label"] for r in training])
    cats = labels != "Empty"
    heads = {"fine": fit(fine, labels), "coarse": fit(coarse, labels),
             "fallback": [fit(fine, cats), fit(fine[cats], labels[cats] == "Pixel")]}
    args.output.mkdir(parents=True, exist_ok=False)
    export(encoder, heads, args.output)
    features = embeddings(encoder, holdout, 320)
    scale, head = heads["fine"]
    predicted = head.predict(scale.transform(features))
    confusion = {label: dict(Counter(p for p, r in zip(predicted, holdout, strict=True)
                                      if r["label"] == label)) for label in LABELS}
    result = {
        "scope": "held-out single-frame primary head before ONNX packing; replay.py tests exported bundles",
        "weights": args.weights,
        "training_frames": dict(Counter(labels)),
        "holdout_frames": len(holdout),
        "holdout_confusion": confusion,
    }
    (args.output / "frame-evaluation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
