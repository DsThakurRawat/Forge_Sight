# Stage 2: Llama through ExecuTorch on the actual Jetson

Reviewed 2026-11-05 (Asia/Calcutta). Stage 2 is BLOCKED - NOT VERIFIED.
Stage 1 was reviewed by the user's request to continue. No export, Llama
generation, device benchmark, or offline inference has been performed.

## 2.1: Candidate and prerequisites

`configs/edge_llama.json` pins a preparation candidate, not a working deployment:

| Item | Selected reference |
| --- | --- |
| Model | `meta-llama/Llama-3.2-1B-Instruct` |
| Model revision | `9213176726f574b556790deb65791e0c5aa438b6` |
| Model format for native exporter | Original checkpoint, params, and tokenizer |
| ExecuTorch | Release `v1.5.1`, commit `3b60683923245cf472b7323426920e15623ba361` |
| Backend | XNNPACK on ARM64 CPU |
| Candidate quantization | Dynamic INT8 activations / INT4 weights, group 128; embedding 4-bit/group 32 |
| Initial lengths | Export sequence 128; context 512, subject to actual validation |

Primary source review:

- [Model API](https://huggingface.co/api/models/meta-llama/Llama-3.2-1B-Instruct)
  supplied the revision, original file list, and `manual` access gate. The user
  explicitly reports having no Meta Llama access. No credentials were requested
  or inspected and no weights were downloaded.
- [Model license](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct/blob/9213176726f574b556790deb65791e0c5aa438b6/LICENSE.txt)
  is the Llama 3.2 Community License with its Acceptable Use Policy, rather than
  the dataset's Creative Commons license. Review attribution/notice, license-copy,
  display, and redistribution conditions before shipping model artifacts.
  Access/license acceptance must occur through the user's publisher account.
- [ExecuTorch release](https://github.com/pytorch/executorch/releases/tag/v1.5.1)
  and its [tag reference](https://api.github.com/repos/pytorch/executorch/git/ref/tags/v1.5.1)
  supplied the pinned version and commit. PyPI's top-level API reported 1.6.0
  while GitHub's latest-release API reported 1.5.1. Record this source difference;
  use the pinned 1.5.1 source rather than combine latest instructions arbitrarily.
- [Pinned package metadata](https://pypi.org/pypi/executorch/1.5.1/json) lists
  CPython 3.12 Linux x86_64 and AArch64 wheels, Python >=3.10/<3.15, and newer
  numerical/export dependencies than the existing shared PyTorch environment.
  Package availability alone does not establish Jetson ABI or runtime support.
- [Pinned XNNPACK example](https://github.com/pytorch/executorch/blob/3b60683923245cf472b7323426920e15623ba361/examples/models/llama/config/llama_xnnpack.yaml)
  provides the quantization/backend basis; the candidate retains those settings.
  [Pinned export schema](https://github.com/pytorch/executorch/blob/3b60683923245cf472b7323426920e15623ba361/extension/llm/export/config/llm_config.py)
  and [export entry point](https://github.com/pytorch/executorch/blob/3b60683923245cf472b7323426920e15623ba361/extension/llm/export/export_llm.py)
  are the authority for recipe keys, not snippets targeting a different revision.

Use a separate export environment when dependencies and model access are ready;
do not upgrade the image `.venv` or shared `/root/pytorch-env`. There is no tested
export-environment lock or completed installation yet.

## Why this route

The smallest proposed instruct model reduces the initial memory burden compared
with 3B, without promising it fits the unknown Jetson variant. INT4 may lower
weight memory but still requires tokenizer, KV cache, runner, vision, and OS
memory. Generated quality and quantization effects need actual tests.

CPU/XNNPACK is the first feasibility route documented for ARM64. GPU execution
and native binary compatibility remain separate investigations; do not assume
Jetson's GPU is used by this choice. Source export and target execution may
happen on different machines. Build the target runner for the actual Jetson
userspace/toolchain rather than copy a WSL x86 binary or Raspberry Pi setup.

The [official ARM tutorial](https://docs.pytorch.org/executorch/stable/raspberry_pi_llama_tutorial.html)
is a Raspberry Pi reference, not Jetson validation. Its toolchain and system-
library modification instructions are not adopted. No JetPack/glibc upgrade,
CPU affinity, or performance target has been selected without device facts.

## Read-only preflight

```powershell
wsl -d Ubuntu --exec .venv/bin/python -B -m forgesight.edge_preflight --require-jetson
```

On this PC it exits 2 with `NOT_VERIFIED_JETSON_ORIN_NANO`, records x86_64,
Python 3.12.14, absent ExecuTorch/export packages in the image interpreter, and
`inference_status=NOT_RUN`. The actual local report is ignored at
`artifacts/edge/pc_preflight.json`. Four parsing/guard tests passed. Their
synthetic host facts are unit tests, not Jetson evidence.

Later, on the Jetson in the project checkout:

```sh
python3 -B -m forgesight.edge_preflight --require-jetson --output artifacts/edge/jetson_preflight.json
```

A matching ARM64/device-tree/L4T identity is only a candidate for execution.
Verify exact module/RAM, JetPack packages, available memory/storage, and camera
separately. Preflight never claims successful inference or network disconnection.
It reads route tables without contacting an external service.

## Current blockers and next tasks

1. Device unavailable: exact Jetson facts, target build, and generated text absent.
2. User has no Meta Llama access: checkpoint/tokenizer/license access unresolved.
3. Export environment, dependency closure, model export, and runner build not run.

Substep 2.2 prepares and validates source-pinned recipe files. Substep 2.3
prepares a device-only capture harness. Those tools can be tested on the PC,
but Stage 2 cannot be DONE until actual Llama text is generated through
ExecuTorch on the Jetson and its provenance/measurements are reviewed.
