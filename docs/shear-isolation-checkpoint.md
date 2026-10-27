# Shear isolation investigation checkpoint — 27 October 2026

Read current continuation record and `shear_isolation_manifest.json`. The old
reference harness is unchanged at SHA-256
`475940b3ae0273395e87195698ef10d09c493181aeedd40d47005c7e28089965`;
its reference manifest is unchanged at
`5391fddc78317075bc6f705b4754cbe3fd880418d6fc871394a68363fe0c5163`.
The earlier coupled result remains a failed engineering comparison and will
not be rerun. The empty-RHS guard cannot affect this one-RHS experiment.

Plan and discriminating acceptance:
1. New isolated harness imports the exact old reference_fields/stress_errors
   read-only and validates source/reference identity against retained evidence.
2. For each of four registered meshes, recover analytic nodal-interpolant
   stress and then make one host solid-only solve with exact analytical end
   displacement values at every upstream face DOF, zero loads and free lateral
   surfaces. No native shell or connector is used in these controls.
3. Preserve complete samples/results in flushed JSONL; compare the identical
   fixed x=.25..75 sampling region and scales, and report each controlling
   location. Sum actual K*u prescribed-face coefficients into physical force
   and moment diagnostics using the public physical component/coordinate map.
4. After parent preflight authorization, execute exactly one bounded process,
   at most four solid solves. Completion/discrimination is the outcome;
   original accuracy limits, residual gates and production NO_GO remain.

Actual API finding: SolidRegion.prescribe_dofs accepts individual analytical
values; backend.boundary_dofs selects all P2 face/edge coefficients. Recovery
provides matching physical quadrature coordinates for interpolant/solved data.
End reactions can therefore be measured without modifying product source.

Remaining: implement new harness, submit ready identities for parent review,
then wait for the explicit run authorization before any numerical execution.
No blocker; no new numerical process has started.

## Ready for independent preflight

Implemented the new harness; syntax checked with `ast.parse` only. Numerical
execution is awaiting the parent's explicit preflight-reviewed authorization.
Ready source SHA-256:
`3e9b726f73da71cd0e1d400e8571b28fd008ad2dc6b643e85ae4a4220680ef84`.
Frozen isolation manifest SHA-256:
`95d6031eed7b267184832df4c513257c0aa9104f5134f0a45824859bc09432f4`.

Fingerprint comparison against retained source identities found exactly the
expected changed file, `ANYsolver/src/anysolver/solid_residuals.py`, at
`49c9683b3a4ae43d3a2152a8a867a0cb171bfb6519de6e1ee0ddf1c52f0856d0`.
All other recorded product-source fingerprints still match. The new harness
checks reference source and manifest identities before numerical evaluation,
records imported core module identities and versions, and explicitly checks
that the original-mesh quadrature points equal the retained failed coupled
case's points. Every interpolant record flushes before the corresponding
solve starts, preserving the computed prefix if a later operation fails.

Support resultants use actual K*u at prescribed physical coefficients, with
moments about [xface,.5,0]. Expected signs follow outward face tractions:
left Fz=-Q, My=+2Q; right Fz=+Q, My=-Q. These are diagnostics only.
No unregistered solve, mesh, post-hoc smoothing or sample selection is added.

Parent preflight requested stricter source identity admission before execution.
The manifest now registers the exact retained/current absolute-path hash pair
for the empty-RHS guard. The harness requires the observed changed-source set
to equal these exact registered pairs; filename-based whitelisting was removed.
Revised ready harness SHA-256:
`e6449e634bd1788c9e9767d0e74c27d13cac186945aa6bed407b30fa10485367`.
Revised manifest SHA-256:
`b6bef9939fcc48d4109614903a3dbdebd88b24e76bf074f0376a6519f1544da3`.
No numerical execution occurred before this revision or before parent run
authorization. The numerical definitions and registered four meshes are unchanged.

## Authorized execution and evidence

Parent explicitly confirmed: "Preflight reviewed, run authorized." Independent
math/source preflight and exact identity-pair admission preceded the run.

Exact command:

`.venv/Scripts/python.exe tools/run_check.py --name shear-isolation --timeout 180 -- python tools/shear_isolation.py`

Evidence directory: `evidence/w1/shear-isolation-c9e5b50eda`.
Completed exit 0; four meshes, four analytical interpolants and exactly four
solid solves; zero execution failures, no stderr and no retries. Process wall
2.9219999999986612 s under the 180 s bound. Outer receipt verifies zero
remaining owned processes. Full `stdout.jsonl`, `stdout.stderr.txt`,
`identity.json`, `result.json` and progress receipt retain the computed prefix,
full coordinates/tensors/coefficient maps and exact input/runtime identities.
The original-mesh quadrature-coordinate equality check passed.

Executed harness SHA-256:
`e6449e634bd1788c9e9767d0e74c27d13cac186945aa6bed407b30fa10485367`.
Executed isolation manifest SHA-256:
`b6bef9939fcc48d4109614903a3dbdebd88b24e76bf074f0376a6519f1544da3`.
Reference harness and reference manifest hashes above remained unchanged.
No original coupled case was rerun or relabelled.

## Fixed-region stress measurements

Every error below uses all registered quadrature samples with
0.25<=x<=0.75, axial scale 0.3 Pa and shear scale 0.0075 Pa. No smoothing or
post-hoc exclusion was applied. All eight routes exceed the retained 5% shear
criterion. All four solved controls meet the original numerical residual gate.

| Mesh | solid DOFs | interpolant axial | interpolant shear | solved axial | solved shear |
| --- | --- | --- | --- | --- | --- |
| Nx4 Ny1 Nz8 original | 1377 | .004783163265 | .812181122450 | .018679473874 | .752353377549 |
| Nx8 Ny1 Nz8 axial only | 2601 | .002391581633 | .198341836736 | .004850014765 | .202085939264 |
| Nx4 Ny2 Nz8 width only | 2295 | .004783163265 | .812181122450 | .019318995437 | .778245468420 |
| Nx4 Ny1 Nz16 thickness only | 2673 | .002391581633 | .816884566329 | .019164827895 | .766071618531 |

Maximum registered equilibrium residual across controls:
1.1013412404281553e-10, below 1e-9. Constraint residuals are zero (no interfaces).
No reference was selected from these measured errors.

The original-mesh solved control's controlling shear point is
[0.4464285714285714, 0.9285714285714285, -0.0035714285714285726] m:
actual sigma_xz=0.00184778334185072 Pa, reference=0.007490433673469387 Pa,
absolute error=0.005642650331618667 Pa, scaled error=.7523533775491557.
The axial-only control's controlling shear error is 0.001515644544478766 Pa
at [0.4732142857142857, 0.9285714285714285, -0.0035714285714285726] m.
Full controlling coordinates/components for both routes on all four meshes
are retained in each JSONL result and the final compact summary record.

## End force and moment diagnostics

Values below are actual K*u force resultants and moments about each end face's
centroid [x,.5,0]. Reference Fz is -.001 / +.001 N and My is +.002 / -.001 Nm
on left/right respectively. These are not extra acceptance gates. Other force
and moment components and all prescribed-coefficient force values remain in
the full records.

| Mesh | left Fz N | right Fz N | left My Nm | right My Nm |
| --- | --- | --- | --- | --- |
| original | -.001013057818240 | .001013057818197 | .002006528909121 | -.000993471090912 |
| axial only | -.001001065598851 | .001001065599323 | .002000532799470 | -.000999467200446 |
| width only | -.001014378917185 | .001014378918050 | .002007189458702 | -.000992810541153 |
| thickness only | -.001012919239538 | .001012919240850 | .002006459619888 | -.000993540379934 |

Axial-only refinement reduces relative Fz error from about 1.306% to .107%
and the left/right My errors from .326%/.653% to .0266%/.0533%. These are
measured discrete support diagnostics, not a change to the registered problem.

## Discrimination and limits

Large shear-recovery error is reproduced without any connector or native
shell: the same-mesh analytic-boundary solid control gives 75.24%, compared
with 72.19% in the retained failed coupled case. Thus the connector/native
route is not necessary for a large error on this solid mesh. The analytical
nodal interpolant also gives a large error (81.22%); it is not a solved state
or a best-approximation lower bound.

Changing only axial resolution reduces both interpolant and solved shear
errors substantially (to 19.83% and 20.21%), while the separate width/thickness
changes do not improve the solved shear error in these four controls. This
supports strong axial solid discretization sensitivity and motivates a
distinct next investigation if authorized. It does not establish a convergence
rate, a complete error decomposition, an interpolation bound, a kernel defect,
locking, or absence of additional transition/modeling error. Prescribed P2
end interpolation remains part of the measured control, and only four finite
meshes were examined. No automatic further refinement is authorized.

Handoff state: diagnostic implementation complete and verified against the
four-mesh registered execution contract; accuracy failures retained, final
scientific adjudication with parent. Product kernels, coupling, tolerances,
old reference sources and prior evidence remain unchanged. Production and
the original engineering comparison remain NO_GO.
