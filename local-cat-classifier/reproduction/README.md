# Reproduce on another fixed-view camera

The example commands exercise the same main method. It trains a frozen ImageNet MobileNetV3 Small with scene-specific heads, exports a single CPU graph, and replays your saved image bundles against independently reviewed labels and any saved Gemini decisions. It runs offline after the weights are cached. It does not start a Home Assistant instance or publish a service.

## 1. Export and review crops

Export a fixed ledger snapshot and the original three JPEGs for each candidate. Confirm usable JPEG bytes with a checksum and decoder. Store stable tracker event IDs, candidate intervals, camera, status, original cloud answer, and any corrections separately. A row can be locally filtered or pending cloud review. Keep that status distinct from a verified Empty label. If a candidate is retried and crops change, retain the specific revision seen by the cloud. Compare only the same crop bytes.

For Gemini-assisted review, use a single target plus a verified example of each cat. Keep references out of evaluation and do not choose them from later held-out data. The pilot used `gemini-3.1-flash-lite`, inline JPEGs, temperature 0, and an enum response constrained to Eli, Pixel, Neither, or Unsure. The prompt tells the model which of the first two images corresponds to each cat, asks it to label only the third, and specifies Unsure for darkness, occlusion, multiple cats or ambiguity. Compare visible coat markings and body shape. A cat need not be inside the tray to receive an identity label.

Start small across boxes and days and inspect every proposal. Archive proposal provenance and token usage, then write corrected labels separately. The hosted request uses files you choose to send, so check the privacy requirements of your camera and project before using it. The API key should be provided locally from your environment, outside the dataset and repository. [Gemini image inputs](https://ai.google.dev/gemini-api/docs/image-understanding) · [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing/)

Prepare a reviewed CSV. Filenames resolve relative to the CSV. Example values are synthetic.

```csv
path,label,event_id,start,end
crops/example-1.jpg,Eli,visit-1,2026-01-03T11:00:00Z,2026-01-03T11:00:30Z
```

Use Empty for confirmed Neither. Keep uncertain or unusable images outside the training CSV. Use a shared event ID for the three crops and any additional frames from the same physical visit. For correlated motion bursts with several tracker IDs, assign a common group upstream. The example removes pre-holdout images from overlapping event IDs, exact decoded pixel matches, and the embargo before the holdout boundary. The historical analysis also checked time-group and per-class coverage separately. Use a chronologically distinct validation set for tuning and a later untouched test set for any claimed victory.

## 2. Train and replay

Tested with Python 3.13 on macOS ARM64. Install the recorded versions where matching wheels are available. The default trainer downloads the torchvision ImageNet weights if they are not cached. [MobileNetV3 Small weights](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.mobilenet_v3_small.html)

```sh
python3 -m venv /path/to/local-cat-venv
. /path/to/local-cat-venv/bin/activate
python -m pip install -r reproduction/requirements.txt
python reproduction/smoke.py
python reproduction/train.py /path/to/private/images.csv --holdout-start 2026-01-08T00:00:00Z --output /path/to/private/model-small
python reproduction/replay.py /path/to/private/model-small /path/to/private/bundles.jsonl
```

Run these from the research folder and keep your camera CSV, bundle manifest, crops, virtual environment and model output outside the research repo. The smoke test uses a temporary directory and random encoder weights to exercise the wiring without a download. Its scores are meaningless. The trainer reports primary-head held-out frame results. Assess the deployed rule with the exported graph and three-frame replay.

Example input line for `bundles.jsonl`, with paths relative to that file.

```json
{"truth":"Pixel","gemini":"Unknown","event_id":"visit-1","paths":["crops/example-1.jpg","crops/example-2.jpg","crops/example-3.jpg"]}
```

Use `null` or omit `gemini` for no saved baseline. Use `Unknown` only for an actual saved abstention. The replay reports both the full eligible sample and the paired denominator. When supplied, `event_id` also counts each group once by comparing its fraction of paired bundles correct. Keep each group on one split. Interpret time-derived groups as provisional until a person checks the event boundaries.

## 3. Observe prospectively in HA

The [app patch](ha-small-shadow.patch) applies to the classifier app in the project checkout at base revision `77013efd9083734d627068df983243d2bf9cfeb7`. It adds the Small profile and leaves the earlier Large trial protocol intact. The model produced by these scripts has the three expected ONNX outputs and model card fields. Supply your own model directory in the app's build context as `models/small-empty-augmented/`. The patch is provided as engineering evidence. The existing collector expects the original tracker's API and directory contract, so adapt those read-only integration points to your own tracker before deploying.

Record start, deadline, code and model hashes, thresholds, revision limits and resource limits before observation. Write private evidence for candidate revisions, separate baseline history from labels, do one full scan at startup and on resume, and stop automatically at the deadline. Keep the observer separate from live decisions. Check persisted shutdown state and review evidence read-only, including disagreements and a balanced set of agreement controls. If an ingress client cannot preserve JPEG bytes, use an authorized binary-safe export and prove the checksums before labeling.

## Evidence provenance

`collect_evidence.py` refreshes aggregate JSON snapshots from the originating development checkout for the author, with original source SHA-256 digests in [sources.json](../evidence/sources.json). External readers can use the shipped aggregates and substitute their own crops. The collector does not fetch camera images or send API calls.
