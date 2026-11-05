# Decisions and unresolved choices

## 001: Preserve the existing workspace in place

The audited directory contains three project instruction documents and the
original architecture PDF, with no Git repository. GitHub's branch list was
empty when checked again before initialization.

Initialize local Git on `main` in this directory and configure
`https://github.com/honey-cake7/Forge_Sight.git` as `origin`. This preserves the
existing paths and contents. A local commit and remote configuration do not
upload anything. Push only after user authorization and an actual credential
check. Keep the original PDF locally outside source history.

## 002: Follow the stage roadmap and preserve evidence boundaries

The roadmap overrides the master prompt and reference PDF when they conflict.
Distinguish PC results, Jetson results, and disconnected Jetson end-to-end
evidence. Jetson unavailability blocks device proof, while independent PC work
may proceed after its own gates are reviewed.

## 003: Use one component domain first

Start the dataset prototype with MVTec AD `metal_nut`, subject to Stage 1's
license and split review. Physical camera images form a separate domain and
require controlled real samples. Do not merge unrelated steel/PCB benchmarks
into the metal-nut evaluation.

## 004: Keep vision decisions separate from language advice

Proposed later flow: capture one distinct part, run vision, create a structured
inspection record, apply versioned deterministic grading, and persist locally.
A separate bounded queue feeds structured evidence to an asynchronous Llama
worker running through ExecuTorch on Jetson.

Llama cannot set or override PASS/REVIEW/REJECT. Advice must retain uncertainty
and evidence provenance. A worker timeout must leave inspection usable and
mark advice unavailable. SQLite and a minimal local API/UI remain roadmap
choices for later stages, not implemented features.

## 005: Treat the PDF as a technical reference

Preserve its separate vision/advisory paths, anomaly localization, compact
telemetry, local logging, and evidence-linked procedure retrieval.

Replace or verify its Raspberry Pi/Hailo runtime and CPU-affinity assumptions
for the actual Jetson/JetPack combination. Begin geometry in pixels; homography
alone does not establish a calibrated physical scale. Its two anomaly maps do
not prove named defect types, certified grades, or manufacturing causes.
Neither its 8-15 ms/60 FPS figures nor its FP16 and sample-count assumptions
are measured project results. Defer lock-free buffers, SPC, and advanced
retrieval until their complexity is justified at the corresponding stage.

## 006: Defer model selection until compatible runtime tests

EfficientAD is the provisional deployment candidate: teacher/student and
autoencoder discrepancies provide local and global anomaly evidence, with a
training and export-validation cost. PatchCore is the reference alternative:
normal-feature memory banks simplify fitting but incur storage and search
costs. PaDiM is a statistical alternative using patchwise Gaussian models;
covariance storage and spatial consistency need evaluation.

These are design considerations, not measurements. Stage 3 decides using
compatible dependencies and leakage-safe `metal_nut` evaluation. No method is
selected, trained, exported, or benchmarked yet. Defect-type classification
remains a separate requirement.

Primary technical references reviewed during the audit:

- [EfficientAD paper](https://arxiv.org/abs/2303.14535)
- [PatchCore paper](https://arxiv.org/abs/2106.08265)
- [PaDiM paper](https://arxiv.org/abs/2011.08785)

## 007: Preserve actual Llama + ExecuTorch device inference

Llama 3.2 1B Instruct is a candidate subject to licensing/access and actual
device memory/runtime checks. Linux ARM64 CPU execution through XNNPACK is a
feasibility route, not a verified Jetson implementation. Quantization and
KleidiAI behavior must be verified for the chosen versions and device.

Stage 2 requires actual Jetson-generated text, artifact hashes, runtime/model
versions, exact commands, memory, latency, and network state. Exporting a
`.pte` file, running on this PC, or substituting another LLM runtime does not
meet that gate.

Reference: [ExecuTorch XNNPACK documentation](https://docs.pytorch.org/executorch/stable/backends/xnnpack/xnnpack-overview.html).

## 008: Isolate the minimal PC image environment

The existing WSL environment imports CUDA-enabled PyTorch and discovers the
desktop GPU. Preserve it and use its CPython 3.12.14 interpreter to create a
separate project `.venv` without system-package access. Windows-native Python
would create a different environment; using WSL keeps the first image tools on
Linux while remaining explicitly a PC development result.

Substep 0.3 installed only Pillow 13.0.0, pinned by version and the official
CPython 3.12 Linux x86_64 wheel hash. Reading and inspecting images does not yet
require NumPy, OpenCV, matplotlib, PyTorch, or ExecuTorch. Add dependencies only
when their roadmap tasks need them. This lock targets the tested WSL platform,
not Jetson. A second fresh environment reproduced the setup and PNG smoke check.
