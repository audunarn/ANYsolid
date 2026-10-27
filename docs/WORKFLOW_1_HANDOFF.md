# Workflow 1 handoff — refined benchmarks meet targets; production NO_GO

## Current completion blockers after fresh beam and platform verification

The repaired beam finite patch is accepted: two certificates and two physical
cases passed, with one factorization/two RHS. All eight local adapter platform
snapshots passed tests, wheel/sdist builds and installed P2 smoke. The final
current development profile passes 331 tests, zero failures/errors/skips.
See BEAM_REPAIRED_RESULTS.md, PLATFORM_RESULTS.md and qualification.json.

Workflow 1 remains incomplete:

1. The transition reference pair fails global displacement convergence:
   .0029565802 > .001. Its two solves are retained; zero coupled cases were run.
   The registration is consumed. TRANSITION_REFERENCE_REPAIR_PROPOSAL.md gives
   a mathematically reviewed alternative for the same nu=0 BVP; a fresh bounded
   campaign is needed before execution. No narrower ROI or relaxed limit is used.
2. Required host case NLG-007 remains FAIL under the unchanged warped-plastic-Q4
   guard; NLG-003 inherits that failure. Native nonlinear verification is outside
   this linear adapter workflow. No legacy fallback, XFAIL reclassification or
   required-case waiver was adopted. The native owner must resolve this gate.
3. Full host and clean-checkout/remote CI remain unpassed. Local adapter runtime
   snapshots do not replace them. Exact constructor-policy inventory maintenance
   now passes, but neither failed host portable run is relabeled as passed.
4. Historical coupled timings remain Candidate A measurements where multiplier
   blocks differ. Current Candidate B performance claims require their own
   evidence; condensation remains disabled.

All failed evidence and limits are preserved. All owned jobs/sessions have
verified cleanup and no further numerical work was launched after this handoff.
No Git delivery, merge or publication occurred. Historical checkpoints below
retain their original outcomes and scope.

## Final revised-candidate handoff

Candidate B's registered 18-operator/12-physical study is independently accepted.
All three subsequent broader certificates pass; their physical scope is accepted
using the original unaffected checks plus a distinct exact retained-work audit
(`2.3266364125e-11 <= 1e-10`). The original two-region double evaluation failed
and stays failed. See REVISED_MULTIPLIER_RESULTS.md and the separate dispositions.
No fresh solve was used for that correction. All registrations are consumed.

Workflow 1 is still incomplete: connected-beam physical results were lost to the
postsolve harness error; transition-distance/independent full-body shear coverage
and full clean-checkout/platform gates remain open. Coupled performance evidence
is scoped to Candidate A where blocks differ. No limit, budget or source identity
was silently changed; no automatic retries or release actions occurred.

## Current revised-candidate checkpoint — 27 October 2026

Candidate B resolves the registered finite stability gate: 18 fresh operator
assessments and 12 fresh physical results pass, with six authenticated references
reused. Maximum dual amplification is 1,257,436.6214 against the unchanged
5,000,000 limit. Independent non-author review accepted this finite scope.
Candidate A remains failed. See REVISED_MULTIPLIER_RESULTS.md for exact commands,
identities, limits and evidence. Development checks now pass 316 tests, zero
failures/errors/skips, in 16.875887 process seconds.

Workflow 1 remains incomplete. Connected-beam physical acceptance is blocked by
a consumed one-attempt harness failure after the host solve; no physical results
were saved or inferred. The original shifted membrane profile violates B's
input-spacing limit and remains unsupported. Broader engineering/transition
distance and applicable clean-checkout/platform gates remain open. The older
checkpoint below describes Candidate A and is retained as history.

## Latest completion continuation — 27 October 2026

**Terminal checkpoint: Workflow 1 remains incomplete; scientific NO_GO.** The
finite stability study completed 18 operator assessments, 12 coupled cases and
6 independent full-solid references. One thin 16:16 operator failed the modal
amplification allocation (5,645,155.4093 versus 5,000,000). All references and
finest physical targets passed. The registration is consumed; see
FINITE_STABILITY_RESULTS.md. No threshold was relaxed or failed case promoted.
Final development checks pass 287 tests in 15.175 seconds with no skips/failures;
evidence `evidence/development/20261027T100646Z-b14d50fb`. Full platform/repository
CI remains unexecuted. Further candidate design/qualification is required before
production coupling can advance; existing all-solid work remains independently
usable within its documented development/verification envelope.

The development regime now passes 263 tests in 14.856 seconds, including new
production-derived S3/mixed traces, the multiplier consistency witness, explicit
strong diagnostic opt-in and exact overlap-confirmation regressions. No native
mechanics kernel was changed. Unrelated results work remains protected.

Thirteen extended finite physical cases pass independent non-author evidence
review: mesh ratios through 1:8 and reversed, shifted partition, S3/mixed bending,
two cores/four transitions, a strong nodal control and S3 width bending. The
original construction failure, source-review timing mistake and reviewed manual
continuation are retained in EXTENDED_PATCH_RESULTS.md. The continuation is
consumed: 14 attempts, 13 actual solves, 9.453 process seconds; do not rerun.

Four further signed-offset membrane/bending fixtures passed, with explicit
generalized-section B/D shifts and trace transport about the same physical
material centroid. Independent review supports those four static reference
models only. Actual native section-resultant recovery and a separate stiffness
symmetry measurement were not performed. Other eccentric geometry is unqualified.

W1.5 all-solid measurements now cover 1,275 DOFs and 1/10/100/1,000 RHS with
complete recovery, one reusable host factorization and independently checked
equivalence; see REPEATED_LOAD_RESULTS.md. Coupled performance is not measured.
Local isolated baseline-plus-owned-overlay host/adapter wheels pass license,
all-solid/S3/1:8 installed smoke checks and both installed examples on Windows
CPython 3.11. This is not full clean-checkout or multi-platform CI.

The finite amplification/locking study above now supplies evidence and a real
blocking gate. A universal theorem was not required. Larger engineering
references, connected beam/shell/solid coverage and
full applicable release/platform gates remain incomplete. No release is made.

## Current outcome

Continuation on 27 October investigated the coarse shear failure without
changing production code. Four solid-only controls reproduced the large error
without a connector and identified axial resolution sensitivity. Two new
matched control/coupled pairs then met every unchanged registered target:

| Solid resolution | Control shear error | Coupled shear error | Pointwise paired difference |
| --- | ---: | ---: | ---: |
| Nx16 Ny1 Nz8 | 4.396% | 4.565% | 0.934% |
| Nx32 Ny1 Nz8 | 1.360% | 1.413% | 0.178% |

Each pair shared the exact prepared solid, quadrature and interior mask; native
axial4 remained fixed. Eight new solves completed without execution failures
or retries. The original failed specimen remains failed, and no numerical
operator, reference, tolerance or smoothing was changed. This supports axial
discretization as a major contributor, not unique attribution of interface
effects or a general accuracy/convergence claim. See SHEAR_DIAGNOSIS.md.

The user-approved registered_physical_v2 correction is implemented and reviewed.
It requires prospectively supplied ResidualScales and BOTH local physical and
normwise checks at the unchanged 1e-9 limits. Legacy diagnostics and failed v1
source/results remain preserved. Without registered references, the existing
legacy path remains explicit. General multi-master v2 reductions are refused
before factorization; disjoint-support reductions are covered by the reviewed
physical scaling argument. No implicit fallback or observed-error-derived
reference scale is used.

ANYsolid provides lazy upstream P1/P2 tetrahedral assembly, immutable tet4 SI
snapshots, consistent loads (including affine traction), physical traces,
full tensors, rigid modes and signatures. ANYsolver supplies the explicit
SolidModel wrapper, native-preserving block layout, affine support/MPC handling,
reusable sparse factorization, multiple RHS and result slices. Unsupported
nonlinear/modal/transient entries refuse the wrapper.

The planar production-Q4 weak connector remains research-only. Membrane,
bending, Poisson contraction, in-plane shear and twisting specimens pass their
registered checks. Seven bounded verification spectra have positive eigenvalues
and verification-norm Cholesky checks; they are NOT uniform inf-sup/locking proof.

## Historical coarse failure — preserved, not relabelled

The three-level transverse engineering comparison completed without execution
failures. Its finest 1497-primary/20-multiplier case gives:

| Criterion | Error | Limit | Result |
| --- | ---: | ---: | --- |
| Tip displacement | 0.1266% | 1% | Pass |
| Tip rotation | 0.000274% | 1% | Pass |
| Twice strain energy | 0.1266% | 1% | Pass |
| Axial stress | 1.7633% | 5% | Pass |
| Interior shear stress | 72.1933% | 5% | FAIL |

Registered equilibrium and constraint residuals pass. The fixed interior mask,
component scales, references and tolerances were not changed. An independent
non-author source/evidence review found no obvious loading, reference, tensor
index or sampling mistake. The controlling retained point is
(0.6964285714,0.9285714286,-0.0035714286) m: actual sigma_xz=0.002075939529 Pa,
reference=0.007490433673 Pa. Cause remains unresolved: discretization and known
finite-traction-space/interface modeling error were not separated. Do not
infer a plateau, physical instability or a convergent shear rate.

The earlier constant-shear exact patch was withheld BEFORE execution because
native Q4 uses the 5/6 shear correction. The replacement engineering reference
was prospectively registered and explicitly was NOT an exact coupled patch.
No unregistered physics run, sample exclusion or tolerance change followed that
campaign's NO_GO. The later Proceed instruction authorized the two separately
registered discriminating designs above; their four-solve authorities were
each consumed without rerunning the old campaign.

## Checks and evidence

Numerical environment: Windows x64 CPython 3.11, NumPy 2.4.6, SciPy 1.17.1,
scikit-fem 12.0.2. Exact commands, source/input hashes, full diagnostics, process
wall durations, cleanup receipts and JUnit are indexed by evidence/w1/summary.json.

- ANYsolid: python -m pytest tests/test_backend.py -q: 77 passed (unchanged
  backend inputs; retained parent acceptance run).
- ANYsolver: python -m pytest tests/test_solid_residuals.py tests/test_solid_models.py
  tests/test_solid_coupling.py tests/test_submodel_transfer.py
  tests/test_constraint_audit.py -q: 148 passed, 0 deselected, process wall 12.344 s.
  The 66 evaluator cases are INCLUDED in that total, not additional tests.
- Registered membrane direct/single/multiple entries pass, preserving the v1
  diagnostic failure. Actual affine and mocked free-single-master/multimaster
  routing tests protect the new applicability/refusal boundary.
- Bending pilot and three proper physical patches passed fixed criteria;
  seven spectra completed as diagnostics only. The held constant-shear case
  is not a pass. See coupling-feasibility-checkpoint.md.
- Three transverse comparison levels completed; finest scientific gate failed.
  See transverse-shear-checkpoint.md and its registered manifest.
- New control command: python tools/run_check.py --name shear-isolation
  --timeout 180 -- python tools/shear_isolation.py: four solves, zero execution
  failures, process wall 2.922 s. Evidence shear-isolation-c9e5b50eda.
- New paired command: python tools/run_check.py --name paired-axial
  --timeout 180 -- python tools/paired_axial.py: four solves, zero execution
  failures, both pairs meet their registered targets, process wall 6.437 s.
  Evidence paired-axial-03080fe925. Maximum coupled primary count 10065, 20
  multiplier rows. Sparse matrix storage is recorded, not factor/RSS savings.
- All-solid 1/10/100/1000 RHS reuse and example passed. Tiny integration
  measurements are not engineering performance/RSS or speed-up evidence.
- ANYsolid and ANYsolver wheels built; final installed-host smoke passed with
  python -I outside source trees and installed dependency distributions:
  ANYmaterial 0.2.0, ANYmesher 0.5.0, ANYgeometry 0.4.5, ANYfileio 0.3.2,
  same-checkout ANYsolver-results 2.1.1. Lazy shell-only import was verified.
- Existing ANYsolver source/artifact license compliance and git diff --check
  passed. Original dirty results work remains hash-identical and protected.

The source/evidence review was by a non-author OpenAI agent, not a different
model family; Claude subscription weekly limit prevented that route. No API
fallback or further quota probe occurred. Review did not waive any scientific
gate. Full clean-checkout CI and other Python/OS combinations remain unexecuted.

## Remaining scope and next decision

Production coupling remains NO_GO due to the remaining broader qualification
gates. The refined Nx16/Nx32 benchmark shear criteria are now met; it is no
longer correct to state that every tested mesh fails that criterion.
Do not promote broad nonmatching, S3/mixed chains, coupled multiple regions,
physical offsets, strong diagnostic comparison or region condensation. Wider
stability/convergence and measured shell-only before/after performance remain
open. The controlled results are not universal mesh counts or permission to
promote arbitrary geometry/families. Wider stability, orientation, nonmatching,
physical-offset and mixed-model acceptance must retain their independent gates.
No blind refinement or altered threshold is justified by these finite cases.

Only ANYsolid and ANYsolver were modified. ANYsolver baseline HEAD remains
1cff283d67ba31bf6d5dc816e2b55bd8359daa9b; changes are uncommitted. Built version
0.4.7 host wheels are local candidates, not a new published release. ANYsolid
0.1.0 is unpublished. No commit, merge or package publication occurred.
