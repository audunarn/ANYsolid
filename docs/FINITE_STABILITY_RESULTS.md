# Historical Candidate A result

This failed study is preserved unchanged below. Candidate B subsequently passed
its separate fresh registration; see [revised results](REVISED_MULTIPLIER_RESULTS.md).
The new pass does not change Candidate A's failure or complete Workflow 1.


# Finite stability qualification — NO_GO

The registered study completed all work in 35.781 process seconds with zero
execution failures and verified process cleanup. Its nonzero exit means a
scientific gate failed. Receipt:
`evidence/w1/workflow1-finite-stability-dd745908f7`.

| Assessment | Observed result |
| --- | --- |
| Verified inverse certificates | 18 / 18 |
| Finite positive-energy assessments | 18 / 18 |
| Physical displacement/rotation amplification allocation | 18 / 18 |
| Modal traction/couple amplification allocation | **17 / 18** |
| Independent full-solid references | 6 / 6 |
| Finest matching Q4 refinement cases | 3 / 3 |
| Coupled residual/work/force/moment invariants | 12 / 12 |

## Blocking gate

For `matching_s16_v16_t0p05`, the certified modal traction/couple amplification
upper bound is **5,645,155.4093**, above the prospective **5,000,000** limit.
At the registered residual-uncertainty level 1e-9 this gives 0.00564516 of the
declared modal reference, exceeding the allocated 0.005. The allocation and
physical scaling were selected and independently reviewed before execution.

The computed inverse row-norm upper value is 5,644,372.9272. The verified right
defect is 0.0001386113; Neumann inflation contributes only about 0.0139%, much
less than the roughly 12.9% budget excess. Merely tightening this enclosure is
unlikely to resolve it. This observation is not a formal lower bound on the
exact inverse norm and is not evidence that computed stress/energy is wrong.

Physical-output amplification for that case is 15,994.3278, safely below its
1,000,000 limit. No eigenvalues were deleted, stiffness regularized, multiplier
space changed or gate relaxed after results were observed.

## Physical evidence

Q4 width bending uses an independently known continuum field and a genuine
non-exact shell normal trace. Both native and **whole-core solid** displacement
are checked. Coarse models retain their failed accuracy observations; they are
diagnostics, not promoted configurations. The N16 cases at t=0.2/0.1/0.05 meet
the fixed finest measured targets. Whole-core displacement error is about
0.260417% at each thickness; native-only checks would miss that interpolation
effect. These are finite observations, not combined energy/stress certificates.

Six independent P2 full-solid solves (two meshes at each thickness) pass the
strict reference criteria, including actual common-point refinement differences.
They use real affine surface tractions, essential values and direct SciPy
solution, without shell traces or coupling code. The analytical width-bending
field is exactly P2-representable. Their convergence corroborates this reference;
it does not qualify arbitrary load/geometry/material classes.

Independent non-author review confirmed all source/input identities, actual
single-thread runtime, counts, certificate mathematics and the terminal failure.
The review is same-family; no different-family review is claimed.

## Disposition and remaining work

This registration is **consumed**. Preserve its NO_GO and raw evidence; do not
rerun it, raise the budget or relabel it successful because physical cases pass.
Production weak coupling and full Workflow 1 completion remain blocked.

Principled next candidates include a P1 multiplier partition coarsened by a
factor two while retaining endpoint bases and refinement consistency, or a
separately verified actual-residual uncertainty policy. Either changes the
prospective candidate/acceptance contract and needs a new bounded design study,
independent review and retained comparison with this failure. Neither is adopted
here, and the existing 1e-9 residual limits remain unchanged.

Further open work includes broader engineering/transition-distance convergence,
connected beam/shell/solid qualification and full applicable clean-checkout,
platform and release gates. No merge or package publication was performed.
