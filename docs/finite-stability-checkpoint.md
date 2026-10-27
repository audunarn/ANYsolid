# Finite stability and Q4 width-refinement proposal

Preparation only: no candidate metrics, FE assembly or physical solve is
authorized yet. The offset proposal and all prior study files remain frozen.

Prospective inventory is18 finite metrics: matching Ns=Nv=2,4,8,16 at
t=.2,.1,.05; nonmatching2:16 and16:2 at t=.2,.05; shifted4:5 at t=.2,.05.
Only the12 matching cases get physical Q4 width-bending solves. Native axial1,
core Nx1/Nz2, geometric corner multipliers (shell on ties), no MPC/crosspoint,
primary<=2000, KKT<=2100, lambda<=180, one180s process, no retry.

Governing certificate design:

- Construct the actual stored physical K/C and a selection-only support P.
  L1 makes s=1 exactly. Record T=U/s,S=F*s,G=Uiface*||C D^-1||1 and the
  node-major translation/couple modal Lambda scales.
- Sparse LU supplies approximate inverse columns R in blocks<=64. It is not
  itself a certificate. Use the RIGHT defect I-HR, outward row-absolute sums,
  conservative gamma_n product/subtraction/summation bounds and gradual-
  underflow protection. Include H-formation uncertainty using gamma4/(1-gamma4)
  times an outward upper bound of |H||R|, with explicit normal-finite input,
  reciprocal and multiplication guards. No inverse norm estimator is used.
- If eta<1, row-block inverse norms are bounded by ||R_rows||inf/(1-eta).
  Actual translation check reference is .000125m, whereas Uref=.0005m; the
  declared physical-output factor4 multiplies the primal bound before the
  <=1e6 gate. Modal traction/couple bound<=5e6 is separate and does NOT certify
  recovered stress uncertainty. Delta is1e-9.
- QR null basis plus unregularized projected Cholesky will provide bounded
  numerical coercivity assessments and nullspace-defect checks; strict dense
  cases exceeding a prospectively declared resource cap are deferred, never
  called accepted or rank truncated. Parent review must settle the exact
  coercivity-assessment claim before execution.

Physical study uses the registered continuum width-bending field and real
side moments/tractions, with nonzero exact native left values. Q4 normal trace
is not exact, so coarse cases are retained diagnostics and only N16 at each
thickness faces measured .009 global/.045 stress criteria. Those observations
are not rigorous combined energy/stress certificates. Work/symmetry1e-10,
resultants1e-8 and residual1e-9 remain unchanged.

Parent separately permits fixed synthetic matrix tests<=8x8 for the certificate
helpers only. Remaining: implement manifest/harness, prove/document arithmetic,
run only those focused algorithm tests, freeze final source and send for
independent review. No candidate numerical work has begun.

## Final registered inventory and governing updates

Root superseded the initial proposed600-coordinate dense cap: the final
numerical positive-energy assessment allows every registered case up to2000
reduced coordinates. It is explicitly a finite QR/Cholesky check, not an exact
coercivity certificate. No stiffness regularization, row truncation, rank
truncation or artificial mass is added. The defended invertibility criterion
is the verified ideal-scaled KKT inverse bound described below.

The final prospective manifest contains18 metric cases and12 coupled physical
width-refinement solves:

| Family | Thicknesses | Count | Physical solves |
| --- | --- | --- | --- |
| matching Ns=Nv2,4,8,16 | .2,.1,.05 | 12 | 12 |
| nonmatching(2,16),(16,2) | .2,.05 | 4 | 0 |
| shifted(4,5) | .2,.05 | 2 | 0 |

The shifted solid interior knots are explicitly i/5+1/20, i1..4, with endpoints
0,1 fixed: [0,.25,.45,.65,.85,1]. This is quarter of a finer solid cell; the
coarser shell corner partition is[0,.25,.5,.75,1]. The geometric corner list,
shell on ties, determines the frozen multiplier space. Integration cuts never
refine multipliers. All native axial counts are1 per strip, core Nx1/Nz2,
with no MPC, crosspoint, physical offset or changed physical kernel.

Planned maxima:1893 primary,1791 reduced,170 multiplier,1961 KKT coordinates,
within2000/180/2100 bounds. Actual dimensions are checked before factorization.
All physical and metric cases use E1000,nu0,a=.001,width/span1/3, actual
thickness t. Force reference F=M(t)/L=E*a*t³/12, L1m and U=.0005m. Native
translation/rotation check references remain .000125m/.0005rad. The pipeline
logs the complete newly derived geometry/load/reference registration and
reuses only read-only fixture functions; no old execution authority or manifest
gate is bypassed or altered.

## Independent full-solid reference prerequisite added before execution

Root required six independent numerical reference corroborations: at each
thickness .2,.1,.05, full solid[-1,2]x[0,1]xz±t/2 with P2 meshes2³ and4³.
Planned DOFs375/2187, below the separate3000 reference bound. The final
single180s process therefore registers18 metric factorizations,12 coupled
physical solves and6 independent full-solid solves. No candidate has run yet.

These references run before any ANYsolver or coupling import. They use public
ANYsolid K and affine side traction, prescribed analytical displacement at ALL
x=-1 face coefficients, zero body force and other natural faces, then a direct
SciPy free-DOF sparse LU. The function refuses if native/coupling modules were
already imported. No shell, shell trace, host coupling solve, manufactured K*u
forcing or fitted reference enters this independent path.

Exact u=(0,a*(y-.5)*z,-a*(y-.5)²/2) has epsilon_yy=a*z,
gamma_yz=a*(y-.5)-a*(y-.5)=0, sigma_yy=E*a*z, zero other components and
zero stress divergence. Natural side tractions are t_y=-E*a*z at y0,
+E*a*z at y1; x/z faces are traction-free except the prescribed exact x=-1
field. This P2-representable field is the exact continuum reference, with zero
theoretical reference error. Numerical references corroborate only this
width-bending reference, not all physics or the actual mixed-interface model.

Both meshes compare ALL primary and ALL boundary coefficients and ALL
quadrature stress tensor components against the analytical reference, and
actual K quadratic energy against3*E*a²*t³/12. Measured support work is included.
Strict reference gates are1e-4 global field/boundary/energy and5e-4 stress;
residual1e-9, work1e-10 and physical resultants1e-8 remain. Actual fine-minus-
coarse displacement is evaluated at coarse coefficient coordinates through
the public upstream trace; energy difference is normalized by the exact
reference energy. Both full stress fields retain their independent exact-
reference comparison; no difference of separately attained stress maxima is
mislabelled a pointwise difference. If any reference prerequisite fails, all
six fixed reference results are retained and the metric/coupled phase stops.

## Certificate arithmetic and scope

Let Hhat be the stored scaled KKT and Hstar the exact arithmetic scaling of
canonical stored physical Kr/B by the recorded stored S/T/G/Lambda. Kr and B
are selected physical submatrices, with no support summation because P is
selection-only with exact+1 entries. Each nonzero Hhat entry uses one normal
finite reciprocal and two normal finite multiplications. Every intermediate
is checked against overflow, subnormal values and zero underflow. Therefore
|Hstar-Hhat|<=beta4*|Hhat| with beta4=gamma4/(1-gamma4) is conservative. This
bound encloses scaling formation, not FE assembly/continuum/model errors.

For binary64 u=2^-53 and q=2^-1074, gamma_n=n*u/(1-n*u) and
tau_n=(2*n+1)*q/(1-n*u). The exact rational constants are rounded upward.
For each inverse-action block (at most64 columns), form Zhat=fl(Hhat*R),
Ahat=fl(|Hhat|*|R|), Ehat=fl(I-Zhat). An outward product-sum upper bound is
Aup=(Ahat+tau_n)/(1-gamma_n). The entrywise RIGHT-defect enclosure is

`|I-Hstar*R| <= |Ehat| + gamma_n*Aup + tau_n + u*(|I|+|Zhat|)+q + beta4*Aup`.

The subtraction term bounds the actual residual subtraction separately.
Every bound add/multiply/divide uses nextafter toward+infinity, positive
denominators are rounded downward, row summation uses its own gamma/underflow
correction, and each streamed block accumulates outward. Arithmetic requires
IEEE binary64 round-to-nearest/ties-even with gradual underflow; executable
probes refuse changed rounding/FTZ/DAZ. Nonfinite results never certify.

After ALL identity columns, eta is an outward upper bound of the infinity
norm of the RIGHT defect. If eta<1, Hstar*R=I-E is nonsingular and
Hstar^-1=R*(I-E)^-1. Consequently each primal/dual row-block norm is bounded
by its outward accumulated row norm divided by(1-eta). LU requires no separate
error claim: its actual returned columns define R and are fully checked.
There is no norm estimator and no full inverse/R retained, only streamed
blocks and row accumulators. Canonical Kr/B and formed H CSR arrays, all scale
inputs and phase/column progress will be flushed for independent audit.

The exact rational norm of the actual physical output map
DP*T/individual_check_reference is checked<=4; the conservative primal output
upper bound is therefore FOUR times the primal row-block inverse bound.
At delta1e-9 it must be<=1e6 to allocate at most .001 of the actual displacement/
rotation check reference. The separate dual block limit5e6 allocates .005 of
the declared modal traction/couple amplitude. Lambda node-major scales are
F/(L*t) for xyz and6F/t² for the two moment modes, with reference coupleF*L.
This is NOT an interior recovered-stress uncertainty certificate. Physical
force/moment closure likewise is not traction accuracy.

The QR nullspace-defect upper bound and projected symmetry are checked<=1e-10,
followed by unregularized projected Cholesky. This is labelled a finite
positive-energy numerical assessment only. Dense Q/projected matrices are
allowed up to reduced dimension2000; named array storage and phase wall are
reported, excluding factors/library workspace/RSS. There is no automatic
resource-based waiver. The outer180s bound and internal175s deadline retain
partial prefixes and stop further work without retry if exhausted.

## Finite physical acceptance interpretation

Q4's interface normal trace is not the exact quadratic continuum width field.
The12 physical cases are a refinement study, not exact patches. All coarse
errors and flags are retained as diagnostics. Only N16 at each thickness must
meet measured .009 displacement/rotation/energy and .045 stress targets; work,
physical force/moment and residual criteria apply at ALL physical levels.
Those stricter finite observations are not rigorous combined energy/stress
uncertainty certificates. No convergence rate, plateau, locking, uniform
stability or universal qualification follows from the finite inventory.

## Checks actually run and readiness

Only fixed synthetic matrices<=8x8 were numerically exercised. Exact command:

`.venv/Scripts/python.exe tools/run_check.py --name finite-certificate-review-candidate --timeout 90 -- python -m pytest tests/test_finite_stability_certificate.py -q`

Final synthetic result:24 passed, zero failed. Evidence:
`evidence/w1/finite-certificate-review-candidate-a5255bdac1`; process wall
0.8120000000053551s. Full stdout/stderr, source/input identity, JUnit and cleanup
receipt are retained. Earlier initial run
`finite-certificate-synthetic-d13b6e043a` had21 passed/1 failed because the
numerical QR helper assumed sparse input; converting its inputs to CSR repaired
that implementation-only defect. Subsequent22/24-case clean runs remain
preserved, with overlapping counts not summed.

The24 checks include exact Fraction inverse norms, nonsymmetric actual scaling
formation, RIGHT-vs-left defect discrimination, output factor4, independent
primal/dual amplification refusal, singular and eta>=1 refusal, nonfinite
inputs/actions, block-size1/2/3/8 invariance, formation underflow/subnormal and
noncanonical-entry refusal, and the explicitly unregularized numerical
positive-energy label. They establish helper behavior on those matrices, not
candidate metric/physical results. AST and stdlib manifest/source checks also
passed. **Zero candidate FE imports, assemblies, metrics or solves occurred.**

Ready source SHA-256:
`fecbd10f83d306e0929fc4a136408c16dc18d19570b98c7ec5c86ec6ef163be9`.
Ready manifest SHA-256:
`1a3535858ccb045e9842c84994bb4a2617a8a50e331efa42e94f14927d744901`.

Parent's final field-gate finding was incorporated before readiness: physical
global displacement is the MAXIMUM of whole-native translation error and
ALL whole-core P2 coefficient displacement errors at their actual physical
coordinates/components, each normalized by .000125m. Native and solid errors
are reported separately. A solid constant-normal shift cannot hide behind
accurate native DOFs or stress; neither the whole-core field check nor its
factor4 algebraic output bound uses the smaller stress ROI.

Actual BLAS/OpenMP pool inspection follows eager SciPy linalg imports before
any candidate work. The executable refuses absent/unverifiable pools or any
pool with threads other than1, and records actual pool/library details and
OMP/OPENBLAS/MKL environment settings. The wrapper already configures those
variables before imports. Candidate normalization scope remains exact scaling
of canonical stored physical blocks and recorded stored S/T/G/Lambda values;
no FE-assembly interval-error enclosure is claimed.

Prospective command, NOT RUN and requiring independent review/authorization:

`.venv/Scripts/python.exe tools/run_check.py --name finite-stability-study --timeout 180 -- python tools/finite_stability_study.py --execute`

Handoff state: prepared, candidate-numerically-unverified. Parent/reviewer must
independently inspect the certificate arithmetic, formation model, units,
reference BVP, geometry/partition registrations and finite acceptance claims
before execution. Offset and all older source/evidence remain frozen. Final
readiness freezes this owner candidate until parent returns explicit findings.
Production and historical NO_GO remain unchanged.
