# Prospective physical-offset patch checkpoint

Preparation only; no assembly or solve has been executed. This is a distinct
four-case offset-law investigation, not a retry of the earlier study.

Actual production conventions inspected:

- `elements.py::_build_shell_b_matrices`: kappa_xx=+d(theta_y)/dx,
  kappa_yy=-d(theta_x)/dy; strain at normal coordinate zeta is
  epsilon_ref+zeta*kappa.
- `e4_pl_element.py::_constitutive_and_drill_stiffness`: the native 8x8 law
  contains A,B,B.T,D in the membrane/curvature blocks and As for shear.
  `_generalized_section_in_frame` preserves physical-director covariance.
- Nonzero B is explicitly admitted when an authoritative reference_normal is
  supplied. The fixture will use +z and director polarity+1 on planar Q4s.
- Public `GeneralizedShellSection` validates finite A/B/D/As, ABD symmetry and
  SPD after dimensionally scaled congruence; no new material implementation.

For reference plane z_ref=-e and material centre global z=0,
zeta=z_global+e. Direct thickness integration therefore gives
A=t*Q, B=e*t*Q, D=(t³/12+e²*t)*Q, As=(5/6)*G*t*I. The positive B sign follows
the actual positive native curvature convention. The ABD Schur complement is
(t³/12)*Q, positive for E1000,nu0; the existing API has no identified blocker.

Membrane: epsilon_ref=.005,kappa0 -> N=1N/m,M_ref=eN; physical force at z0
requires native reference-edge Fx=1N,My=eFx. Its moment about the global origin
has y-component z_ref*Fx+My=-eFx+eFx=0. Bending: epsilon_ref=-e*a,kappa=a
gives N=0,M_ref=E*a*t³/12; native ux_ref=-e*a*(x+1), and transport through
arm(z_global+e) recovers ux=a*(x+1)*z_global exactly once.

Plan: standalone public-API Q4/P2 harness and frozen prospective manifest for
e=+/-.05 with membrane and x-bending, unchanged core centred at globalz0,
native z=-e, traceoffset=e. Four solves maximum, primary<=2000, rows<=40,
one90s process after independent review. Fixed 1% field/energy,5% stress,
1e-9 residual,1e-10 work and1e-8 physical resultant limits. Consistent line
loads, support-only physical reactions/global moment arms, measured support
work and exact non-overlapping replacement geometry will be explicit.

Remaining: write minimal harness+registered matrices/fields/load/reference
values, freeze source/fixture identities, AST/stdlib checks and parent handoff.
No numerical API construction, assembly or solve is needed for this proposal.
No offset product capability or production qualification is claimed.

## Prepared four-case handoff

Created only the three assigned new files. The standalone harness uses existing
public GeneralizedShellSection and Q4 constructors, the existing physical
ShellEdgeTrace offset and the P2 backend; it imports no prior study helper and
does not bypass any old manifest gate. The native midsurface reference is
z=-e but the solid and physical material thickness remain exactly z=-.1..+.1.
No implicit element reference_surface_offset is set or added a second time.

| Case | e / native zref m | end Fx N | reference end My Nm | planned primary / rows |
| --- | --- | --- | --- | --- |
| offset_plus05_membrane | +.05 / -.05 | 1 | +.05 | 183 / 20 |
| offset_plus05_bending | +.05 / -.05 | 0 | 1/1500 | 183 / 20 |
| offset_minus05_membrane | -.05 / +.05 | 1 | -.05 | 183 / 20 |
| offset_minus05_bending | -.05 / +.05 | 0 | 1/1500 | 183 / 20 |

All reference section matrices are registered before execution. In exact
rational units, Qdiag=(1000,1000,500)Pa, Adiag=(200,200,100)N/m,
Bdiag=+/-(10,10,5)N, Ddiag=(7/6,7/6,7/12)Nm and
Asdiag=(250/3,250/3)N/m. The membrane physical end force is applied at global
z0 by the reference force/moment pair above. Bending uses no axial force.
The two endpoint line weights are .5,.5; they are derived from segment
integration and checked against the frozen registration.

Membrane references: epsilon=.005, physical centre tip displacement .015m,
theta0, stressxx5Pa, twice energy .015Nm. Bending references:
a=.001/m, physical centre tip(0,0,-.0045)m, theta_y=.003rad, native reference
tip ux=-e*.003m, stressxx=E*a*z_global, twice energy2e-6Nm. Displacement and
angular checks use fixed global reference magnitudes, not observed residuals.
Both interface Urefs are .015m for membrane or .0045m for bending; Lref1m,
Fref1N or1/1500N respectively. Work and moment scales are registered explicitly.

The prospective harness checks native reference-plane fields and separately
transports all nodal displacements to globalz0 for the physical centre-field
comparison. Energy comes from actual native and solid K quadratic forms;
external work includes the actual reference force AND nodal moment covectors.
Only prescribed physical native support reactions enter resultants, with their
actual globalz=-e moment arms, and measured prescribed-support work is included.
These exact left fields are zero at x=-1; no hidden nonzero constraint is used.
Independent arbitrary-vector interface work checks retain the same transpose
operators. All9 solid stress components are compared at every quadrature point
with .25<=x<=.75 using the unchanged fixed 5Pa/.1Pa scales.

Frozen candidate harness SHA-256:
`5d5deea4107c2e8a6d8723326cac5675e90e844ae5012cce9e3f23b8a835c029`.
Prospective manifest SHA-256:
`dd9c94dd7a0598a8c1ee0c975eacb4d3c8c90178219fa4d4bd84c63a2787cd14`.
The manifest records actual source/fixture hashes for the section law, Q4,
physical trace, coupling, backend, host, evaluator, assembly, load and DOF
sources. Any drift refuses before execution. This proposal leaves all older
study source/manifests/evidence and all product kernels unchanged.

## Checks and limits

Checks actually performed: AST parse, JSON/source-hash admission inspection,
and execution of only extracted stdlib manifest validation. Exact Fraction
checks establish the registered N/M pairs, the positive ABD Schur complement
and the membrane global-load moment cancellation for both offset signs.
All passed. The self-check explicitly verified **zero NumPy/SciPy/skfem
imports, zero public numerical object constructions, zero assemblies and zero
solves**. No study invocation or test campaign was run. Existing public API
admission is established from source and existing tests; eventual runtime
construction/validation still belongs to the independently authorized process.

Prospective command, NOT RUN:

`.venv/Scripts/python.exe tools/run_check.py --name offset-patch-study --timeout 90 -- python tools/offset_patch_study.py --execute`

Default invocation is proposal-only. An independently authorized --execute
run is bounded to four cases/one90s process, primary<=2000 and rows<=40. It
flushes identity/configuration, actual section matrices and complete geometry,
registered scales and external loads before each solve. It retains complete
field/stress/support/work/residual results and all flags. Exceptions stop the
remaining inventory with no automatic retry; accuracy failures are retained
without changing references, thresholds or subsequent cases.

State: prepared and numerically unverified, ready for independent parent
source/sign/section-law review. No physical-offset capability or W1.4
acceptance is claimed. Production coupling and historical NO_GO remain.
