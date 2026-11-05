# MVTec AD metal_nut: source and evaluation policy

Stage 1, Substep 1.1. Reviewed 2026-11-05 (Asia/Calcutta).
This is a source review and a proposed local data contract. No dataset images
have been acquired, counted, decoded, or split yet.

## Source and permitted scope

Use the original 2D MVTec AD `metal_nut` category. The
[official dataset page](https://www.mvtec.com/research-teaching/datasets/mvtec-ad)
describes normal-only training, mixed normal/anomalous testing, pixel-level
annotations, and CC BY-NC-SA 4.0 licensing. The legacy `/company/research/`
address redirected to this page with HTTP 200 during this review. The current
page presents a download form; no form was submitted and no unofficial mirror
or guessed archive address has been selected. MVTec AD 2 is a different dataset.

Use this benchmark for the noncommercial learning/research prototype.
Commercial use is excluded by the stated license. When sharing dataset images
or adaptations, retain attribution and license notices, identify changes, and
apply the required ShareAlike terms to shared adaptations. This step does not
establish commercial rights for trained artifacts or decide whether a particular
competition use qualifies as noncommercial. Source code and future controlled
physical samples have separate provenance and licensing.

License references: [CC summary](https://creativecommons.org/licenses/by-nc-sa/4.0/)
and [legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en).
Keep raw archives, extracted images/masks, and generated previews outside Git
under the already ignored `data/` and `artifacts/` paths. This repository policy
does not mean the license forbids every form of redistribution.

Dataset attribution: MVTec Software GmbH; Paul Bergmann, Michael Fauser,
David Sattlegger, and Carsten Steger, *MVTec AD -- A Comprehensive Real-World
Dataset for Unsupervised Anomaly Detection*, CVPR 2019, pp. 9592-9600.

## Published facts versus local evidence

The original authors' [paper, Table 1](https://openaccess.thecvf.com/content_CVPR_2019/papers/Bergmann_MVTec_AD_--_A_Comprehensive_Real-World_Dataset_for_Unsupervised_Anomaly_CVPR_2019_paper.pdf)
reports 220 normal training images, 22 normal test images, 93 anomalous test
images, four defect groups, and a 700-pixel image side length for metal nuts.
These are published expectations, not local counts. The four labels expected
by our contract are `bent`, `color`, `flip`, and `scratch`; their names also appear
in a [published evaluation's supplementary table](https://openaccess.thecvf.com/content/ICCV2023W/LXCV/supplemental/Gula_Gaussian_Image_Anomaly_ICCVW_2023_supplemental.pdf).
Actual directories, per-type counts, image modes, and mask values remain
NOT VERIFIED until acquisition. The `flip` label concerns an orientation
anomaly; a dataset label does not establish physical damage or severity.

Expected local layout, to verify after download:

```text
data/mvtec_ad/metal_nut/
  train/good/<id>.png
  test/good/<id>.png
  test/<defect>/<id>.png
  ground_truth/<defect>/<id>_mask.png
```

The [officially linked evaluation archive](https://www.mydrive.ch/shares/163177/45dca6b52b7453388ebe2b82e97e064b/download/439517473-1665675012/mvtec_ad_evaluation.tar.xz)
was inspected in memory, without installing or executing its code. Version 1.0's
`evaluate_experiment.py` confirms test/ground-truth pairing by matching defect
directory and filename stem, adding `_mask.png` for defective images, and using
no ground-truth file for `good` images. Positive mask pixels represent anomalies;
do not assume a specific on-disk encoding before checking real masks. A missing
mask for an anomalous image is an error, not an implicit normal image.

Reference archive: 11,056 bytes; SHA-256
`dfcda7d67eee25316ec6ae5042c0b1684a4cabf33b2346be351e2ce36013f220`.
It is reference material only; its historical Python/dependency recipe was
not adopted. No external evaluation files were copied into this repository.

## Project split policy v1: choose before viewing samples

Anomaly detection learns normal appearance; it does not learn four defect
classes merely because folder names exist. Keep the original source folders
unchanged and assign roles in a separate manifest before generating previews.

| Source | Project role | Expected count | Permitted use |
| --- | --- | --- | --- |
| `train/good` | fit | 176 | Fit model and training-dependent preprocessing |
| `train/good` | validation_normal | 44 | Select settings/calibrate normal false-alarm behavior |
| One image per anomalous test folder | development_preview | 4 | Learn the data and debug image/mask display |
| All remaining original test images | final_holdout | 111: 22 normal, 89 anomalous | One final evaluation after configuration is frozen |

Counts assume the published inventory and no cross-role duplicate content;
they must be verified before any split is marked created. No split manifest
exists yet.

Deterministic selection rule for the later manifest implementation:

1. Use seed `42` and version string `forgesight-metal-nut-v1`. Paths are POSIX
   paths relative to the category root, such as `train/good/000.png`.
2. Rank paths by the hexadecimal SHA-256 of UTF-8 text
   `forgesight-metal-nut-v1|42|<relative_path>`; break ties by relative path.
3. For normal training images, take the first floor(20% of the count) as
   validation; use the remainder for fitting.
4. Within each of the four anomalous test folders, reserve the first ranked
   image and its mask for development previews. All other original test images,
   including every `test/good` image, enter the final holdout.
5. Record source paths, roles, content hashes, mask links, and the policy version.
   Check source and decoded-pixel duplicates before accepting the partition;
   conflicting roles require review and a documented policy update before
   training. Do not silently accept leakage or change the seed to improve results.

The development positives never enter fitting or threshold calibration. Normal-
only validation can estimate false alarms, with substantial uncertainty from
44 samples; it cannot optimize defect recall or F1. Do not use final holdout
images/masks for model selection, resizing decisions, threshold tuning, or
preview contact sheets. Image hashing and structural inventory are permitted
to establish provenance before evaluation.

Trade-off: reserving four examples permits honest hands-on learning with real
anomalies, but final results use a custom 111-image project holdout, not the full
115-image official test set. The 80/20 normal split also fits fewer images than
an all-training-images baseline. Report both differences when comparing models.
Keep the same frozen manifest for fair project baseline comparisons. If final
test results guide another revision, those images are no longer an untouched
test set; record that and obtain independent evaluation evidence.

Physical part IDs are not yet verified. Byte/pixel duplicate checks alone cannot
prove that different photographs show different physical parts. Later camera
validation requires distinct controlled samples and part-level splitting.

## Known gaps and next task

No data loader, masks, split manifest, predictions, or metrics are implemented.
Defect subtype classification remains unmet: test folder labels are ground truth
for evaluation, not a prediction mechanism or a supervised training set.
Physical camera generalization and every Jetson requirement remain unverified.

Next: Stage 1.2, acquire the official category archive through the publisher's
download flow; record the actual source/archive hash; inspect archive paths,
notices, and counts; and verify the local layout under ignored `data/`.
Create the manifest before viewing real examples in a later loader/preview step.
