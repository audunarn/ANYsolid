# Revised multiplier broader physics: prospective checkpoint

Owned files are only this checkpoint, the new runner and new manifest.
Candidate B's accepted finite family is a prerequisite, not production
qualification. Existing studies/manifests/evidence remain unchanged.

Four original physical configurations are selected: shifted Q4 membrane,
mixed Q4/S3 x-bending, two replacement regions/four transitions, and S3
transverse-width bending. All interface partitions change by the public
fixed coarsening policy. Only explicit knots and resulting row counts change
in their physical registrations. Original closed-form references, loads,
supports (including affine values/work), sampling and units remain intact.

The frozen finite helper's whole case runner assumes one region and width
bending. Therefore the new runner must assemble generic multi-region blocks
itself and reuse only its scaled-KKT/certificate/positive-energy functions.
It will compare whole-core coefficients for every region as well as native
fields, retain all stress ROI tensors, and calculate a conservative exact
ceil-Fraction physical output factor from each original case's references.
Expected factors are 1,2,3,4; no hardcoded width factor is used.

Bounds: four fresh metrics plus four fresh physical solves, one90s outer /
85s inner process, primary<=1000, KKT<=1100, multipliers<=100. New measured
field/energy .009 and stress .045 are prospective stricter criteria; original
.01/.05 checks will also be reported. Certificate bounds remain1e6 physical
output and5e6 modal traction/couple; no stress certificate is inferred.

Remaining: materialize runner/manifest, inspect source and perform only
stdlib AST/registration audits. No FE assembly, factorization or solve is
authorized before final frozen source review. No other old physical cases
are fresh B tests; any reuse requires separate parent adjudication.

## Final proposal and adopted admission delta

The initial four-case audit found a real admission conflict before any
numerical import: original `q4_membrane_shifted_4_5` has solid corners
`[0,.1,.3,.55,.8,1]`, nominal intervals `.1,.2,.25,.25,.2` and spacing ratio
2.5, exceeding B's input limit2. The public policy validates both inputs,
including the unselected finer side. Parent prospectively withheld that
original profile and retained the policy/geometry unchanged. It is explicitly
`WITHHELD_UNSUPPORTED_B_INPUT_PARTITION` in the new manifest. It is not covered
by the distinct valid shifted4:5 geometries in the accepted finite B family.
The original physics result remains preserved; no B pass/failure was measured
for this withheld profile. No replacement case is added.

The final THREE-case proposal is implemented and FROZEN for independent
review. It calls only exact-source compiled frozen fixture functions and
scaled-KKT/certificate/positive-energy functions; neither old main nor the
single-region old case runner is invoked or monkeypatched.

| Fresh configuration | Primary | Multiplier | KKT | Output factor |
|---|---:|---:|---:|---:|
| mixed_bending_weak | 477 | 20 | 479 | 2 |
| two_replacements_four_transitions | 828 | 40 | 850 | 3 |
| s3_width_bending_min3_term | 387 | 20 | 389 | 4 |

The row matrix is assembled with a separate solid column block for every
region, retaining each operator's native block and placing its negative
solid block only in the named region. Selection supports and actual dimensions
are verified before any factorization. Canonical stored Kr/B, formed H, all
scales and free-coordinate ownership are serialized. Common interface U and
L=1 are checked; the modal scales are F/(L*t) three times and6*F*L/t² twice.
All original physical references/loads/supports/ROI remain byte-value equal
in the derived case registrations, except explicit knots and row count.
New measured .009/.045 criteria are stricter prospective observations, not
combined certified energy/stress bounds. Both original .01/.05 flags remain
visible. The inverse certificate is for the registered ideal scaling of
canonical stored matrices with the frozen formation uncertainty arithmetic.
Positive-energy QR/Cholesky is labeled a numerical assessment.

The runner serializes all native and solid coefficient fields, exact fields,
mesh identities/arrays, all quadrature stress tensors/ROI, physical loads,
support reactions and affine support work. It includes whole solid coefficient
displacement error for EVERY region in the mixed global field maximum.
Virtual work uses each operator's actual interface force action. Partial
metric/physical attempt/result counters survive ordinary execution failure;
the first such failure stops subsequent cases. Scientific gate failures do
not alter the registered next case. Runtime must match recorded interpreter,
packages, PYTHONPATH, thread environment and complete single-thread pool
metadata from accepted B. Parent's exact disposition file/source hash and
status `PASSED_FINITE_CANDIDATE_B` are required at execution.

## Verification and remaining authority

Only stdlib AST/manifest/source audits were run. The initial audit refused
the unsupported shifted partition as expected; this was an admission finding,
not a numerical attempt. Following parent exclusion, the three derived case
registrations,23 source/input hashes, unchanged certificate registration,
actual count formulas and exact-factor ceiling derivations passed audit.
The audit asserted NumPy, SciPy, scikit-fem and ANYsolver were NOT imported.

Exact persisted check command:
`.venv/Scripts/python.exe tools/run_check.py --name revised-broader-proposal --timeout 30 -- python tools/revised_broader_physics.py`

Exit0;2 JSONL records (identity/proposal-only),0 fresh metrics,0 physical
solves,0 reference solves. Process wall0.21899999999732245s; cleanup verified
active processes0. Evidence: `evidence/w1/revised-broader-proposal-055176c8e2`.
No unit tests were run: there is no new certificate arithmetic, and only
stdlib proposal checks are authorized before review. No FE assembly/solve or
inverse action was run. Candidate A and all prior failures remain unchanged.

Runner SHA256:
`67719d9d2b9adf2496edb7e0d291419d02ecb4dc4a9c1faafb2f1ff9d4827758`.
Manifest SHA256:
`6c6845da4bcb37b47bda571b89427fe9330f461962822bd14bc879cbd6f6b9de`.

Independent source/math review and explicit execution authorization remain
pending. The prospective command is
`.venv/Scripts/python.exe tools/run_check.py --name revised-broader-physics --timeout 90 -- python tools/revised_broader_physics.py --execute`.
It has at most3 fresh metrics and3 physical solves,85s inner deadline, and
no automatic retry. All other old cases are not fresh B tests. No universal
stability or production acceptance is claimed; production remains NO_GO.
