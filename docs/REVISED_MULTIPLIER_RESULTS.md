# Revised multiplier: finite Candidate B accepted

Candidate B resolves Candidate A's registered finite stability failure. It does
not complete Workflow 1 or qualify production coupling. Candidate A remains
FAILED, with its source, limits, consumed registration and raw evidence intact.

The new explicit `anysolid.multiplier.coarsened_p1_partition` policy takes every
second corner from the trace with fewer geometric intervals, retaining both
endpoints (shell wins ties). It refines with the primal meshes. Both input
partitions must have interval-spacing ratio at most two; an odd final interval
can give output spacing ratio four. The five physical force/moment modes,
quadrature, loads, geometry, scaling and numerical gates are unchanged.

## Registered evidence

Command, from ANYsolid:

```console
.venv/Scripts/python.exe tools/run_check.py --name workflow1-revised-multiplier --timeout 180 -- python tools/revised_multiplier_study.py --execute
```

Evidence: `evidence/w1/workflow1-revised-multiplier-b1dde87f2a`.
Process wall time 28.031 seconds; exit zero; verified zero remaining processes.
All 18 fresh operator assessments passed, with 12 fresh coupled physical
results and no execution failures. Six independent full-solid reference results
were reused only after source, runtime, array, predicate and raw-line identity
validation; they were not solved again. The registration is consumed.

| Bound | Candidate B maximum | Unchanged limit |
|---|---:|---:|
| Physical output amplification | 16,014.5231 | 1,000,000 |
| Modal traction/couple amplification | 1,257,436.6214 | 5,000,000 |

Candidate A's failing thin 16:16 result was 5,645,155.4093. Its corresponding
Candidate B result is 1,257,436.6214. All three finest physical cases pass;
whole-core displacement errors are approximately 0.260417%. Coarse-case errors
remain recorded. Residual limits remain 1e-9, applicable work/symmetry 1e-10,
resultant imbalance 1e-8, and the registered accuracy allocations are unchanged.
The maximum verified right-defect bound is 0.000132477693. This is a bounded
certificate for the enumerated matrices, not a universal stability theorem or
a recovered-stress uncertainty certificate.

Source identities (SHA-256):

- Policy: `03706a167e6d7ddf77c2afd81e55142273a005abf42e376448af6951a4d515e8`
- Harness: `b55987fc7c9d24f0d4a6c2e035ac4503a13aa88de3706014f0b976bdf9107ed3`
- Manifest: `e3fa2d94d77c924fd502238e46dfe622d4dbc4e19b1fc1aa036ec8b2677202f5`

An independent non-author reviewer checked the counts, all gates, source
identities and effective single-thread runtime and accepted this finite scope.
The reviewer used the same model family; no different-family review is claimed.
The machine-readable decision is `revised_multiplier_disposition.json`.

## Development and installed delivery

The policy has 29 passing refusal, immutability and selection tests. The full
development profile was run with `python tools/dev_checks.py full --timeout 180`;
316 tests passed, with zero failures, errors or skips in 16.875887 process
seconds. Its receipt is `evidence/development/20261027T110804Z-1f5b37aa`.
An isolated Windows CPython 3.11 wheel build, install and `-I` installed policy
smoke passed (`revised-policy-wheel-build-5386f1cfd8`,
`revised-policy-wheel-install-edbb081a50`,
`revised-policy-installed-smoke-3da23b9c5a`). The smoke constructed a real
connector with the installed policy; it did not solve or repeat qualification.

## Remaining gates

Broader engineering and transition-distance qualification, connected beam
physical acceptance and applicable clean-checkout/platform delivery gates remain
open. Historical repeated-load timings describe Candidate A where its
multiplier rows differ; no Candidate B speedup or benchmark equivalence is
claimed. Condensation remains disabled. No merge or publication occurred.

The connected-beam attempt `workflow1-connected-beam-d8b983a20d` took 2.125
seconds and failed after two certificates and the two-RHS host solve, before
physical results were saved. A harness lookup incorrectly used
`native.mesh.materials`; the correct API is
`native.get_material(beam.material_name)`. Both certificates and the numerical
positive-energy assessment passed, but this does not recover physical
acceptance. Its one-attempt registration is consumed; no retry was run.

The earlier shifted membrane fixture has an input interval-spacing ratio of
2.5, outside Candidate B's limit of two. It remains unsupported by this policy;
the limit and original geometry were not changed. The finite Candidate B study
includes separate admissible shifted cases, not this excluded fixture.

## Broader three-case attempt: scientific NO_GO

The separately reviewed command was:

```console
.venv/Scripts/python.exe tools/run_check.py --name revised-broader-physics --timeout 90 -- python tools/revised_broader_physics.py --execute
```

Evidence `evidence/w1/revised-broader-physics-016d398003`: 3.437 process seconds,
zero execution errors and verified zero remaining processes. All three inverse
certificates and positive-energy assessments pass. Mixed shell-chain bending
and S3 width bending pass every physical gate. Two-region/four-transition
bending fails only its external/support work balance: normalized error
`1.0614817842248283e-10` exceeds the unchanged `1e-10` limit. Twice energy is
`3.3333333338025692e-6`, external work `3.333333333448742e-6`, support work zero.
Passing fields, stress and residuals do not waive this failure. The registration
is consumed; no retry or limit change occurred. See
`revised_broader_disposition.json` for final evidence-review status.

### Separate exact work evaluation accepted

Independent inspection identified cancellation in the double-precision quadratic
energy contraction. A distinct retained-only audit was registered, reviewed and
executed; it does not change the matrix, solution, loads, reference or limit:

```console
.venv/Scripts/python.exe tools/run_check.py --name exact-retained-work --timeout 30 -- python tools/exact_retained_work.py --execute
```

Evidence `evidence/w1/exact-retained-work-367854920d`: 0.422 process seconds,
exit zero, cleanup zero. All 33 source/input identities, node/region/free-row
ordering, loads and homogeneous supports were validated. One exact rational
contraction of the saved 810-by-810 matrix (32,241 entries) and actual saved
coefficients gives normalized work error `2.3266364125382088e-11`, below the
same `1e-10` limit. No FE modules, assembly, factorization or solves were used.
The comparison itself is rational, rather than a rounded display comparison.

Independent non-author review accepted the corrected evaluation. The three
enumerated broader finite cases are therefore supported by their unaffected
original checks plus this separate exact work assessment. The original double
evaluation remains FAILED_UNCHANGED; its terminal record was not rewritten.
See `exact_retained_work_disposition.json`. This correction closes no beam,
transition-distance or platform gate.

## Workflow 1 completion blockers

- Connected-beam physical acceptance is unavailable after the consumed harness
  failure. A repaired, separately registered run is needed; it was not retried.
- Existing refined shear controls do not move interfaces or establish an
  independently converged whole-body clamp/end-traction reference. A bounded
  transition-distance study and its larger-system stability route remain to be
  designed and reviewed. Current small-matrix limits were not expanded.
- Full clean-checkout owner/consumer and Windows/Linux Python 3.11–3.14 gates
  have not run. Local Windows 3.11 staged and installed checks are narrower.
- Coupled repeated-RHS timings remain explicitly Candidate A measurements where
  multiplier blocks differ; no new Candidate B performance claim is made.

The historical thin-case failure and coarse shear failures remain evidence.
All numerical limits are unchanged, protected sibling work is unchanged, and
no merge or publication was performed. Workflow 1 is not complete.
