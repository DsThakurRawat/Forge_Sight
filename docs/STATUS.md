# Project status

## Current stage

Stage 1, Substep 1.1: dataset source, licensing, expected layout, and project
split policy reviewed and documented. Stage 1 remains IN PROGRESS. Desktop
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

## Open gates

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

After review, Stage 1, Substep 1.2: acquire the official MVTec AD `metal_nut`
archive through the publisher's download flow, record its actual source/hash,
inspect archive paths/notices/counts, and verify the expected local layout in
ignored `data/`. The split policy is recorded, not implemented. Generate and
freeze its manifest before later sample previews. Keep Jetson hardware,
ExecuTorch device inference, and offline edge gates explicitly blocked.
