# Project status

## Current stage

Stage 1, Substep 1.4: manifest-based image/mask loader verified.
Stage 1 remains IN PROGRESS. Desktop
preparation is complete; the Jetson hardware audit remains BLOCKED - NOT VERIFIED.

## Evidence already observed

- Substep 0.1 audited all four original workspace files without changing them.
- No local `.git` directory existed at audit time.
- GitHub's repository metadata reported size zero, and the branch-list endpoint
  returned `[]`; this was checked again before repository initialization.
- Windows Python 3.10.11 runs. Ubuntu WSL has an existing Python 3.12.14
  environment with PyTorch 2.6.0+cu124; PyTorch reports CUDA available and the
  desktop RTX 2000 Ada GPU name.
- The user explicitly reports that the Jetson is not available yet.
- The original architecture PDF has been read; its proposed measurements and
  performance are not accepted as verified results.

## Completion evidence for Substep 0.2

Local commit `fd58c96` initialized `main` and recorded 12 intended files. The
remote `origin` is `https://github.com/honey-cake7/Forge_Sight.git`. No push was
performed. Staged whitespace and inventory checks passed. All four original
workspace files retained their audited SHA-256 hashes; the three original
Markdown files were also byte-identical in the staged snapshot. Seven
representative local/generated paths were checked against `.gitignore`.
Git reported a clean `main` branch after the commit.

## Completion evidence for Substep 0.3

- Created the project `.venv` using WSL CPython 3.12.14 with system packages
  excluded. Only pinned Pillow 13.0.0 and bundled pip 25.0.1 were installed.
- Installation used the published wheel hash, binary-only artifacts, and the
  official PyPI index. The exact recipe is in `docs/ENVIRONMENT.md`.
- `scripts/check_environment.py` passed isolation and lossless PNG pixel checks.
- `pip check` reported `No broken requirements found.`
- A second fresh temporary environment reproduced installation and both checks.
- No model or dataset was downloaded, and no inference was performed.

## Completion evidence for Substep 1.1

- Reviewed the official MVTec AD page and its CC BY-NC-SA 4.0 license, including
  the linked Creative Commons summary and legal code. No download form submitted.
- Checked published metal-nut counts in the original authors' paper: 220 normal
  training images, 22 normal and 93 anomalous test images. These are not yet
  locally verified counts.
- Inspected the publisher-linked 11,056-byte evaluation archive in memory;
  its code confirms image/mask pairing and absence of mask files for `good`.
  No code from the archive was executed or installed.
- Recorded a deterministic split policy before sample viewing: expected
  176 fit, 44 normal validation, 4 development previews, 111 final holdout.
  This is a project protocol, not the full official test protocol.
- See `docs/DATASET.md` for sources, limitations, and the exact proposed rule.
  No dataset images downloaded, no split manifest generated, and no loader
  implemented during this substep.

## Completion evidence for Substep 1.2

- The user supplied a Downloads path and explicitly confirmed official MVTec
  acquisition. The original `metal_nut.zip` was copied without changing it.
  Exact archive URL was unavailable; this source limitation is recorded.
- Archive: 165,672,999 bytes, SHA-256
  `5468b22edb8e3ebcb2e415bcc6adbed571e1b8a4dec03d1747e52d696384d838`.
- Actual counts: 220 normal training images; 22 normal and 93 anomalous test
  images; 93 matching masks. Defect counts: bent 25, color 22, flip 23, scratch 23.
- Every PNG fully decoded: 700x700 RGB images, grayscale `L` masks, values 0/255.
  Every anomalous image has a nonempty paired mask; no orphan masks.
- Safely extracted to ignored `data/mvtec_ad/metal_nut/`; all 430 regular files
  matched audited hashes, including the two retained attribution/license notices.
- Fourteen synthetic ZIP/tar validation/extraction tests passed. This is separate
  from the real data audit; neither is model-performance evidence.
- Source, archive, extracted data, and generated audit reports stay outside Git.
  No split manifest generated, no sample previews displayed, and no model run.

## Open gates

Substep 1.3 verified all current files against acquisition fingerprints and
found zero byte/pixel duplicate image groups. The frozen manifest assigns
176 fit, 44 normal validation, 4 development preview, and 111 final-holdout
samples. A fresh rebuild reproduces its bytes; checksum:
`14b11ebd03d5107c7ef3478e1c4d20887237e2fbef58601ac043014b8f0e340f`.
All 22 current tests passed. No previews or inference were performed.

The user authorized the next three Stage 1 substeps and `git push origin main`
after each verified commit. Actual push results are reported at each checkpoint.

Substep 1.3 was committed and pushed as `7ff8846`. Substep 1.4 verified loading
all 176 fit, 44 normal-validation, and four development samples with byte/pixel
hashes, modes, sizes, and mask semantics checked. Default final-holdout access
was refused. All 31 current tests passed. No visual previews or predictions yet.

| Gate | Status | Missing evidence |
| --- | --- | --- |
| Repeatable minimal PC image environment | DONE on tested host | Pinned install and smoke check reproduced in two isolated environments |
| Exact Jetson hardware and camera | BLOCKED - NOT VERIFIED | Device unavailable; need device-side inventory |
| Llama through ExecuTorch on Jetson | BLOCKED - NOT VERIFIED | Actual device-generated text, runner/version/hash, memory and timing |
| Vision model and defect-type classification | NOT STARTED | Real same-domain evaluation |
| Offline end-to-end inspection | NOT VERIFIED | Actual disconnected Jetson run |

Stage 1 is not DONE; no later stage is DONE. Desktop preparation and GPU
availability are not Jetson proof. The environment and source-review checks
do not establish a defect-inspection application.

## Next exact task

Stage 1, Substep 1.5: generate development-only sample previews using the verified
loader. This is the third of the three currently authorized substeps. Stop at the Stage 1
gate before advancing to Stage 2; all Jetson gates remain explicitly blocked.
