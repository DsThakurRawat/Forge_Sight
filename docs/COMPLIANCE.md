# Requirement evidence

No challenge requirement is marked satisfied by repository setup alone.

Stage 2.5 verifies an isolated desktop exporter environment, real CLI startup,
and structured configuration parsing. No checkpoint was loaded or converted;
no model inference was performed. Optional GPU-library warnings are retained.
All device, quality, performance, and offline acceptance requirements below
remain open.

| Requirement | Status | Acceptance evidence needed |
| --- | --- | --- |
| Real surface anomaly detection | NOT VERIFIED | Real model scores/maps and held-out evaluation |
| Defect type | NOT VERIFIED | Same-domain labeled evaluation; retain `unknown` when unsupported |
| Severity and operator decisions | NOT VERIFIED | Versioned deterministic rules and behavior tests |
| Useful operator recommendations | NOT VERIFIED | Actual evidence-linked advice with uncertainty and next checks |
| Every-inspection history | NOT VERIFIED | Persisted PASS/REVIEW/REJECT/error records, restart and duplicate checks |
| One event per physical part | NOT VERIFIED | Capture/re-arm gate; repeated frames do not inflate counts |
| Exact eligible edge hardware | BLOCKED - NOT VERIFIED | Device-side module/RAM/architecture/JetPack inventory; device currently unavailable |
| Llama-family inference via ExecuTorch on Jetson | BLOCKED - NOT VERIFIED | Actual locally generated text plus model/runtime/artifact provenance and measurements |
| Physical camera validation | BLOCKED - NOT VERIFIED | Controlled real samples captured and inspected on Jetson |
| Offline edge operation | BLOCKED - NOT VERIFIED | Disconnected cold start and real end-to-end device run |
| Real-time performance | NOT VERIFIED | Device vision/advice latency, distinct parts/minute, RAM and thermal observations |
| Reproducible source/application/report/video | NOT VERIFIED | Reproducible setup, actual application, report, demo and repository delivery |

HailoRT is not applicable to the proposed Jetson route without Hailo hardware.
No calibrated millimeters, certified industrial grades, PDF performance,
factory root causes, or actual offline compliance are claimed.

Development-time access to GitHub or documentation is separate from the later
offline runtime test. Dataset/model licensing and redistribution conditions
must be checked before acquisition and publication of those artifacts.

## Dataset review evidence

Stage 1.1 documented the MVTec AD source, noncommercial license scope,
attribution, expected image/mask layout, and evaluation partition policy in
`docs/DATASET.md`. Review, acquisition, actual image/mask validation, and hashed
extraction are verified. The frozen split, role-based loader, and development
previews are verified on the PC. The project holdout excludes four
development images from the original test set and must be reported accordingly.
The exact archive URL was not captured; the user confirmed the publisher's
download flow and the archive fingerprint is recorded. No requirement above
is satisfied merely by acquiring or validating benchmark files.

Stage 1 gate evidence: 176 fit, 44 normal validation, four development, and 111
final-holdout samples; zero exact byte/pixel duplicate image groups; 36 passing
tests; real image/mask/overlay contact sheet inspected. Preview ground truth is
explicitly labeled, and zero final-holdout images were displayed. This completes
data/input preparation, not model detection, type classification, severity,
Jetson runtime, or offline compliance.

## Stage 2 source/preflight evidence

Model/runtime candidate pinned and sources reviewed in `docs/EDGE_RUNTIME.md`.
The initial review recorded no Meta Llama access (cleared in Substep 2.4).
Actual PC preflight identified x86_64 and
refused a device-only operation. No weights, model export, runner build,
generated text, device timing, or disconnected execution is verified.

Source-pinned recipe generation and device-only capture guards are now tested.
All 52 project tests passed, including generic process log/failure/timeout tests.
A real PC capture attempt recorded no runner process and no generated text.
Recipe/harness readiness is separate from actual export/runtime proof. A
successful capture remains pending review; neither source tags, artifact
filenames, stdout, nor an operator network declaration automatically pass the
Llama/ExecuTorch or offline requirements.

Substep 2.4 verified all five acquired original model files against the pinned
publisher revision. User-confirmed access and local source assets are now
verified; fingerprint metadata is committed and all model bytes stay ignored.
All 58 tests passed. This clears the source-asset blocker only: no model export,
generated text, native target build, device execution, or offline proof exists.
