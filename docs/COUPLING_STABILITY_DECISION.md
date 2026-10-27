# Coupling stability decision — bounded Candidate B accepted

Current disposition: Candidate B passed its separate 18-operator finite study,
with all limits unchanged. See [results](REVISED_MULTIPLIER_RESULTS.md) and
`revised_multiplier_disposition.json`. The historical reasoning and Candidate A
failure below remain evidence. Wider production qualification is still open.

The existing seven spectra are finite diagnostic observations. Positive
eigenvalues and full row rank do not establish uniform stability or absence of
locking. No absolute beta threshold may be selected from those observations.
The existing geometric-mass regularization also scales transverse shell terms
like thickness, while bending stiffness scales like thickness cubed. A declining
beta in that norm cannot by itself diagnose physical instability.

A fixed multiplier partition `[0,L]` does not define a general convergent
interface refinement family. For L=1, take the represented P2 solid displacement
jump `(0,0,6*s*s-6*s+1)`, with zero shell trace. Its integrals against both P1
line tests vanish; the two in-plane thickness-moment modes see no normal jump.
The actual connector therefore admits this nonzero jump for every refinement
that retains those two multiplier knots. This leaves the previously passing
uniform-load cases intact, but prevents their promotion to general interfaces.
`ANYsolver/tests/test_solid_multiplier_consistency.py` exercises this witness on
the real coupling matrices and shows that a refined admissible multiplier
partition detects it. It is a contract counterexample, not an inf-sup study.

The non-author review proposes a research family for quasiuniform structured
face strips: select P1 knots from the trace with fewer corner intervals, tie
breaking in favor of the shell. Solid stations must come from declared geometric
strip vertices, not a union with P2 coefficient locations. The rule must refine
with both meshes. Common integration cuts remain independent. This is a proposed
rule, not an automatic production selector or a validated capability.

Initially restrict endpoints to free interface ends without support/MPC action
or shared-interface junctions. Do not silently drop endpoint rows. Mesh-shape
and spacing regularity, endpoint ownership, dimensional norms, a defensible
stability/right-inverse bound and independent reference convergence must be
established before production qualification. Shifted and reversed mesh ratios
are separate cases, not consequences of one-sided rank checks.

The initial metric prerequisite is now resolved at the design level: a universal
continuum theorem/Fortin bound is not a requirement of this bounded plan. A
prospective finite study will bound the inverse of the actual physically scaled
KKT operator, with explicit residual-to-output amplification budgets, and assess
non-exact Q4 width bending against an analytical convergence reference. This is
more than checking rank or positive eigenvalues. Its norms, error allocations,
roundoff certificate, inventory and execution must still pass independent review.
The registered study has now executed. All 18 inverse certificates and all
finest physical-reference checks pass, but one thin 16:16 case exceeds the
prospective modal amplification budget. See FINITE_STABILITY_RESULTS.md for the
exact NO_GO, evidence and consumed authority. No old campaign is renewed.
