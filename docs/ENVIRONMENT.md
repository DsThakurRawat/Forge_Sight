# Observed environment

This is an audit record, not a dependency lock or a fresh-install procedure.
No packages were installed during Stage 0.1 or Substep 0.2.

## Windows shell

- Python 3.10.11, AMD64.
- Executable: `C:\Users\RF AND SIMULATION\AppData\Local\Programs\Python\Python310\python.exe`.
- `sys.prefix == sys.base_prefix`: no active virtual environment.
- pip 23.0.1; Git 2.56.0.windows.2.
- Checked packages absent: torch, torchvision, executorch, anomalib, OpenCV,
  NumPy, ONNX Runtime, TensorRT, and the checked PDF-reading libraries.
- `py -0p` reported no registered Pythons even though `python` runs. Resolve
  interpreters explicitly rather than assuming the launcher selects correctly.

Read-only inspection commands from PowerShell:

```powershell
Get-Command python,git,wsl,nvidia-smi
python -B --version
python -B -m pip --version
git --version
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
```

## Existing Ubuntu WSL environment

| Component | Observed value |
| --- | --- |
| Interpreter | `/root/pytorch-env/bin/python3` |
| Python | 3.12.14 |
| Environment prefix | `/root/pytorch-env` |
| PyTorch | 2.6.0+cu124 |
| torchvision | 0.21.0+cu124 |
| NumPy | 1.26.4 |
| PyTorch CUDA build | 12.4 |
| `torch.cuda.is_available()` | `True` |
| `torch.cuda.get_device_name(0)` | `NVIDIA RTX 2000 Ada Generation` |

ExecuTorch, anomalib, OpenCV, ONNX Runtime, and TensorRT were absent in this
environment. The observations apply to this interpreter, not every installed
environment on the machine.

To repeat the check, enter the existing distribution from PowerShell:

```powershell
wsl -d Ubuntu
```

Then, in its Linux shell:

```sh
/root/pytorch-env/bin/python3 -B - <<'PY'
import sys
import torch
import torchvision
import numpy

print('Python:', sys.version)
print('Executable:', sys.executable)
print('torch:', torch.__version__)
print('torchvision:', torchvision.__version__)
print('numpy:', numpy.__version__)
print('PyTorch CUDA build:', torch.version.cuda)
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('GPU:', torch.cuda.get_device_name(0))
PY
```

The recorded check establishes importability and CUDA device discovery. It does
not prove a model executes correctly or establishes any performance result.
PyTorch's CUDA build version is not proof that a standalone CUDA toolkit is
installed. WSL runs on the PC's x86_64 CPU and desktop GPU, not Jetson ARM64.

## Remaining environment work

Substep 0.3 must select an isolated project environment and a minimal dependency
set, verify it, and record reproducible commands. Preserve the existing WSL
environment. Do not copy an unrelated environment's entire package inventory
and call it the project's tested requirements. Jetson dependencies need a
separate compatibility decision after the device audit.
