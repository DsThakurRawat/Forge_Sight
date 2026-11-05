# Learning log

## Stage 0.1: Learn what exists before changing it

The PC is a Windows x86_64 workstation with an RTX 2000 Ada GPU. Its Ubuntu WSL
environment can import PyTorch and discover that GPU. WSL is still running on
the PC; it does not turn desktop results into Jetson ARM64 evidence.

A working `python` command does not guarantee that a Python launcher or another
shell uses the same interpreter. Record the executable path and inspect that
environment's packages explicitly.

No local repository existed. The original four files are valuable local work
even though the remote repository has no branches. The user later confirmed
that the Jetson is unavailable.

## Stage 0.2: Protect local work with honest version control

- `git init -b main` creates repository metadata and names the initial branch.
- `git remote add origin URL` stores a remote address; it does not connect local
  history to remote history or transfer files.
- `git add` selects the exact contents for the next snapshot.
- `git diff --cached` reviews that selected content.
- `git commit` creates a local snapshot; `git push` is a separate upload.
- `.gitignore` keeps matching untracked files out of ordinary staging. It does
  not remove already tracked secrets and is not a backup system.

The PDF is retained locally and ignored; the instruction Markdown files and
new project documentation belong in the initial source snapshot. Raw data,
weights, runtime history, generated artifacts, and credentials stay outside
ordinary staging.

`.gitattributes` keeps text line endings consistent between Windows and WSL.
The original roadmap's intentional Markdown hard breaks have a file-specific
whitespace exception, so validation does not require changing that reference.

Checks for this step: inspect the staged inventory, validate ignore examples
without creating data/secret files, check staged whitespace, compare original
file hashes, and inspect final Git status. Report actual outcomes in the step
response rather than inventing a future commit hash inside these notes.

Concept checks:

1. Does adding `origin` or making a local commit upload anything to GitHub?
2. If a secret was already committed, does adding it to `.gitignore` erase it
   from history?

## Stage 0.3: Build a small repeatable image environment

An isolated virtual environment gives this project its own packages. Creating
it with an existing environment's Python does not copy that environment's
installed packages by default. Calling `.venv/bin/python` explicitly avoids
depending on shell activation or an ambiguous `python` command.

`requirements.txt` pins Pillow's version and the exact Linux x86_64 CPython 3.12
wheel hash. `pip install --require-hashes --only-binary=:all:` checks artifact
integrity and avoids an unplanned source build. Python, OS libraries, and GPU
drivers are separate prerequisites, not captured by this package pin.

`scripts/check_environment.py` contains one `main()` function. It checks that a
venv is active and the user package site is disabled, then encodes and decodes
a tiny in-memory RGB image and compares every pixel byte. This tests the image
codec and Python environment, not anomaly detection. `pip check` separately
checks installed dependency consistency.

Both checks passed in the project environment and a second fresh temporary
environment. The project environment cannot see the shared environment's
PyTorch, torchvision, NumPy, ExecuTorch, or OpenCV packages.

Concept checks:

1. Why pin both a package version and a wheel hash?
2. What does a successful PNG round trip prove, and what does it leave untested?

## Stage 1.1: Understand data roles before opening images

Anomaly detection asks whether appearance differs from normal. Classification
asks which learned class applies. A folder label is ground truth for checking
a prediction, not evidence that a model can predict that type.

An image shows appearance; a mask marks anomalous pixels for localization
evaluation. The publisher's evaluation code pairs anomalous images with masks
using the defect folder and filename stem. Normal samples do not have mask
files; a loader can represent their ground truth as an all-zero mask. It must
not treat a missing anomalous mask as a normal sample.

Fitting learns from the training partition. Validation supports configuration
and threshold choices. Final evaluation checks the frozen system. Repeatedly
adjusting settings after examining final test results leaks information from
evaluation into development and makes performance claims optimistic.

Stage 1 requires real defective previews for learning. Reserve four development
examples deterministically before inspecting them; exclude them from the final
holdout. This gives an expected custom 111-image holdout, not an untouched
115-image official test set. Our 44-image normal-only validation partition can
help calibrate false alarms but cannot establish defect recall. No files have
actually been assigned yet; these are a recorded protocol and expected counts.

The dataset has noncommercial licensing conditions and attribution obligations.
Keeping raw data out of Git is our repository policy, not a claim that all
redistribution is prohibited. The detailed source review is in `DATASET.md`.

Concept checks:

1. Why must an image used to debug an overlay be excluded from the untouched
   final holdout?
2. Why can't normal-only validation tell us how many defects the system misses?

## Stage 1.2: Verify the actual archive before using it

The real archive contains 335 inspection images and 93 masks. Images are RGB;
masks are grayscale, with 0 for normal pixels and 255 for anomalous pixels.
Mask brightness is a binary annotation, not a probability or severity score.

SHA-256 fingerprints the archive bytes. Matching hashes prove our copy matches
the supplied file; they do not independently authenticate publisher origin.
Here the user confirmed downloading through MVTec, while the exact archive URL
and publisher checksum were unavailable. Keep those evidence types separate.

`scripts/audit_metal_nut_archive.py` checks archive entries and fully decodes
the PNGs without displaying them. `canonical_path()` prevents path traversal;
`audit_archive()` checks structure/counts/pairing and records file/pixel hashes;
`extract_audited_archive()` writes into a new directory and verifies each file.
Normal images have no mask files; anomalous images must have nonempty masks.

Fourteen temporary synthetic tests in `tests/test_archive_audit.py` exercised
valid and malformed archives. The actual dataset was then independently audited
and extracted: 430 regular files, including the original license and readme,
matched their hashes. The test fixtures are not claimed as inspection samples.

No split or preview exists yet. First create a frozen manifest and check
duplicate content, then use only the designated development examples to learn
image/mask visualization. Structural validation does not demonstrate detection
accuracy or camera generalization.

Concept checks:

1. What does matching the original archive's SHA-256 prove about our copy?
2. Why is a missing anomalous mask an error, while normal samples have no mask?

## Stage 1.3: Freeze sample roles before learning from previews

`forgesight/data_manifest.py` verifies the current files against acquisition
hashes, rejects exact image-byte or decoded-pixel duplicates, and ranks portable
relative paths with the recorded seed/version. The manifest stores metadata,
not raw dataset pixels. It assigns 176 fitting, 44 normal validation, four
development, and 111 final-evaluation samples.

The real dataset had zero byte/pixel duplicate image groups. This does not rule
out near-duplicate photographs or prove physical-part independence. A second
build in memory reproduced the manifest bytes. Eight split tests protect
order-independent assignments, role integrity, mask pairing, duplicate
rejection, and path boundaries; all 22 current tests passed.

Concept checks: Why must two runs produce identical role assignments? Why do
zero exact duplicates still leave physical-part independence unverified?
