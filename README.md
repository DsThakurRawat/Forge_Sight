# ForgeSight AI

An incremental project for offline industrial surface-defect inspection on an
NVIDIA Jetson Orin Nano, with deterministic grading, local inspection history,
and a Llama-family advisory model running on the device through ExecuTorch.

**Current state:** Stage 1 data/input preparation is verified on the PC, including
a frozen split, role-based image/mask loader, and inspected development previews. There is
no inspection application, trained model, or verified Jetson runtime yet.
The user reports that the Jetson is currently unavailable.
Stage 2 preparation has started; actual Llama/ExecuTorch device inference is
blocked by device unavailability and unprepared export/build tooling. The user
has obtained Meta Llama access; all five original source files match the pinned
publisher revision. See
[the runtime evidence and candidate](docs/EDGE_RUNTIME.md).
The source-pinned export recipe is preparation only; it reports its missing
inputs and does not download weights, install packages, or create a model.
The capture harness also refuses this PC as a Jetson target. All 58 project
tests pass; there is still no exported Llama artifact or generated model text.

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
- [Dataset source and split policy](docs/DATASET.md)
- [Architecture decisions](docs/DECISIONS.md)
- [Requirement evidence](docs/COMPLIANCE.md)
- [Learning notes](docs/LEARNING_LOG.md)

The benchmark domain is MVTec AD `metal_nut`. Its real archive and extracted
335 images/93 masks have passed structural validation; the license, source
fingerprint, counts, and split policy are in `docs/DATASET.md`. A frozen manifest
assigns 176 fit, 44 normal-validation, four development, and 111 holdout samples.
A verified loader reads fitting, validation, and development roles. A local
contact sheet shows supplied ground-truth annotations; no model predictions
exist yet. Final evaluation uses a disclosed custom holdout that excludes
development previews. Controlled physical samples and actual Jetson camera
validation are separate later evidence.

Repeat the category archive audit without extracting or displaying images:

```powershell
wsl -d Ubuntu --exec .venv/bin/python -B scripts/audit_metal_nut_archive.py data/downloads/metal_nut.zip
```

Verify the frozen split against the current dataset:

```powershell
wsl -d Ubuntu --exec .venv/bin/python -B -m forgesight.data_manifest --check
```

Load and verify the four development image/mask pairs:

```powershell
wsl -d Ubuntu --exec .venv/bin/python -B -m forgesight.data_loader --role development_preview
```

Generate the development-only contact sheet (output directory must be new):

```powershell
wsl -d Ubuntu --exec .venv/bin/python -B -m forgesight.data_preview
```

Open `artifacts/data/development_preview_v1/contact_sheet.png`. Its five rows
contain one normal fitting image plus bent, color, flip, and scratch development
samples. The red overlays are dataset annotations, not detector predictions.
The source, license, manifest fingerprint, and pixel-area metadata accompany
the image in `preview.json`. No holdout images are displayed.

Run the 58 current data-integrity and edge-preparation tests:

```powershell
wsl -d Ubuntu --exec .venv/bin/python -B -m unittest discover -s tests -v
```

Read the Stage 2 [candidate, blockers, recipe, and capture instructions](docs/EDGE_RUNTIME.md)
before installing export dependencies or attempting a device run.

Verify the downloaded source model against the publisher-checked reference:

```powershell
wsl -d Ubuntu --exec .venv/bin/python -B -m forgesight.edge_assets
```

The verified source weights are not an exported `.pte` or a successful runtime
test. The separate export environment has not been installed yet.

## Development

Use Ubuntu WSL with CPython 3.12. The project `.venv` contains Pillow 13.0.0,
pinned by version and wheel hash in [requirements.txt](requirements.txt).
It is isolated from the existing GPU-accessible PyTorch environment.

From PowerShell in this project directory, after following the
[environment setup](docs/ENVIRONMENT.md#project-environment-stage-03):

```powershell
wsl -d Ubuntu --exec .venv/bin/python -B scripts/check_environment.py
wsl -d Ubuntu --exec .venv/bin/python -B -m pip check
```

The smoke check verifies environment isolation and exact PNG pixel preservation.
It does not load a defect dataset, run a model, or test Jetson. Installation and
the check were also reproduced in a second fresh temporary environment.

Datasets, model binaries, secrets, runtime databases, and generated outputs stay
outside Git. A local commit records a snapshot on this PC; pushing to GitHub
requires a separate authorized operation.
