# Research notes

## 2026-11-20

- Opened this investigation to preserve the engineering record for a future blog post. The blog workspace is separate.
- Read the research repository instructions. Keep this work in one new folder and commit only that folder.
- Located the classifier and tracker source, the first Home Assistant shadow assessment, the Gemini labeling records, grouped evaluation and runtime benchmarks, and the startup record for the still-running 48-hour follow-up.

### Evidence selection and reproduction

- Copied aggregate outputs for the data export, Gemini pilot and expansion, matched retrospective comparisons, failed optimizations, Linux/Mac measurements, and the finished Large shadow run. Saved a startup-only projection for the Small follow-up and labeled it pending.
- Captured the scoped HA source diff against home-infra base revision `77013efd9083734d627068df983243d2bf9cfeb7`. The research folder does not contain a source checkout, camera exports, raw review rows, credentials, or fitted household models.
- Wrote a small offline reproduction pipeline using a date cutoff, an event embargo, exact decoded pixel deduplication, MobileNetV3 features, balanced logistic heads, and one packed CPU ONNX graph. The synthetic smoke test checks that the pipeline works independently of the private dataset.
- The likely editorial story is that abstention and frame sampling mattered more than backbone size, and the retrospective lift needs to be distinguished from a thin prospective lead. The 860 additional Empty labels helped explicit Empty decisions, with no demonstrated Pixel recall gain.

### Earlier spikes

The following references are local workspace provenance for the author. Their aggregate results are summarized in the report.

- `ideas/2026-11-15-cat-classifier-dataset/README.md` records the first 487-image release, crop inventory, trainer/evaluation split, and temporal safeguards.
- `ideas/2026-11-15-cat-classifier-training/README.md` records the first frozen MobileNetV3 Large and DINOv3 ViT-S/16 comparison. On the 18-image historical subset, separate date-excluding heads scored 16/18 and 17/18 respectively. That subset and those heads differ from the 54-image later-day test.
- `ideas/2026-11-16-frigate-native-cat-classifier/README.md` records the native MobileNetV2 0.35 INT8 proof and its false Empty. That experiment tested the processor on saved validation frames, without switching live routing.

### Verification

- Both random-weight and cached ImageNet-weight smoke runs completed with synthetic image files. The local ONNX CPU replay checked finite outputs and group results. The synthetic smoke scores carry no model-quality claim.
- Applied the HA patch in a temporary export of the recorded base revision. All 20 existing app tests passed. The copy with whitespace-normalized patch context also passed the forward apply check.
- Reconciled comparison denominators and trial limits from the shipped JSON. Reduced per-bundle mismatch lists to totals and scanned the staged packet for local host paths, credential patterns, and private data file types.
