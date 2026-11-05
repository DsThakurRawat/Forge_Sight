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
