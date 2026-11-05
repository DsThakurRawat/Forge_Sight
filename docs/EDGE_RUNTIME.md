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
  initially reported having no Meta Llama access. In Substep 2.4 the user obtained
  access and downloaded the pinned source assets. No credentials were requested
  or inspected by the verification tools.
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
2. Source model access/download blocker cleared in 2.4; user-confirmed access
   and all five publisher-matching local source files are recorded below.
3. Export environment, dependency closure, model export, and runner build not run.

Substep 2.2 prepares and validates source-pinned recipe files. Substep 2.3
provides a device-only capture harness. Those tools can be tested on the PC,
but Stage 2 cannot be DONE until actual Llama text is generated through
ExecuTorch on the Jetson and its provenance/measurements are reviewed.

## 2.2: Source-pinned export/build recipe, not an executed export

`forgesight/edge_recipe.py` renders two ignored files under
`artifacts/edge/export_recipe_v1/`: `export_config.yaml` and `recipe.json`.
The YAML file uses valid JSON syntax (a YAML subset), with the candidate's
checkpoint paths, XNNPACK/quantization settings, BOS/EOS metadata, and lengths.
The JSON recipe keeps commands as argument lists plus working directories,
including checkout/download, export, and native target build steps. It never
executes those commands or installs anything.

`configs/edge_upstream_schema.json` records field names parsed with Python's
AST parser from the pinned upstream dataclasses, their source commit, and the
exact source-file fingerprint. The upstream code was read, not imported or
executed. Recipe validation checks these keys and basic length/backend
constraints; it is not a full Hydra instantiation or successful export test.

The reviewed [native runner instructions](https://github.com/pytorch/executorch/blob/3b60683923245cf472b7323426920e15623ba361/examples/models/llama/README.md)
use the `llm-release` and `llama-release` CMake workflows. Their names were
independently checked in both pinned CMake preset files. They remain NOT RUN
and require an appropriate native Jetson toolchain, dependency environment,
submodules, and CMake supporting those presets. No Pi toolchain is substituted.

```powershell
wsl -d Ubuntu --exec .venv/bin/python -B -m forgesight.edge_recipe
```

The observed output is `PREPARATION_ONLY_NOT_RUN`, with missing licensed model
files, absent matching source checkout, and no installed export environment.
`ready_to_claim_export` is false. Six recipe tests passed, covering schema
keys, source revision mismatch, lengths, backend substitution, path arguments,
missing input reporting, and existing-output preservation. No `.pte` was created.
The output directory must be new; `--output` can select another ignored path.

After model access, download the original checkpoint/params/tokenizer from the
pinned model revision and retain license notices locally. Verify their actual
hashes, review dependencies in a separate export environment, and validate the
recipe with that installed revision before exporting. Native CPU runner build
and ARM64 ABI checks happen on/for the actual Jetson. This preparation recipe
does not replace the still-missing reproducible installed dependency lock.

## 2.3: Device-only capture, pending real execution

`forgesight/edge_capture.py` collects the same preflight and refuses execution
unless it identifies a Linux ARM64 Jetson Orin Nano candidate. It also checks
the pinned source checkout, nonempty local artifacts, `.pte` extension, and a
native little-endian AArch64 ELF runner. There is no desktop override, alternate
LLM runtime, hosted call, or simulated model response.

On a future real run it fingerprints runner/model/tokenizer/prompt, passes an
argument list directly to the native runner, and saves raw stdout/stderr,
return code, elapsed process wall time, sampled RSS, and preflight before/after.
It bounds execution by timeout and log size. The pinned runner source was
checked for `model_path`, `tokenizer_path`, `prompt_file`, `max_new_tokens`,
`temperature`, and `num_bos`; deprecated generation-length flags are avoided.
The basic prompt is only a runtime smoke test, not the Stage 9 advisory design.

Wall time includes process startup/model loading and is not token latency or
vision latency. RSS is sampled every 50 ms, can miss peaks, and excludes other
processes. A route-table snapshot and operator-reported network state do not
prove offline operation; `offline_status` remains NOT VERIFIED. Exact module,
memory sufficiency, tokenizer behavior, model/export provenance, linked backend,
generated content, and device/runtime performance still require actual review.

The report records candidate/requested model IDs, not an automatic inspection
of model identity inside the artifact. A source checkout's HEAD does not attest
how an arbitrary binary was built. Match export/build logs, input/checkpoint
hashes and revisions to the artifact hashes when actual assets exist. Nonempty
stdout can contain echoed prompts or diagnostics, so even a successful process
is only CAPTURED_NOT_VERIFIED; it cannot automatically pass the Stage 2 gate.

Actual PC refusal test:

```powershell
wsl -d Ubuntu --exec .venv/bin/python -B -m forgesight.edge_capture --output artifacts/edge/pc_capture_attempt_v1
```

Observed exit 2 and ignored `run.json`: BLOCKED_NOT_VERIFIED, missing target
identity/source checkout/runner/model/tokenizer, `process=null`, no generated
text, and Stage 2 NOT VERIFIED. No runner process was started.

Only after device audit, model access, real export, and native runner build,
run on the Jetson with paths appropriate to that checkout:

```sh
python3 -B -m forgesight.edge_capture --output artifacts/edge/jetson_capture_v1 --network-state connected
```

Use the actual observed network state; `physically_disconnected` is an operator
declaration, not a software-certified offline result. Output directories must
be new. Failure, timeout, or empty stdout remains FAILED_NOT_VERIFIED; a captured
run still needs its actual text/provenance reviewed. Stage 10 remains the full
offline system gate.

Six new capture tests passed; all 52 project tests passed together. The process
tests use real generic Python children for log/exit/timeout behavior, with no
pretend Llama generation, model artifacts, or Jetson success report.

## Stage 2 gate after these three preparation steps

Preparation tooling and downloaded source assets are verified, but installed
dependency closure, export, target compilation, real generated text, and measured on-device
execution remain BLOCKED or NOT RUN. Stage 2 is not DONE. Keep this gate open
while proceeding with independent PC vision work only after review, as allowed
by the roadmap. The next independent task is Stage 3.1: inspect compatible
PatchCore/EfficientAD baseline options for this PC without consuming the final
holdout. Resume actual Stage 2 execution when model/device access is available.

## 2.4: Actual source-model acquisition verified

The user confirmed access approval and completed the pinned download into
`models/llama3_2_1b/`. The verifier checked public metadata at the exact model
revision, not a moving branch, without reading authentication tokens. All five
files matched the publisher's sizes and object fingerprints. Large LFS objects
were compared using their published SHA-256; small files were compared using
their Git blob IDs. SHA-256 was additionally recorded for every local file.

| File | Actual bytes | Publisher check |
| --- | --- | --- |
| `original/consolidated.00.pth` | 2,471,677,246 | LFS SHA-256 matches |
| `original/params.json` | 220 | Git blob matches |
| `original/tokenizer.model` | 2,183,982 | LFS SHA-256 matches |
| `LICENSE.txt` | 7,712 | Git blob matches |
| `USE_POLICY.md` | 6,021 | Git blob matches |

Checkpoint SHA-256:
`fc17d497df5e4175b3a8acb4f5865b26f7fc1b009b25bef814b95fde10e8a1f3`.
Tokenizer SHA-256:
`82e9d31979e92ab929cd544440f129d9ecd797b69e327f80f17e1c50d5551b55`.
Parameters describe 16 layers, hidden dimension 2048, 32 attention heads,
eight KV heads, and vocabulary size 128,256. The tokenizer contains 128,000
valid base64 token entries with unique tokens and contiguous ranks; reserved
special tokens are separate. No checkpoint deserialization or inference was
used to verify these files.

`manifests/llama3_2_1b_assets.json` commits metadata/fingerprints only. The
weights, tokenizer, license/policy copies, Hub cache, and verification reports
remain local under ignored paths. `configs/edge_llama.json` now records access
granted and source assets verified. This does not prove tokenization during
generation, export correctness, quantized quality, memory fit, or edge execution.

Repeat offline verification against the publisher-checked committed reference:

```powershell
wsl -d Ubuntu --exec .venv/bin/python -B -m forgesight.edge_assets
```

Observed result: five files verified, 128,000 tokenizer base entries,
`ASSETS_VERIFIED_NOT_EXPORTED`, and inference NOT_RUN. Six new tests cover
integrity success, same-size corruption, missing files, path escape, duplicate
tokenizer ranks, and noncontiguous ranks. All 58 project tests passed.

A new ignored recipe at `artifacts/edge/export_recipe_assets_verified/` reflects
the current assets without overwriting the earlier blocked recipe. It reports
an empty missing-model-files list and no access blocker. Actual source checkout,
installed export environment/dependency lock, export, native build, and Jetson
execution are still unverified. Next is a separate Stage 2.5 export-environment
setup/compatibility check; it has not been started by this verification step.
