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

## Stage 1.4: Load verified inputs without inventing predictions

`MetalNutDataset` exposes one role from the frozen manifest. On every load,
the file and decoded-pixel hashes must match. An `InspectionInput` carries the
source image, mask, role, and explicitly named ground-truth type. Nothing in
this loader predicts anomalies or severity.

For a normal sample, the zero mask is an explicit representation of the normal
annotation. A missing anomalous mask is instead an error. Real loading passed
for all 176 fitting, 44 validation, and four development samples. The loader
preserves 700x700 source geometry, while final-holdout pixels require opt-in.
Nine new synthetic tests cover changed data/masks, missing annotations,
checksum tampering, role gates, indexing, and normal/anomaly mask behavior.
All 31 current tests passed. Commit `7ff8846` for the prior manifest step was
successfully pushed before beginning this loader work.

Concept checks: Why name the label `ground_truth_type`? Why should a missing
anomalous mask never become an all-zero mask silently?

## Stage 1.5: Inspect real annotations without consuming the holdout

The contact sheet shows a normal fitting image and four reserved development
examples, each beside its mask and red overlay. It was visually inspected:
normal pixels are unchanged by the overlay, and the annotated regions align
with the source images. The title explicitly identifies ground truth rather
than model output. Five new preview tests passed; all 36 tests now pass.

The normal mask is empty. The flip annotation covers most of the nut, while
the other displayed annotations are smaller localized regions. That difference
does not establish which defect is more severe. The recorded areas are source
pixel counts from annotations; no calibration or quality decision is claimed.

Only display tiles are resized. Binary masks use nearest-neighbor resampling,
while originals stay at 700x700. The local output includes source/license
attribution, exact sample paths, manifest fingerprint, mask provenance, and a
record that zero holdout images were displayed.

The manifest step (`7ff8846`) and loader step (`0eada8b`) were each committed
and pushed before proceeding. This third step completes Stage 1's technical
proof and stops at the review gate before mandatory ExecuTorch device work.

## Stage 2.1: Separate a supported route from proof on our hardware

The user accepted Stage 1 and authorized three Stage 2 steps with pushes. Public
sources identify a manually gated Llama 3.2 1B model and a pinned ExecuTorch
1.5.1 source candidate. A source-pinned CPU/XNNPACK route is not evidence of
Jetson GPU use, sufficient RAM, binary compatibility, or generated text.

The user has no Meta Llama access, and the Jetson remains unavailable. Preflight
recorded real WSL host facts and refused the device gate; four new parsing and
guard tests passed. No packages were installed and no model text was simulated.
The three-state distinction matters: source review can be verified while export
is NOT RUN and actual device inference stays BLOCKED - NOT VERIFIED.

## Stage 2.2: A checked recipe is still not an export

The recipe generator writes exact argument lists/configuration without running
commands. Pin both model and ExecuTorch revisions so that future exports do not
silently switch APIs or checkpoints. AST-derived field metadata checks the
configuration against the chosen source without installing the exporter.

Six tests passed. The actual recipe correctly reports missing model access,
weights, checkout, and export environment. No generated model file or text
exists. Dependency installation/locking and actual export remain unverified.
The prior preflight step was successfully pushed as `51cdb0f` before this step.

## Stage 2.3: Capture evidence without promoting it to proof automatically

The capture harness refuses non-Jetson execution, checks native runner identity
at the ELF architecture level, fingerprints local files, and records bounded
process logs, exit/timeout status, elapsed wall time, and sampled RSS. It does
not know from a filename whether a model is Llama or whether printed text is
new generation. Those facts require export/build provenance and text review.

All 52 tests passed. The six capture tests use generic child processes and
synthetic guard inputs, never fake Llama replies. The actual PC capture attempt
was blocked before any runner started; generated text is absent. No source tag,
recipe, exported file, or capture report alone closes the mandatory device gate.

The first two preparation commits (`51cdb0f`, `c06e15e`) were each pushed before
the next step. Stop after the third push for review. The user can request model
access while independent Stage 3 PC work proceeds under an explicit Stage 2
blocker. No Jetson performance or offline success is claimed.

## Stage 2.4: Confirm the downloaded model is the intended source asset

The user obtained access and downloaded five files. A filename alone is not
enough: the checkpoint and tokenizer matched publisher SHA-256 fingerprints,
and the small files matched the pinned revision's Git objects. A portable
reference now lets us repeat local verification without authentication or
network access. No Hub token or credential cache was inspected.

The checkpoint is about 2.47 GB. The original parameter file describes the
selected 1B configuration; the tokenizer has 128,000 valid base entries with
unique tokens/ranks. These checks read bytes and JSON rather than loading a
Python checkpoint. Six integrity tests and the full 58-test suite passed.

Source files are ready for export preparation, but no export or inference was
performed. The separate export environment, native runner build, and actual
Jetson execution remain next-stage evidence, not consequences of a download.

## Stage 2.5: Prepare the conversion workshop

A virtual environment gives this exporter its own tools, so its newer PyTorch
does not replace the GPU tools or the small image environment. The source Git
commit pins the program; the package lock pins its dependencies. CPU wheels
are sufficient for the startup/config checks performed here and avoid a second
CUDA stack. This does not establish how fast the eventual Jetson model runs.

Actual checks passed: CPU matrix multiplication returned 11.0, source/installed
schemas matched the reference hash, our recipe became a real upstream LlmConfig,
and the pinned checkout's exporter printed its actual help with exit code zero.
A fresh temporary installation from the lock repeated those checks. Full
inventories show both older environments unchanged; all 59 project tests pass.
The CPU build suffix is now recognized without accepting another release.

Optional TorchAO GPU libraries reported load warnings. These did not prevent
startup, but quantization compatibility remains unproven until real conversion.
No checkpoint was loaded, no model exported, and no text generated. Next:
attempt the real export and inspect its result before building a device runner.
