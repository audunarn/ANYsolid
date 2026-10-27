# Coupling feasibility harness checkpoint

2026-10-26: read prospective `coupling_feasibility_manifest.json`, current host
registered-v2 integration, and controlled specimen helper in
`ANYsolver/tests/test_solid_coupling.py`. The helper fixes t=.2; the harness
will import it read-only, reuse it directly for default thickness, and rebuild
controlled traces/solid geometry when thickness changes. Native constraints
use the public constraint transformation. Native mass uses public assembly;
solid vector mass uses upstream skfem assembly on the prepared basis only.

Plan/acceptance:
1. Add a standalone JSONL CLI and physical bending pilot. Record exact manifest
   identity, physical measurements, fixed references, errors, registered
   residuals and failures; no tuning or promotion.
2. Implement seven prospectively fixed normed Schur spectra with bounded
   primary/multiplier dimensions. This route will remain unexecuted until
   parent source/math review.
3. Run one bounded bending pilot through `tools/run_check.py` (180 s). Repair
   implementation defects only, at most three attempts; retain scientific
   failures and partial records without changing references.

Actual findings: two Q4 native strips span x=-1..0 and x=1..2; P2 solid spans
x=0..1. Both interface traces have length 1 and five section modes. Explicit
P1 multiplier knots [0,1] give 10 rows per interface, 20 total. Host already
accepts per-case immutable `ResidualScales` and reports registered residuals.
Remaining: implement harness, run only bending pilot, inspect evidence, handoff.
No blocker. Parent owns all acceptance, manifest and promotion decisions.

## Implementation and bounded bending pilot handoff

Implemented `tools/coupling_feasibility.py` with `--case bending|spectrum|all`,
flushed JSONL identity/start/result/failure/summary records. Identity includes
manifest/harness/fixture SHA-256 and exact numerical-library versions. Each
physical result retains reference inputs, measurements, errors, stress sample
coordinates/tensors, registered residual report and historical diagnostics.
Only the authorized bending route has been executed.

Exact commands:

1. `.venv/Scripts/python.exe tools/run_check.py --name bending-pilot -- python tools/coupling_feasibility.py --case bending`
   failed after solve during JSON emission on a NumPy int32 value. Evidence:
   `evidence/w1/bending-pilot-53346dfd6b`, process wall
   2.0159999999959837 s. Full traceback and partial JSONL retained.
2. Repaired JSON encoding for NumPy scalars/arrays and mapping diagnostics.
   `.venv/Scripts/python.exe tools/run_check.py --name bending-pilot-repair -- python tools/coupling_feasibility.py --case bending`
   completed exit 0, one case / zero failed checks, process wall
   2.0310000000026776 s. Evidence:
   `evidence/w1/bending-pilot-repair-6f4764781a` with full stdout/stderr,
   process receipt and exact source/reference identity. No references changed.

Measured 183 primary DOFs / 20 multipliers. Tip w values
[-0.0044999999999310245, -0.004499999999921585] m; theta_y
[0.002999999999965779, 0.0029999999999686697] rad. Twice energy
1.99999999996927e-6 Nm (native 1.3333333333016044e-6, solid
6.666666666676655e-7). Relative w/theta/energy errors
1.74255e-11 / 1.14070e-11 / 1.53652e-11. Maximum stress error divided by the
registered 0.1 Pa scale: 8.58841e-12, over 52 interior quadrature samples.
Registered equilibrium/constraint maxima: 1.47917e-11 / 3.86071e-14.
Legacy constraint diagnostic remains 4.15584e-4; it was not erased or retuned.

Spectrum code assembles native density-one consistent mass through public
API, vector L2 mass through pinned scikit-fem 12.0.2 basis, and the registered
V/Q norms. It forms only the 20x20 Schur matrix with factored sparse solves,
checks symmetry, and reports generalized eigenvalues and minimum-positive
beta as diagnostics. Parent adopted characteristic L=1 m interface width,
distinct from 3 m specimen span; the code requires the explicit prospective
`stability_diagnostic.characteristic_length_m` manifest field.

State: bending implemented and verified against the fixed pilot criteria;
spectrum implemented but UNEXECUTED pending parent source/math review.
No seven-case campaign, production promotion, uniform inf-sup claim, locking
qualification or extra numerical run was performed. Only the two assigned
source/checkpoint paths were edited.

## Continued bounded spectrum and physical patch assignment

Before execution: spectrum now checks numerical symmetry of V and establishes
SPD with bounded dense Cholesky (maximum reduced dimension 1500), retaining
the sparse n-by-20 block RHS solve and 20-by-20 dense generalized eigensolve.
`beta_full` is zero if any nonpositive eigenvalue occurs; the distinct
minimum-positive beta and the complete spectrum remain recorded. Native mass
is labelled density-stripped geometric Q4 rotary/drilling verification norm,
not a dynamic capability. Constructed E/nu and trace thickness are checked
against the prospective manifest before analysis.

Added `--case patches` for the four cases in the independently registered
`physical_patch_manifest.json`. The harness constructs every required solid
y/z surface group, explicit physical side loads, consistent native edge
forces/moments and transverse top/bottom-couple area moments, and exact
nonzero left boundary values. No loads are generated from K times an exact
displacement. Native full-field, energy and independent stress comparisons
retain the manifest's thresholds and registered residual scales.

Prospective contract delta reported before execution: production Q4 source
`e4_pl_element.py:5473` applies transverse shear factor 5/6. The proposed
uniform 3D transverse-shear exact field has gamma=.002, G=500, t=.2, giving
native Q=(5/6)*G*t*gamma=1/6 N rather than the manifest's 0.2 N. The prescribed
native loads and exact reference therefore do not form an exact production
shell patch. Parent decision pending on running that case as a deliberate
diagnostic mismatch. References and physical loads remain unchanged.

No new spectrum or patch execution had occurred at this checkpoint.

## Completed continued assignment

Parent adopted the transverse constitutive delta prospectively, archived the
original patch manifest, and marked transverse shear
`NOT_EXECUTED_CONSTITUTIVE_MISMATCH`. The CLI emits this as an unqualified,
non-success record before any specimen setup/solve. It cannot count four
passing cases. Parent reserves a distinct compatible transverse-shear
convergence reference for future registration; no tolerance was changed.

The physical load signs were checked analytically before execution:
in-plane shear uses right-edge positive y force and opposite x side forces;
twist has sigma_xy=E*a*z, right-edge moment_x=-E*a*t³/12 and y-side
moment_y=+/-E*a*t³/12. Both fields have zero other strain/stress components
as specified. The Poisson field has only sigma_xx=5 Pa. All prescribed left
values retain the exact nonzero field, and all natural loads come directly
from these physical surface/line force and moment definitions.

### Seven-case normed spectrum

Command: `.venv/Scripts/python.exe tools/run_check.py --name coupling-spectrum -- python tools/coupling_feasibility.py --case spectrum`

Evidence: `evidence/w1/coupling-spectrum-5f7f456dea`. Completed exit 0;
7 diagnostic cases / 0 failures; process wall 3.936999999998079 s. All V
symmetry/Cholesky checks passed, all 20 generalized eigenvalues were positive
in every case. Maximum reduced dimension 1251, within the registered 1500
dense-SPD bound; maximum H relative asymmetry 3.28418e-13.

| nshell | nsolid | thickness m | beta_full |
| --- | --- | --- | --- |
| 1 | 1 | .2 | .263841409755784 |
| 2 | 1 | .2 | .2634543799468347 |
| 4 | 1 | .2 | .27808005100124017 |
| 1 | 2 | .2 | .32871562595323983 |
| 1 | 4 | .2 | .3726131044312627 |
| 1 | 1 | .1 | .13709938005281833 |
| 1 | 1 | .05 | .06928201377248941 |

These norm-dependent finite-case values establish neither a uniform inf-sup
bound nor locking. Full H/Q/eigenvalues and block RHS dimensions remain in
the flushed JSONL. The verification mass and V do not alter physical K.

### Three proper physical patches and one withheld case

Command: `.venv/Scripts/python.exe tools/run_check.py --name coupling-physical-patches -- python tools/coupling_feasibility.py --case patches`

Evidence: `evidence/w1/coupling-physical-patches-af6a055a4b`. Completed exit 0;
3 executed / 0 failures / 1 withheld; process wall 2.2180000000007567 s.
Each executed case passed native full-field, energy, independently computed
tensor stress and registered residual criteria. Summary deliberately reports
`passed=false` for all four requested cases and `executed_cases_passed=true`
for the three actually executed. Transverse shear remains unqualified.

| Case | maximum native field scaled error | energy relative error | stress scaled max error |
| --- | --- | --- | --- |
| Poisson membrane | 1.12107e-12 | 2.54426e-14 | 8.27782e-14 |
| In-plane shear | 2.89659e-12 | 1.44199e-13 | 4.03757e-13 |
| Twist | 1.91845e-11 | 2.90109e-13 | 5.67668e-12 |

No implementation retry or scientific retuning occurred in these two runs.
Raw stdout/stderr, full reference and candidate identities, exact commands,
wall receipts and verified owned-process cleanup are preserved by the outer
harness. Current harness SHA-256:
`2d078957529a062e158086b6535899280ea38c8f8945a432ae511228bb09af14`.
Executed patch-manifest SHA-256:
`1799b9f7af37aa6c94f1ba9473f660b7bbd852a0851372f84283d61fafda98d7`.

Handoff state: implemented and verified against assigned diagnostic/patch
criteria, with one explicit constitutively incompatible requirement withheld.
Parent source review, broader convergence and promotion remain separate.
Production weak coupling remains NO_GO. No source outside the owned harness
and checkpoint was edited, and no `--case all` execution occurred.
