# Normalization correction — explicitly approved 26 October 2026

The user approved the documented correction. Its final prospective specification
is verification_registered_v2.json, including mandatory local checks and the
independently reviewed reduction restriction below. Failed membrane evidence
and the legacy source are retained under evidence/w1/. Production coupling
remains NO_GO independently of these numerical postchecks.

## Observed witness

The controlled axial membrane case has applied nodal force max 0.5 N and
maximum displacement 0.015000000000000437 m. Raw free-equilibrium error is
2.5626655623976092e-14 N. Raw coupling error is 3.524088605974593e-16 in the
integrated displacement constraint. The controlling transverse constraint has
native contribution -1.914605911549128e-15 and solid contribution
1.5621970509516685e-15; its affine target is zero. The componentwise rule divides
by a 1e-14 floor and reports 0.03524088605974593. It therefore rejects the solve.
The source/test gate has not been removed, relaxed or changed.

## Proposed new prospective manifest version

Keep both acceptance limits at 1e-9. For each RHS define normwise backward error
with infinity norms, before any new acceptance run:

eta_equilibrium = ||P.T (K u + C.T lambda - F)||inf /
  (||P.T K||inf ||u||inf + ||P.T C.T||inf ||lambda||inf + ||P.T F||inf).

eta_constraint = ||C u - g||inf /
  (||C||inf ||u||inf + ||g||inf).

Here u=P z+u0 includes prescribed values, C uses the same assembled coupling
operators as force recovery, and all norms are per load case. A zero denominator
and zero numerator gives zero; a positive numerator with zero denominator fails.
Store dimensional residual maxima and the existing componentwise diagnostics
in addition to the new normwise measures. Do not discard the old failure or
call this a validation of physical accuracy/stability. Production qualification
still requires the separate gates, convergence cases and independent review.

Automatic approval review rejected the first attempted implementation of this
change because replacing the componentwise gate could mask meaningful local
violations. Explicit user approval is required before adopting the prospective
normalization; absent that approval retain the unchanged gate and NO_GO.

## Independent review addendum — global metric alone is insufficient

A non-author reviewer supplied the analytical counterexample C=diag(1,1e-12),
u=(1,1), g=(1,0): the global normwise constraint measure is approximately
5e-13 while the second equation is violated by 100%. Translation/rotation
units and unrelated large displacements also require care. Therefore the
global measures above must NOT become the sole scientific acceptance gate,
even if the original correction is approved in principle.

Before a new acceptance run, register complementary per-row physical checks:
let D convert each native rotational coefficient to a displacement using an
explicit reference length L; solid translations keep unit scale. For each
constraint row use |C_i*u-g_i|/(||C_i*D^-1||1 * U_ref), with a positive
prospectively registered displacement reference U_ref for that physical
interface and case. For projected equilibrium use an explicit force reference
F_ref with the corresponding work-conjugate reduced-coordinate length scales.
Keep the 1e-9 targets, old diagnostics and all failed evidence. No denominator
may be selected from the observed residual or adjusted to obtain a pass.

For the axial specimen only, analytical input references are L=1 m (interface
length), F_ref=1 N, U_ref=F*span/(E*area)=1*3/(1000*0.2)=0.015 m. This describes
a proposed prospective local policy, not an implemented or accepted replacement.
It still requires explicit user adoption and independent source review before
execution. Coupling stability/convergence remain separate unmet gates.

## Adopted applicability restriction

Independent review found another counterexample for general multi-master MPCs:
P=[[1,0],[0,1],[M,M]], D=I, K=I, u=(1,-1,0), F=0 yields apparent errors 1/M
under column-max scaling despite order-one admissible imbalance. The initial
registered v2 policy therefore requires every canonical P row to touch at most
one independent coordinate. This makes DP columns disjoint and orthogonal;
max-column scaling is conservative relative to L2-normalized physical columns.
General multi-master v2 reductions are explicitly refused, with no fallback.
Existing native and legacy analysis behavior is unchanged.

## Verified implementation

The approved correction is implemented in ANYsolver/solid_residuals.py and
integrated through explicit ResidualScales mappings. Independent non-author
review confirmed the formulas, dimensional/reference routing, refusal boundary
and retained legacy diagnostics. The final affected suite passed 148 tests,
including 66 evaluator tests, the scaled-row/MPC counterexamples, zero-RHS
refusal, fully fixed reductions and direct/single/multiple membrane entries.
Separate host regressions confirm refusal occurs before factorization and
without falling back. No failed v1 evidence was removed or relabelled a pass.
The original subsequent transverse-shear accuracy failure was independently of
residual acceptance and remains preserved. Later registered paired Nx16/Nx32
meshes meet that unchanged accuracy target. The broader connector still remains
production NO_GO pending its other qualification gates.

The earlier 'awaiting approval' statements above describe the retained review
history; user adoption is now explicit. No global norm alone is an acceptance
gate. Counterexamples, dimensional checks and prior failures remain recorded.
