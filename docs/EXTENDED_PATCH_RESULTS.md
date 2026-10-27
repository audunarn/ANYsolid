# Extended physical patches — finite results, production NO_GO

Thirteen prospective physical cases meet all their unchanged criteria. The
non-author reviewer independently inspected input/source identities, sampling
masks, all nine stress components and recomputed error maxima. These cases do
not establish uniform stability, general engineering convergence or offsets.

Inventory: Q4 membrane ratios 1:1, 1:2, 1:4, 1:8 and reversed 2:1, 4:1, 8:1;
shifted 4:5 partitions; S3 x-bending; mixed Q4/S3 x-bending; two solid regions
with four transitions; matched S3 all-boundary-node strong diagnostic; and
S3 width bending with nonzero MIN3 edge correction. Native shell contributions
exist only outside the replacement regions. Maximum dimensions are 828 primary
coefficients and 90 multiplier rows, on controlled straight geometry at nu=0.

Membrane and bending references are compatible continuum fields and actual
production shell traces. Line loads use exact segment-integral endpoint weights.
The width-bending case includes its nonzero prescribed field and support work.
All cases check fixed 1% field/energy, 5% interior tensor stress, 1e-9 registered
residual, 1e-10 work and 1e-8 force/moment gates. Strong tying remains explicitly
diagnostic and is never mixed with weak constraint units.

The first process passed three membrane cases, then rejected the 1:8 interface
before its solve. Receipt `evidence/w1/workflow1-extended-patches-030e6dbb32`
retains that construction failure. A final harness-hardening delta landed after
preflight; the parent started prematurely. Its actual frozen source, prospective
criteria and evidence were subsequently independently reviewed, without changing
or rerunning the passing prefix.

The failure was a floating clipping sliver on an exact shared edge, not an
overlapping mesh. An independently reviewed exact SAT confirmation repairs only
the overlap rejection; integration, quadrature and tolerances stay unchanged.
Forty-one focused guard tests pass, including real-overlap rejection and actual
1:8 construction. See `facet-overlap-diagnosis.md`.

An explicit parent-reviewed manual continuation reconciled the original single
process bound. It carried forward four consumed attempt slots and 2.422 seconds,
selected only the ten remaining cases and reduced its deadline to 177 seconds.
Receipt `evidence/w1/workflow1-extended-suffix-ca3b8a8e75` records ten passes in
7.031 seconds. Combined accounting is 14 attempts, 13 actual solves and 9.453
process seconds. Both attempts and the original failed receipt remain; the
continuation is marked consumed and must not rerun. Its executed registration
is retained verbatim in the runtime identity, including its original hash.

The width-bending midpoint correction is 3.125e-5 m, independently matching the
analytic quadratic term. Thus the S3 case tests actual enrichment, rather than
only a field where the new term vanishes. The two-region case contains both
solids and all four interfaces. Maximum observed energy error is approximately
9.01e-11 and tensor stress error 2.20e-10 under the registered scales.

This finite evidence supports implementation and these reference cases only.
The proposed multiplier refinement family still lacks a defended stability
acceptance bound; coarsest-corner selection alone is not that proof. Production
coupling and full W1.4 acceptance remain NO_GO.
