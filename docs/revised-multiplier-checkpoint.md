# Candidate B: explicit coarsened P1 multiplier proposal

Distinct new authority under the user's revised-design/fresh-qualification
request. Candidate A and `workflow1-finite-stability-dd745908f7` remain failed
and immutable. No old study/helper/manifest/product file will be edited.

Design: new reusable public module function
`anysolid.multiplier.coarsened_p1_partition(shell_corners,solid_corners)` chooses
the input with fewer GEOMETRIC corner intervals, shell on ties, and keeps
indices0,2,4,... plus the final endpoint if needed. It owns immutable output,
does not infer coefficient nodes, snap or renormalize coordinates, and does
not change the connector's explicit-knot requirement. Both input partitions
must be finite, start0, share a positive endpoint, increase strictly and have
spacing ratio<=2. This limit is input-only: lengths[2,2,1] legitimately produce
coarsened lengths[4,1]. No adaptive repair is allowed.

New study retains the exact18 geometries/materials/physics/reference scales
and all limits from the frozen finite study. Only both interface knot lists
and resulting multiplier/KKT counts change. All18 operator assessments and12
matching physical solves are FRESH; only the6 independent full-solid numerical
references may be reused after strict raw-artifact validation. No old operator
certificate or coupled physical pass is reusable. Maximum primary1893 stays;
planned maximum multiplier90 and KKT1881 (versus170/1961 previously).

Actual artifacts inspected: frozen helper SHA
fecbd10f83d306e0929fc4a136408c16dc18d19570b98c7ec5c86ec6ef163be9,
old manifest SHA1a3535858ccb045e9842c84994bb4a2617a8a50e331efa42e94f14927d744901.
The old process finished with exit1/scientific failure, not an execution crash;
its terminal record reports18 metrics,12 physical results,6 references and
zero execution failures. Reference reuse will inspect every raw reference
registration/check/finite array and relevant metric plus source/runtime/input
identities, rather than trust a passed boolean.

Implementation and proposal validation are complete; candidate B is FROZEN
for independent preflight review. No candidate FE assembly, solve or inverse
metric has run. Production remains NO_GO; this is not final acceptance.

The new module/test are independent of ANYsolver. The wrapper compiles the
exact validated frozen helper source into a separate module and calls its
case function only, never its main and never monkeypatching its namespace.
It reconstructs the full derived inventory using the public policy and
requires exact equality; only explicit knots and resulting row/KKT counts
change. Every fresh case/start/phase/result/failure is flushed. A first
execution error terminates the process without retry. All 18 metrics and
12 physical solves must be new; counts distinguish the six reused references
from zero new reference solves. Limits and certificate/physical parameters
are copied unchanged and compared to frozen A at runtime.

The read-only replay checked the old archive hashes, outer command/input
registration, all25 retained outer source identities, embedded old manifest,
all six registrations and finite array shapes, complete primary component
maps, all boundary/coefficient and quadrature stress records, and reference
refinement arrays. Primary/boundary/stress/energy/work/refinement metrics
were recomputed; residual and force/moment numeric predicates were checked
against unchanged limits and immutable source/input provenance. The retained
raw artifact has no stiffness/reaction vectors: replay does not claim to
reassemble those unavailable quantities. All six references passed these
checks. Maximum primary error8.143331495236161e-9 and stress error
4.4904350193063517e-10 are retained-reference observations only, not new FE
results. Python/package versions and recorded thread-pool configuration are
validated; execution additionally requires exact PYTHONPATH/environment and
pool metadata equality. Historical compiled-library hashes were not recorded
and are not invented.

Checks actually run:

- `.venv/Scripts/python.exe tools/run_check.py --name multiplier-policy --timeout 90 -- python -m pytest tests/test_multiplier_policy.py -q`:
  29 passed, 0 failed; process wall0.7030000000086147s. Evidence
  `evidence/w1/multiplier-policy-064980a2d4`.
- `.venv/Scripts/python.exe tools/run_check.py --name revised-multiplier-preflight --timeout 90 -- python tools/revised_multiplier_study.py`:
  exit0,6 raw references validated,0 fresh metrics/physical/reference solves;
  process wall1.0s, cleanup verified active processes0. Evidence
  `evidence/w1/revised-multiplier-preflight-9fbdc54a0c`.
- AST parsing of both new Python modules and the policy test; manifest JSON
  parsing and exact 18-case derived-registration checks passed.

No failed implementation check or scientific candidate attempt occurred.
Independent review and the authorized single scientific execution remain
pending. Proposed execution command, ONLY after parent's final authorization:
`.venv/Scripts/python.exe tools/run_check.py --name revised-multiplier-study --timeout 180 -- python tools/revised_multiplier_study.py --execute`.
The policy changes no normalization, physics, material, load, tolerance or
certificate arithmetic. The dual bound applies only to modal traction/couple;
the measured stress gate is not a rigorous stress-error certificate.
