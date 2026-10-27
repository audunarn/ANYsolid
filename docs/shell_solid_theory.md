# Planar weak section-moment connector: research candidate v1

Status: NO_GO for production. This is an implemented candidate, not a stability
proof. The accepted physical scope remains empty pending the registered gates.

## Physical trace and section modes

Let s follow a straight shell reference edge, d be its physical thickness
director, t its constant thickness, and e the explicitly signed distance from
reference edge to interface midsurface. A point has position
x(s,z)=x_ref(s)+(e+z)d, with -t/2<=z<=t/2. Use actual production Q4
interpolation N for the reference translation and global axial rotation:

u_shell(x)=sum N_i u_i + (sum N_i theta_i) cross (x-sum N_i x_i).

This matches the host's physical small-rotation transport convention. It does
not introduce a continuum rotation coefficient. A rotation parallel to d has
no thickness arm; its physical in-plane moment must transfer through force
variation along s. Nonzero-offset algebra tests do not qualify a shell section
law or prove physical offset consistency with its constitutive reference.

The multiplier is continuous piecewise linear along an EXPLICIT partition in
s. Its five thickness modes are three constant global Cartesian traction
directions and (2z/t)*edge_tangent, (2z/t)*in_plane_conormal. The latter two
vectors lie in the SHELL plane, not the solid side-face plane. They are
conjugate to the two director rotations. The factor 2/t is an explicitly
chosen mode-unit scaling; it does not add stiffness.

## Common integration and solution

For each multiplier test function psi form
C_shell=integral psi.T B_shell dA and C_solid=integral psi.T B_solid dA.
The constraint is C_shell*q-C_solid*a=g, and interface forces are the
transposes of these same blocks with the corresponding signs. Global assembly
uses diag(K_shell,K_solid), C=[C_shell,-C_solid], and the symmetric indefinite
saddle system. Native constraints and solid supports are reduced as u=P*z+u0,
so the reduced constraint right side is g-C*u0. Multiplier row scaling is a
congruence; the physical multiplier is recovered by its inverse-variable map.

The input boundary must cover its intended rectangular interface exactly once
with outward-oriented exterior triangles. The implementation checks planarity,
extent, total area and positive-area overlaps with a chart AABB sweep.
It clips each triangle at shell interpolation and multiplier breakpoints.
Upstream scikit-fem degree-four triangle quadrature then integrates the P2
solid/P1 shell and degree-two multiplier products exactly in this envelope.
No solid element shape function or volume quadrature is implemented here.

Integration and multiplier partitions are different objects. Refining the
integration partition must NOT automatically refine the multiplier space.

## Independent counterexample and necessary checks

An independent non-author review identified a reversed-ratio counterexample:
a P2 rectangular solid face consisting of two triangles has 27 physical trace
coefficients, while a five-segment P1 multiplier has 30 coefficients. Thus
C_solid.T has a kernel even if [C_shell,-C_solid] has full row rank. Such modes
can load only the shell with zero net global force/moment. The implementation
therefore rejects either one-sided pairing kernel; this is necessary but not
an inf-sup or locking proof. The explicit coarse multiplier partition remains
a candidate rule requiring a physically scaled refinement study.

Research diagnostics are bounded to 4096 selected facets and 256 multiplier
rows. These limits do not establish a supported engineering size envelope.

## Current evidence and open gates

Passed algebraic cases cover six common rigid motions at zero/nonzero signed
offsets, virtual work and total force/moment balance, coarse explicit multiplier
pairing, the one-sided-kernel refusal, stale geometry/DOF and matrix mutation
refusals, and native affine MPC reconstruction with external blocks.

The membrane solve historically FAILED its componentwise v1 postcheck despite
raw residuals near roundoff. The user-approved registered v2 policy now passes
that specimen through local physical and normwise checks at unchanged 1e-9
limits. It preserves all old diagnostics and failed source/evidence, and
refuses uncertified multi-master reductions. See the normalization record and
verification_registered_v2.json. This is discrete numerical acceptance only.

Analytical bending, Poisson membrane, in-plane shear and twisting patches now
pass their fixed criteria. Seven bounded energy/geometric-mass norm spectra
have positive eigenvalues but do not establish uniform stability or locking.
The original transverse engineering comparison FAILED its then-finest fixed
interior-shear criterion (72.19% versus 5%). Subsequent registered solid-only
controls reproduced that error without a connector. Paired axial-refined
Nx16/Nx32 cases now meet the unchanged target (4.56%/1.41% coupled shear), with
the original failure preserved. This supports axial discretization as a major
contributor, not arbitrary-mesh accuracy or unique interface attribution.
Production qualification remains NO_GO because the other gates are open.

For that comparison, the Saint-Venant parabolic shear flux is outside the
candidate's constant transverse traction space. The admissible variation
delta_u_z=(z^2-t^2/12)/t has zero connector moments, but the reference flux
does nonzero work -Q*t/30 (up to face orientation). Thus the reference is not
an exact coupled patch; discretization and interface-modeling errors have not
been separated. Refinement cannot be assumed to eliminate the latter.

Still unqualified: uniform inf-sup/stability and locking, isolated section-couple
and transformation cases, independent full-solid convergence, transition
distance, complete mesh-ratio matrix, physical offset section consistency,
strong diagnostic control, S3/mixed chains and multi-region coupled behavior.
These are unmet gates, not skipped passes. No general or production shell-solid
connection is advertised.
