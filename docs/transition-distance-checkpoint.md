# Transition-distance study: design checkpoint

New owned files only: runner, prospective manifest, this checkpoint and
optional synthetic test. No scientific execution is authorized before parent
independent preflight. All historical evidence and consumed registrations stay
unchanged. This study is an engineering comparison, not an exact patch.

Candidate smaller design: nu0,E1000,t.2,width1,span x[-1,2], full left clamp,
right physical axial line load qx(y)=4F*y below y=.5 and4F*(1-y) above,
F=1N total. The corresponding 3D traction is qx/t, constant through thickness.
This continuous triangular width profile can be integrated EXACTLY as two
affine public backend tractions and consistent linear native edge loads.
It is not the old uniform membrane patch. No K*u force is used. Unlike the
Saint-Venant shear alternative it needs no assumed warping clamp conversion
and avoids the previously measured large shear-gradient cancellation.

Coupled cores centered at x=.5, lengths .5,1,1.5; core Nx4,8,12 (h=.125),
Ny2,Nz2. Native strips have Q4 width2 and axial5,4,3 each side (h=.25),
respectively. Fixed stress ROI x[.4375,.5625] spans the same physical material,
all y,z; exact minimum distances to a transition are .1875,.4375,.6875.
Whole displacement fields and energy are compared as well as local stresses.
Expected primary891,1455,2019; supports18; multiplier20; KKT893,1457,2021.
This explicitly proposes NEW primary cap2100, KKT cap2100, reduced cap2100;
it does not silently reuse the previous2000-primary admission. Existing exact
right-defect/formation arithmetic and output1e6/modal5e6 criteria are retained.

Reference route: independent whole-body upstream P2 solids under the SAME
pointwise full clamp and piecewise-affine physical right traction. Two
prospective grids(12,8,2),(24,16,4), DOFs6375/43659. Coarse/fine differences
must be <=.001 of fixed displacement scale.015 and energy reference norm,
and <=.005 of fixed stress scale5Pa at every coupled ROI quadrature sample.
These are engineering numerical convergence observations, not rigorous
continuum error bounds or an assumed convergence rate. Failure stops acceptance;
no automatic third reference or mesh adaptation. Fine reference is never fitted.

## Final first-slice proposal: frozen for independent preflight

Parent adopted this as the FIRST nonuniform MEMBRANE transition-distance
slice, with explicit new2100 cap and proposed reference accuracy. It does not
close the previous transverse shear whole-body-reference gap, and makes no
bending/shear transition-distance claim. No old scientific gate is waived.

| Core length | Core Nx/Ny/Nz | Native axial each side | Primary | KKT | Minimum ROI distance |
|---:|---|---:|---:|---:|---:|
| .5 | 4/2/2 | 5 | 891 | 893 | .1875 |
| 1 | 8/2/2 | 4 | 1455 | 1457 | .4375 |
| 1.5 | 12/2/2 | 3 | 2019 | 2021 | .6875 |

Each has18 fully clamped coordinates and20 multipliers. Core hx=.125,
native hx=.25, width partitions and thickness grids remain fixed across the
three distances. All interfaces use the existing B policy, explicit endpoints
[0,1], and unchanged five physical modes. Build-time one-sided physical trace
ranks and physical pairing metadata are retained. Because the triangular load
is not one affine width function, the endpoint-only P1 multiplier cannot
represent that load profile; this is not the exact uniform membrane patch.
Distance-dependent differences still include native/solid model differences,
not a uniquely isolated connector error.

Reference support/load is the same physical full-face clamp/traction BVP;
there is no analytical core-end substitution. Reference computation precedes
ANYsolver/coupling imports. Both reference levels must pass residual1e-9,
exact work1e-10, symmetry1e-10, resultants1e-8. Whole coarse coefficient fields
are compared with the fine public trace. ALL candidate ROI quadrature samples
are generated from geometry before either reference solve; their union is
used for coarse/fine stress comparison, including every component and repeated
points. No smoothing or exclusion. Upstream gbasis/mapping/element_finder
evaluates stress at these common points; on internal FE faces it uses the
upstream deterministic chosen-cell convention, without averaging. A built-in
probe check against the public recover result at ALL own quadrature points
must pass1e-10. This FE probe route is source-derived but remains unexecuted
until the scientific authorization.

Fixed physical comparison scales: displacement.015m, stress5Pa, work.015Nm,
zero director tilt.005rad, length1m/force1N. References must also meet conservative
norm guards max|fine coefficient|>=.015 and max|fine ROI stress|>=5. Relative
energy uses the independently computed fine reference energy. Registered U=.03
for primary/interface residual scaling. Exact Fraction ceiling derives output
factor ceil(max(.03/.015,.03/.005))=6. Native material-director tilts x/y are
zero by thickness symmetry and checked; native drilling z is diagnostic only,
because it is not the3D material-director observable. Numerical amplification
still conservatively includes every native rotational coordinate.

New measured field/rotation/energy.009 and stress.045 are prospectively stricter
than original1%/5%, which remain visible in output. Reference differences
.001/.005 are numerical convergence observations, not rigorous error bounds;
no rigorous combined energy/stress certificate is claimed. Failure to establish
reference convergence stops acceptance before coupled solves, with no automatic
third reference or refinement. Every coupled case receives the full frozen
right-defect+formation inverse certificate, <=64 streamed columns, same1e6
physical/5e6 modal bounds, and unregularized QR/Cholesky numerical assessment.
No condensation, rank truncation or stiffness alteration is introduced.

Work arithmetic is prospectively exact for the actual binary matrices,
coefficients and external loads. Integer exponent bins sum dyadic products
without floating product/contraction rounding, algebraically identical to a
Fraction product sum. Exact normalization and limit comparison follow. This
is not a fallback after an observed failure. Both references and coupled
models retain homogeneous support values, so prescribed support work is0.

Runtime caps are2 reference solves,3 coupled solves,3 inverse assessments,
one180s outer/175s inner process. No automatic retry or added mesh. Prefix,
phase counts, full native/core fields,3D stress tensors, source/configuration
identities and rational work quantities are flushed. Reference K is identified
by CSR byte checksum/shape/nnz, rather than serializing its full large arrays;
coupled canonical Kr/B/H arrays are retained. Dense coupled arrays are bounded
by2100²*8≈35.3MB each; total factor memory and wall time are unmeasured. Sparse
reference fill and actual fit within180s remain execution risks, not a claim
of achieved resource use. The outer supervisor enforces the process-tree cap.

## Checks and handoff

No scientific FE assembly, solve, reference, gradient probe or inverse metric
has run. Only AST/stdlib proposal audits and fixed synthetic matrices<=3x3
were exercised. Checks actually run:

- `.venv/Scripts/python.exe tools/run_check.py --name transition-synthetic --timeout 90 -- python -m pytest tests/test_transition_study.py -q`:
  9passed/0failed; process wall0.6100000000005821s; evidence
  `evidence/w1/transition-synthetic-26ddc5d6e7`.
- After the final source/output-factor audit,
  `.venv/Scripts/python.exe tools/run_check.py --name transition-synthetic-final --timeout 90 -- python -m pytest tests/test_transition_study.py -q`:
  9passed/0failed; process wall0.5159999999887077s; evidence
  `evidence/w1/transition-synthetic-final-312445f3b7`.
- `.venv/Scripts/python.exe tools/run_check.py --name transition-proposal --timeout 30 -- python tools/transition_distance_study.py`:
  exit0,2records(identity/proposal),0 scientific operations; wall
  0.20299999999406282s; evidence `evidence/w1/transition-proposal-4cc01bccf2`.

All three supervisors verified cleanup with0 active processes. No failed check
occurred. A separate stdlib schema audit asserted NumPy/SciPy/skfem/ANYsolver
were not imported. Unit tests cover exact cancellation against independently
derived Fraction values, finite/refusal/deadline paths, actual count/distance
derivation and exact consistent triangular-load integrals/resultants.

Frozen runner SHA256:
`61eb85ce7845e49eb7c0e60d1ace86091bc8c4432a5b018a9918b16294c5335b`.
Frozen manifest SHA256:
`7e22aa6fed7e38e57635ec9043422a2326d73c39462ed0da3d93bed6a9ae758b`.

Independent source/math review and explicit scientific execution authorization
remain pending. Proposed command ONLY after that authorization:
`.venv/Scripts/python.exe tools/run_check.py --name transition-distance --timeout 180 -- python tools/transition_distance_study.py --execute`.
Implementation/proposal verification is complete within the first-slice scope;
scientific verification is prohibited until review. Production remains NO_GO.

## Consumed first attempt: retained-only reference diagnosis

The first scientific registration is consumed and remains NO_GO:
`evidence/w1/transition-distance-6b4550d018`, process60.062s,2 reference
solves,0 coupled solves/metrics,0 execution failures. Both individual reference
check sets passed. The independent reference convergence gate failed ONLY
global coefficient field difference .0029565802212485667>.001; energy
.00043391547994759577<=.001 and common ROI stress.0010265422643632193<=.005.
No reference refinement/retry or gate change was performed.

Read-only diagnosis used only saved arrays and stdlib arithmetic; no new FE
import, interpolation, derivative, assembly or solve. All6375 coarse coefficient
locations were associated with the same structured P2 lattice indices of the
fine mesh, including physical component ownership. The maximum coordinate
roundoff between corresponding stored positions is1.3877787807814457e-17.
This is a retained-node comparison, not a reexecution of public trace. At the
controlling location coordinates are BITWISE equal on both levels, and the
saved-node difference exactly reproduces the registered field metric:

- uy at(2,.6875,.1), coarse DOF6367/fine DOF6358:
  .0007670615335005832 -> .0008114102368193117m;
  difference4.4348703318728496e-5m, divided.015 gives
  .0029565802212485667.
- Largest ux difference is at(2,.4375,.1), scaled.002580663859035974.
- Largest uz difference is at(2,0,.1), scaled.0005045417448103082.
- Saved common-node field maximum inside fixed ROI is only
  .000012142898019732511 at(.5,0,-.1), uy. The failed GLOBAL gate is loaded-end
  accuracy, not the registered interior stress sampling. No sample is removed.
- The maximum restricted to z0 is.002330712238336654 at(2,.4375,0),uy;
  therefore the issue is not confined to a top-surface point.

For this specific nu0 BVP an exact continuum plane solution extrudes through
z: load/clamp and in-plane equations are z-independent, uz=0 and all z-face
tractions vanish; positive elasticity/full clamp gives uniqueness. Thus any
through-thickness dependence is a numerical artifact, not physical warping.
The retained maximum uy spread over z falls from.002218886009801085 of.015
(coarse,xy=(2,.625)) to.0006465184169218563 (fine,xy=(2,.5625)). Maximum |uz|
falls7.85326875634326e-6 ->1.2976076378930346e-6m. This corroborates remaining
3D tetrahedral discretization error, but cannot identify one controlling mesh
direction: x,y,z were all refined together and extrema differ.

The existing grids have hx/hy=2 (.25/.125 then.125/.0625), so axial-only
resolution is a plausible efficiency candidate, NOT an established conclusion.
A fresh separately authorized directional control set based on the consumed
coarse grid would cost12495DOFs for(24,8,2),12375 for(12,16,2),11475 for
(12,8,4), each with identical physical clamp/tractions and no coupling. These
could discriminate x/y/z sensitivity at much lower size than blind additional
uniform refinement. They do not themselves establish a converged reference.
Pure directional refinements of the saved fine grid exceed the old50000 cap:
86427/85995/82467DOFs respectively, requiring explicitly new resource bounds.

Another prospective efficiency option is an independently converged upstream
2D nu0 elasticity reference extruded analytically, using the exact invariance
argument above. This would be a CHANGED reference route requiring parent
adoption, independent scientific review, new manifest and fresh execution
budget; it is not silently substituted for the promised 3D reference. No
particular next mesh or convergence rate is inferred from these two levels.
All original arrays, failed gates, source and manifest identities remain intact.


## Pre-execution documentation correction

Independent review found inherited candidate-A normalization prose under
`stability.certificate.physical_output`. It now explicitly states the current
.015 translation/.005 rotation checks,U.03,L1 and exact factor6. The old
.000125/.0005/factor4 prose is labeled inapplicable. Only this descriptive
manifest string changed; code, physics, numerical criteria and bounds did not.
The previous proposal-only receipt and embedded manifest remain immutable at
`evidence/w1/transition-proposal-4cc01bccf2`; that historical manifest SHA was
`05760701a6b6a903ee8eb412754cf9c9acb70d65b4f65700ee62a5227d1489f9`. The current pre-execution manifest SHA is
`7e22aa6fed7e38e57635ec9043422a2326d73c39462ed0da3d93bed6a9ae758b`. No FE/check campaign was rerun for this documentation-only delta.
