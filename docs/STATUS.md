# Project status

## Current stage

Stage 0, Substep 0.3: minimal isolated PC image environment verified. Desktop
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

## Open gates

| Gate | Status | Missing evidence |
| --- | --- | --- |
| Repeatable minimal PC image environment | DONE on tested host | Pinned install and smoke check reproduced in two isolated environments |
| Exact Jetson hardware and camera | BLOCKED - NOT VERIFIED | Device unavailable; need device-side inventory |
| Llama through ExecuTorch on Jetson | BLOCKED - NOT VERIFIED | Actual device-generated text, runner/version/hash, memory and timing |
| Vision model and defect-type classification | NOT STARTED | Real same-domain evaluation |
| Offline end-to-end inspection | NOT VERIFIED | Actual disconnected Jetson run |

No later stage is DONE. Desktop preparation and GPU availability are not Jetson
proof. The environment checks do not establish a defect-inspection application.

## Next exact task

After review, Stage 1, Substep 1.1: inspect the official MVTec AD `metal_nut`
source, license, directory layout, and leakage-safe split policy before any
dataset download or loader implementation. The roadmap permits independent PC
work while the device is unavailable. Keep Jetson hardware, ExecuTorch device
inference, and offline edge gates explicitly blocked until actual evidence exists.
