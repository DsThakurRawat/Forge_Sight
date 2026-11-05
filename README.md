# ForgeSight AI

An incremental project for offline industrial surface-defect inspection on an
NVIDIA Jetson Orin Nano, with deterministic grading, local inspection history,
and a Llama-family advisory model running on the device through ExecuTorch.

**Current state:** workspace audit and repository documentation only. There is
no inspection application, trained model, or verified Jetson runtime yet.
The user reports that the Jetson is currently unavailable.

## Start here

1. [Step-by-step roadmap](FORGESIGHT_STEP_BY_STEP_ROADMAP.md): authoritative
   stage order and acceptance gates.
2. [Engineering prompt](FORGESIGHT_CODEX_MASTER_PROMPT_V3.md): teaching and
   implementation rules.
3. [Current status](docs/STATUS.md): completed evidence and the next small task.

The original `Edge AI Quality Control Model Pipeline.pdf` remains in the local
workspace as a technical reference and is excluded from Git. Its performance
figures and architectural assumptions are not verified project results.

## Evidence and decisions

- [Hardware audit](docs/HARDWARE.md)
- [Observed development environment](docs/ENVIRONMENT.md)
- [Architecture decisions](docs/DECISIONS.md)
- [Requirement evidence](docs/COMPLIANCE.md)
- [Learning notes](docs/LEARNING_LOG.md)

The provisional benchmark is MVTec AD `metal_nut`. Dataset licensing, acquisition,
splits, and loading belong to Stage 1. Controlled physical samples and actual
Jetson camera validation are separate later evidence.

## Development

The audit found an existing GPU-accessible PyTorch environment inside Ubuntu
WSL. See [the recorded commands](docs/ENVIRONMENT.md) to inspect it. That
environment has not been adopted as a project dependency lock or reproduced
from scratch. No package installation or application launch command is claimed
at this stage.

Datasets, model binaries, secrets, runtime databases, and generated outputs stay
outside Git. A local commit records a snapshot on this PC; pushing to GitHub
requires a separate authorized operation.
