# Extended physical patch study proposal

Preparation only: no scientific assembly, solve or study execution is
authorized before independent parent preflight review. Product sources,
earlier manifests and failed evidence remain unchanged.

Proposed minimal inventory: eleven solves under one 180 s process. Seven
nu=0 Q4 membrane cases cover shell:solid-y ratios 1:1,1:2,1:4,1:8,2:1,4:1,8:1;
one explicit shifted nonmatching membrane case; S3 and mixed Q4/S3 bending;
one Q4 bending model with two solid replacements and four transitions.
All structured interfaces are planar straight, t=.2,E=1000,nu=0, no offsets,
MPCs or crosspoints. Interface endpoints remain unsupported.

Actual findings: current ShellEdgeTrace provides production MIN3 displacement
traces for exact S3 V2D and mixed chains. SolidModel supports named disjoint
regions and per-region interface embedding; result.reactions identifies
physical support DOFs. Trace corner breakpoints are separate from automatic
integration cuts. Multiplier knots will be frozen to the coarser declared
corner station list, shell on ties, with no integration-union multiplier
refinement. Native external line loads/moments will use segment-integral
endpoint/interior weights; no uniform nodal-force shortcut.

Acceptance/reference design: membrane F1 -> epsilon=.005, stressxx5Pa,
tipu=.015m, twice-energy=.015Nm at span3. Bending curvature .001,
M=E*I*a, stressxx=E*a*z, tipw=-a*L²/2, theta_y=a*L,
twice-energy=E*I*a²*L. Multi-replacement span5 uses these same formulas with
x+1 and includes only native strips[-1,0],[1,2],[3,4] plus cores[0,1],[2,3].
Residual1e-9, work1e-10, force/moment resultants1e-8 and fixed 1% global/5%
stress remain. Reaction equilibrium will include support DOFs only and all
applied external loads, with moment arms in actual global coordinates.

Remaining: create prospective manifest with all fixed partitions, dimensional
counts and references; implement bounded JSONL harness; AST/manifest-only
self-review and handoff to parent. No blocker; no numerical work has started.
The study will remain research-only/NO_GO and is not uniform-stability
qualification or W1.4 acceptance.

## Final prepared inventory (supersedes initial eleven-case sketch)

Parent supplied explicit tools-only strong nodal tying and its host protocol,
and requested an S3 width-bending discriminator for nonzero MIN3 edge terms.
The final frozen proposal has thirteen solves, twelve weak research cases and
one strong nodal diagnostic, below the twenty-solve limit. Planned maximum
primary count is828; maximum multiplier count is90. These are combinatorial
structured-mesh counts, not measured assemblies; execution verifies equality.

| Case | physical field / formulation | planned primary | planned multiplier rows |
| --- | --- | --- | --- |
| q4_membrane_1_1 | membrane / weak | 183 | 20 |
| q4_membrane_1_2 | membrane / weak | 273 | 20 |
| q4_membrane_1_4 | membrane / weak | 453 | 20 |
| q4_membrane_1_8 | membrane / weak | 813 | 20 |
| q4_membrane_2_1 | membrane / weak | 207 | 20 |
| q4_membrane_4_1 | membrane / weak | 255 | 20 |
| q4_membrane_8_1 | membrane / weak | 351 | 20 |
| q4_membrane_shifted_4_5 | membrane / weak | 615 | 50 |
| s3_bending_weak | spanwise bending / weak | 183 | 20 |
| mixed_bending_weak | spanwise bending / weak | 477 | 30 |
| two_replacements_four_transitions | span5 bending / weak | 828 | 60 |
| s3_bending_strong_nodal_control | matched S3 bending / strong diagnostic | 183 | 90 |
| s3_width_bending_min3_term | width bending / weak | 387 | 30 |

The shifted native corner partition is[0,.2,.45,.7,1]; solid corners are
[0,.1,.3,.55,.8,1]. Its frozen native segment-integral endpoint/interior load
weights are[.1,.225,.25,.275,.15], not uniform nodal loading. Multiplier knots
come from the declared coarser native corners, transformed explicitly for the
reversed right-interface chart. The numerical integration union does not
select the multiplier space.

The strong case matches the S3 weak case's one-edge native and Ny1/Nz2 core.
It uses ALL15 unique P2 coefficient locations per face, three components,
two faces=90 constraints. There is no historical3x3 grid assumption, penalty,
rank truncation, mixed weak/strong row-unit model or silent fallback. The host
call requires both `SolidModel(...,research_coupling=True)` and
`add_interface(...,diagnostic_strong_tying=True)`. Its result is explicitly
`diagnostic_only_strong_tying`; point forces are not qualified distributed
tractions. Full piecewise continuity is claimed only for compatible polynomial
partitions, not arbitrary nonmatching nodal collocation.

## Width-bending candidate and prospective reference review

The S3 width-bending field is
u=(0,a*(y-.5)*z,-a*(y-.5)^2/2),theta=(-a*(y-.5),0,0). It has
epsilon_yy=a*z and gamma_yz=a*(y-.5)-a*(y-.5)=0; sigma_yy=E*a*z and every
other tensor component is zero. At y1 its physical side traction_y=+E*a*z
gives moment_x=-M per x-length; at y0 traction_y=-E*a*z gives moment_x=+M.
These correspond to the consistently integrated native edge moments. The
solid uses the public affine traction gradient, with no tip load or body force.
All six native left values are prescribed to the exact nonzero field.

Twice energy is E*I*a²*span=2e-6Nm. Maximum physical nodal displacement is
a/8=.000125m, maximum angular field a/2=.0005rad. Fixed residualUref is
max(.000125,Lref*.0005)=.0005m; the separate displacement and angular checks
use .000125m and .0005rad, preserving1% requirements. Work closure includes
the actual prescribed-support reaction work q_fixed·reaction in addition to
ALL applied native and solid loads. Reactions in resultant checks are ONLY
physical prescribed supports; unconstrained numerical residuals are excluded.
These signed load/reference definitions require independent parent scientific
preflight before any solve. This field has a nonzero MIN3 quadratic edge
displacement, unlike the spanwise bending interface field.

All span3 membrane cases registerUref .015m, stress5Pa, twice-energy .015Nm.
Span3 x-bending cases registerUref .0045m, angle .003rad, stress .1Pa and
twice-energy2e-6Nm. The two-region span5 case registersUref .0125m,
angle .005rad, stress .1Pa and twice-energy3.3333333333333346e-6Nm; it contains
only native[-1,0],[1,2],[3,4] and solid[0,1],[2,3], without overlapping replaced
shell elements. All length/force/displacement/interface/work/moment references
are fixed in the prospective manifest before execution and never inferred
from observed errors.

## Self-review and ready handoff — no scientific execution

Created only the three assigned new paths. Checks performed: Python stdlib
`ast.parse` on the harness; JSON inventory/count/reference inspection; exact
source/fixture SHA verification; and execution of only the extracted stdlib
manifest-validation functions. All passed. The validation check explicitly
confirmed NumPy/SciPy/scikit-fem were not imported: **zero backend imports,
zero assemblies, zero solves, no study invocation or numerical campaign**.

Ready harness SHA-256:
`26f8622e2aafd2a5c3c45d242f19398b1a64063a7e1d4d0b6910112055038ee3`.
Ready manifest SHA-256:
`11203765e732ff36e64f879bdb778a14ef486649b552a8510a641194bff17e44`.
Tools-only strong helper SHA-256:
`82378f814c5344af1a1cf3cf1a79ef7bb00ad2f135fa5aab1df4fe4819cfe396`.
Host strong-admission protocol SHA-256:
`d149308d42b00b68529f5c9b0cc45daf5d07164fd91c875aacdb0dce03f0ea22`.
The manifest freezes actual Q4/S3, trace, backend, evaluator, coupling, host and
fixture source hashes and its own harness hash. Drift refuses before execution.

Prospective command, **NOT RUN** and requiring parent review/authorization:

`.venv/Scripts/python.exe tools/run_check.py --name extended-patch-study --timeout 180 -- python tools/extended_patch_study.py --execute`

Default harness invocation describes the proposal only. An explicitly
authorized --execute run flushes study identity, complete case configuration,
registered scales, actual external load vectors/weights, operator metadata and
pre-solve signatures before each solve, then complete coefficient/tensor and
support/work/residual evidence. Unexpected source, assembly, rank,
factorization or serialization exceptions stop the remaining inventory and
retain the computed prefix. There is no automatic retry or added case. Fixed
accuracy failures stay explicit; no subsequent reference or tolerance changes.

Handoff state: **prepared, numerically unverified**. Parent independent source
and scientific review, including the added width-bending load signs and strong
nodal protocol, must precede exact-once execution authority. No result or pass
is claimed. W1.4 and production coupling remain NO_GO, and old scientific
failure evidence remains unchanged.
