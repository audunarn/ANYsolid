# Transverse shear engineering comparison checkpoint

Prospective manifest read: `docs/transverse_shear_comparison_manifest.json`.
Controlled Q4 ordering inspected in `ANYsolver/tests/test_solid_coupling.py`:
counterclockwise xy vertices with physical normal +z, left strip interface
edge 1 and right strip interface edge 3. This harness will construct axial
subdivisions 1/2/4, width one Q4, and upstream P2 tet grids Nx=1/2/4,
Ny=1, Nz=2/4/8. No prior fixture/source/evidence will be edited.

Plan and acceptance:
1. Create standalone JSONL comparison with full identity and flushed level
   records, fixed end force Q=.001 N and zero native left six-DOF support.
2. Compare actual native+solid quadratic energy, tip w/rotation and independent
   Saint-Venant tensor stresses with fixed prospective references. All
   quadrature points x=.25..75 remain in the interior criterion; report
   interface-layer samples separately without post-hoc exclusions.
3. Run the one authorized 180-second outer-harness command. Coarse levels are
   diagnostics; only finest targets (1% field/energy, 5% axial/shear stress,
   registered residuals1e-9) determine this bounded comparison's result.

Reference signs checked analytically: w'=Q/(kGA)-theta, ux,z=theta+warp',
giving gamma_xz=(3Q/(2GA))*(1-4z²/t²), sigma_xz as registered. Also
sigma_xx,x + sigma_xz,z=0. The known interface-mode discrepancy is preserved:
parabolic normal flux does work -Q*t/30 on the documented zero-moment
variation, so these are engineering comparisons, never exact connector
patches. Mesh refinement cannot be assumed to remove this modeling error.

Remaining: implement, bounded run, inspect actual measurements, handoff.
No blocker. Parent owns scientific adjudication and promotion; productionNO_GO.

## Implemented and executed bounded comparison

Created `tools/transverse_shear_comparison.py`. Only this new harness and this
checkpoint were edited. The controlled native strips have true axial
subdivisions with one Q4 across the width, physical +z directors and exact
production node ordering. P2 solid geometry uses the prescribed independent
Nx/Ny/Nz counts. Only the actual end force and zero left supports are applied;
no manufactured forcing, extra springs or fictitious surface loading occurs.

The JSONL retains manifest/source/library identities, each level's dimensions,
actual native and solid energy forms, both tip endpoint values, all recovered
stress tensors and physical sample coordinates, exact independent tensor
references, fixed interior masks, separate interface-layer diagnostics,
registered residual reports and the historical componentwise diagnostic.
Coarse `passed` is null and explicitly diagnostic; finest accuracy is assessed
without changing any reference, threshold or sample region.

Exact command:

`.venv/Scripts/python.exe tools/run_check.py --name transverse-comparison -- python tools/transverse_shear_comparison.py`

Evidence: `evidence/w1/transverse-comparison-afc765db20`. Three levels completed,
zero execution failures, no stderr, no retries. Process exit 1 reflects the
recorded scientific failure, not an implementation exception. Process wall
2.9219999999986612 s under the 180 s outer bound; owned-process cleanup verified.
Harness SHA-256:
`475940b3ae0273395e87195698ef10d09c493181aeedd40d47005c7e28089965`.
Manifest SHA-256:
`5391fddc78317075bc6f705b4754cbe3fd880418d6fc871394a68363fe0c5163`.

| Level | primary / multiplier DOFs | max tip w relative | max tip theta relative | energy relative | axial stress scaled | shear stress scaled |
| --- | --- | --- | --- | --- | --- | --- |
| 1 / Nx1 Ny1 Nz2 | 183 / 20 | .02584686053 | .003329204575 | .02549309857 | .06475830101 | .9331155628 |
| 2 / Nx2 Ny1 Nz4 | 477 / 20 | .005707747241 | .000006717574 | .005707112833 | .06031739879 | 1.851116725 |
| 4 / Nx4 Ny1 Nz8 | 1497 / 20 | .001265785781 | .000002738041 | .001265507002 | .01763341686 | .7219325526 |

Finest tip w values [0.013518866323666412, 0.013518873870267865] m; theta_y
[-0.006749981518226525, -0.006750018481475794] rad. Actual twice energy
1.3518870097220409e-5 Nm. Displacement/rotation/energy and axial stress meet
their fixed finest targets. Interior shear fails the 0.05 scaled target:
0.7219325525611093, corresponding to 0.0054144941442083195 Pa absolute error.
Controlling retained point [0.6964285714285714, 0.9285714285714285,
-0.0035714285714285726] m has actual sigma_xz=0.002075939529261068 Pa versus
reference 0.007490433673469387 Pa. No sample was excluded after observation.

Registered equilibrium maxima across levels:
[2.4168031942037316e-11, 3.322576605800697e-11, 5.3290705182007514e-11];
constraint maxima:
[3.0423655370720073e-14, 2.7689041645646324e-14, 1.2863003787095726e-13].
All residual gates passed. Finest other-stress-component maximum is
0.0008407400999832504 Pa, reported separately. Finest interface-layer axial
and shear scaled errors are .01955657718 and .72888632456; these diagnostics
were never substituted for the registered interior criterion.

## Scientific handoff

Result: **SCIENTIFIC_NO_GO** for the fixed finest engineering comparison,
because its interior shear-stress criterion failed. Numerical refinement
reduced global displacement/energy and axial-stress errors in this three-level
sample. Shear errors are nonmonotonic; these observations establish neither a
convergence rate nor a plateau. The known weak-interface modeling discrepancy
is analytically nonzero and remains distinct from discretization error.
These three levels, with Ny fixed at one, cannot attribute the measured shear
error uniquely to either cause or provide an independently converged reference
for the actual mixed-interface problem.

No reference retuning, tolerance change, additional campaign or scientific
failure repair was attempted. Existing patch/spectrum artifacts remain intact.
Parent must adjudicate any further modeling/reference investigation.
Production weak coupling remains NO_GO.
