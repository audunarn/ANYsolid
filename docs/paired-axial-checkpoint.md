# Paired axial investigation checkpoint — 27 October 2026

Read prospective `paired_axial_manifest.json` and retained specimen/reference
and isolation helper APIs. New authority is exactly two new solid meshes,
Nx16 and Nx32 with Ny1/Nz8; native axial4 per side remains fixed. Maximum four
solves (one analytic-end control and one coupled solve per mesh), 12000 primary
DOFs, 40 multipliers and one 180 s process. Earlier runs are not repeated.

Plan/acceptance:
1. Validate retained reference and isolation source identities and unchanged
   reference manifests. Log the complete derived reference configuration,
   changing only its levels and prospective dimension bound; construct each
   native/solid/operator specimen once through the retained builder.
2. Reuse the same immutable prepared solid for its analytical-end control and
   coupled solve. Preserve all source/helper authority distinctions. Emit
   matrix dimensions/CSR storage and flushed pre-solve identities.
3. At exactly equal physical quadrature coordinates compare each route to the
   analytical reference and compute actual pointwise coupled-minus-control
   tensor differences, with their own controlling locations. Include every
   x=.25..75 point, no smoothing or tuning.
4. Await parent reviewed-source run authorization, then one bounded command.
   Retain 5% stress, 1% coupled global and 1e-9 residual thresholds. Two paired
   finite cases do not establish a rate, exact mixed-interface reference or
   unique connector attribution; fixed native4 remains a limitation.

Actual finding: retained `specimen` accepts a separate level dictionary and
returns native, prepared solid, both weak operators and tip nodes. It can
therefore supply one identical basis per pair without editing any old source.
Isolation `stress_record`/`end_reactions` are measurement-only helpers; their
old numerical campaign authority is not reused.

Remaining: implement harness, syntax/source identity checks, send ready hashes,
wait for explicit parent preflight authorization. No new numerical run started.

## Ready implementation

New harness syntax checked with `ast.parse`; no numerical solve executed.
Ready source SHA-256:
`3d2dad0c984227d17d06f4a2749cbe96d5e89d3dcddd52fcec90835bbc7b0c8f`.
Prospective paired manifest SHA-256:
`346538f85a8d8fbfa2c5e12123b660d2603c4e1156de95f03c527e632acde71b`.

Reference/isolation source and manifest identities are validated before work.
The complete derived specimen configuration is logged with the new authority
manifest; its old measurement helpers do not admit extra solves. The identical
prepared object and unchanged cache signature are checked across both routes.
Both physical quadrature coordinates and fixed ROI masks must match exactly.
Paired tensor deltas are computed pointwise and retain their own controlling
coordinates, coupled/control values and signed differences.

CSR array sizes are logged for solid/native stiffness, the physical interface
operator and the reduced control stiffness. These are matrix storage values,
not process memory or factor storage estimates. Every route has a flushed
pre-solve record and a complete result before the next solve. Unexpected
startup/serialization/implementation exceptions stop further numerical work;
no automatic retry is present. Scientific accuracy failures retain their
flags and references and do not alter the registered four-solve sequence.

## Authorized execution

Parent explicitly confirmed "Preflight reviewed, run authorized" after
independent source/math review of the common prepared object, derived
configuration and pointwise-delta construction.

Exact command:

`.venv/Scripts/python.exe tools/run_check.py --name paired-axial --timeout 180 -- python tools/paired_axial.py`

Evidence: `evidence/w1/paired-axial-03080fe925`. Completed exit 0, two pairs,
exactly four solves, zero execution failures, no retries. Process wall
6.436999999998079 s under the 180 s bound; outer receipt verified zero
remaining owned processes. A single upstream informational stderr line was
retained: `Transforming over 1000 elements to C_CONTIGUOUS.` No error traceback
occurred. Full JSONL identities/configurations, pre-solve prefixes, physical
arrays, coefficient states, tensor differences and controlling locations are
preserved with the process identity/receipt.

Executed source SHA-256:
`3d2dad0c984227d17d06f4a2749cbe96d5e89d3dcddd52fcec90835bbc7b0c8f`.
Executed paired manifest SHA-256:
`346538f85a8d8fbfa2c5e12123b660d2603c4e1156de95f03c527e632acde71b`.
All old reference/helper source and manifest identities matched. The two
routes shared the exact same prepared solid object and cache signature within
each pair; quadrature coordinates and complete interior masks matched exactly.

## Registered accuracy and actual paired differences

All values below are dimensionless errors using the unchanged 0.3 Pa axial
and 0.0075 Pa shear scales. All quadrature points x=.25..75 were retained:
4224 per route for Nx16 and 8448 for Nx32. Both control and coupled routes
meet the retained 5% stress and 1e-9 residual criteria on each new mesh;
coupled tip/rotation/energy also meet their fixed 1% criteria.

| Nx | control axial | control shear | coupled axial | coupled shear | pointwise delta axial | pointwise delta shear |
| --- | --- | --- | --- | --- | --- | --- |
| 16 | .001677463642 | .043960265716 | .001794986523 | .045649495127 | .000230746528 | .009337180656 |
| 32 | .000726221019 | .013604474687 | .000786822282 | .014125388532 | .000120707923 | .001779078040 |

The final two columns are maxima of actual pointwise coupled-minus-control
tensors at identical samples, not differences between separately attained
analytical-reference maxima. At Nx16 the shear-delta witness is
[.7455357142857143,.8571428571428571,.06964285714285716] m:
coupled=.004016109794436479 Pa, control=.004086138649356252 Pa,
signed difference=-7.002885491977362e-5 Pa. At Nx32 it is
[.7477678571428571,.8571428571428571,.09464285714285715] m:
coupled=.0008481472286332725 Pa, control=.0008614903139296526 Pa,
signed difference=-1.3343085296380064e-5 Pa.

| Nx | tip w relative | tip theta relative | energy relative | control equilibrium | coupled equilibrium | coupled constraint |
| --- | --- | --- | --- | --- | --- | --- |
| 16 | .001145593390 | 8.188436387e-8 | .001145585082 | 2.262079413e-11 | 2.325525012e-11 | 6.521795835e-14 |
| 32 | .001143755929 | 1.891853482e-8 | .001143754036 | 1.204591982e-11 | 1.314935102e-11 | 3.103940707e-14 |

No reference, support, physical load, multiplier mode, interface partition,
stress smoothing, threshold or post-hoc sample criterion changed to obtain
these flags. No extra solve was used.

## Dimensions and matrix storage

Native axial4 was fixed: native stiffness shape120x120, 3744 stored nonzeros,
45412 CSR-array bytes. Each coupled model has 20 multipliers. Reported storage
is only data/indices/indptr arrays; it excludes factors, Python overhead and
process RSS. No speedup or memory-saving claim is made.

| Nx | solid / coupled primary DOFs | solid K shape / nnz / CSR bytes | reduced control K shape / nnz / CSR bytes |
| --- | --- | --- | --- |
| 16 | 5049 / 5169 | 5049x5049 / 264669 / 3196228 | 4743x4743 / 246821 / 2980828 |
| 32 | 9945 / 10065 | 9945x9945 / 526141 / 6353476 | 9639x9639 / 508317 / 6138364 |

Physical C is 20x5169 and 20x10065 respectively, 1424 stored nonzeros and
17172 CSR-array bytes in either case. All primary counts are below12000 and
all multiplier counts below40. No dense global nullspace/eigensolve was used.

## Outcome and limits

Handoff state: implemented and verified against the two-pair registered
diagnostic execution/accuracy criteria. Both new control and coupled meshes
meet their fixed numerical targets. These results extend the measured strong
axial solid-discretization sensitivity; the pointwise coupled/control stress
gap is small relative to the fixed stress scales on these two finite cases.
The global displacement/energy errors change little between these two cases
while native axial4 is held fixed; that observation does not establish an
error floor or identify its source.

The controls have analytical end data while coupled states have weak
transitions and finite native discretization, so a residual gap cannot be
uniquely attributed to the connector. These two cases do not establish a
convergence rate, uniform stability, general engineering qualification or an
independently converged reference for the actual mixed-interface problem.
The original failed coupled comparison remains failed and all older evidence
remains unchanged. Production weak coupling remains NO_GO pending parent
scientific adjudication and unmet broader gates. Four-solve authority is fully
consumed; no further numerical work is authorized by this assignment.
