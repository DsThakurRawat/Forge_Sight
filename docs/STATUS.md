# Project status

## Current stage

Stage 0, Substep 0.2: preserve the audited workspace in local version control
and establish the project documentation. Stage 0 as a whole remains IN PROGRESS.

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

The local commit containing this file is the snapshot for this substep. Its
verification requires `git diff --cached --check` before commit, inspection of
the staged inventory, ignore-rule checks, original-file hash comparison, and
`git status --short --branch` after commit. The final step report supplies the
actual commit hash and observed results; this file does not predict them.

## Open gates

| Gate | Status | Missing evidence |
| --- | --- | --- |
| Repeatable minimal project environment | NOT VERIFIED | Isolated setup, exact dependencies, and repeatable smoke check |
| Exact Jetson hardware and camera | BLOCKED - NOT VERIFIED | Device unavailable; need device-side inventory |
| Llama through ExecuTorch on Jetson | BLOCKED - NOT VERIFIED | Actual device-generated text, runner/version/hash, memory and timing |
| Vision model and defect-type classification | NOT STARTED | Real same-domain evaluation |
| Offline end-to-end inspection | NOT VERIFIED | Actual disconnected Jetson run |

No later stage is DONE. Desktop GPU availability is not Jetson proof.

## Next exact task

Stage 0, Substep 0.3: prepare and verify a minimal isolated PC development
environment, using the existing WSL environment as evidence when choosing
compatible dependencies. Do not mutate the shared `/root/pytorch-env` casually.
Choose and explain the smallest dependency set needed for the first image-input
exercise; record exact setup and validation commands.

Review that result before Stage 1, Substep 1.1: inspect the official MVTec AD
`metal_nut` source, license, layout, and split policy. If the Jetson remains
unavailable, independent PC work may continue with the device gates explicitly
blocked, as allowed by the roadmap.
