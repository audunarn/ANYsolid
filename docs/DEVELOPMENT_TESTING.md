# Development testing

Run from ANYsolid with the environment containing `.[skfem,test]` and, for host
profiles, the supported ANYsolver ecosystem dependencies. Use that environment's
Python explicitly; no new environment or installation is needed per edit.

| Change / purpose | Command |
| --- | --- |
| First feedback: imports, missing dependency, invalid mesh, affine patch | `python tools/dev_checks.py smoke` |
| Mesh snapshots, scikit-fem adapter, loads or recovery | `python tools/dev_checks.py backend` |
| Host blocks, supports, affine constraints, results or residual scaling | `python tools/dev_checks.py host` |
| Shell traces or weak coupling algebra | `python tools/dev_checks.py coupling` |
| Test tooling | `python tools/dev_checks.py tooling` |
| Shared API/dependencies, cross-boundary changes, unfamiliar impact, pre-handoff | `python tools/dev_checks.py full` |

Backend changes also require host/coupling coverage before handoff. `full` runs
all ANYsolid tests and the explicitly registered ANYsolver solid adapter modules. It is
**not** the full ANYsolver regression suite. Changes to native solver paths also
require the relevant owner tests and its existing portable CI. New host adapter
test modules must be added to `tools/dev_checks.py` before claiming full adapter
coverage. No automatic changed-file guessing or cached green result suppresses tests.
Documentation-only edits need link/diff inspection rather than numerical reruns.

`full` also runs the host's closed-world shell-constructor policy test. New trace
admission/refusal tests can add constructor call sites, so this catches their
inventory impact before the larger portable CI run. Fast coupling and backend
profiles retain their existing scope. For a constructor-policy-only edit, run
`python -m pytest -q ../ANYsolver/tests/test_e4_pl_functional_constructor_policy.py`
with the host source dependencies available.

Profiles are explicit and nonempty. `--dry-run` lists the exact command without
execution; `--collect-only` records collection without claiming test passes.
Default timeout is 180 seconds for the entire pytest process; use `--timeout N`
for a known, justified development check. Timeout/failure never retries itself.
`--solver-root PATH` selects a sibling checkout explicitly.

The runner disables unrelated pytest plugin autoload and inherited pytest options,
sets numerical pools to one thread, and defaults to **JIT on**. `--jit off` is an
explicit diagnostic shortcut, not compiled-path evidence; verify JIT on for any
affected compiled path. Runtime receipts verify actual imported owner paths,
thread pools and Numba settings. The runner does not alter numerical tolerances,
material parameters or solver behavior. Process groups are terminated on timeout
or interruption (Windows `taskkill /T`, POSIX process group).

Each attempt creates `evidence/development/<unique-id>/` with exact command,
source/test hashes, environment, process-wall time, stdout/stderr, JUnit counts,
and effective runtime/version diagnostics. Failed and partial attempts remain.
There is no speedup claim based on selecting less coverage. Use durations to find
slow tests; do not add parallel workers to these small cases by default.

CI retains the complete Windows/Linux Python 3.11–3.14 matrix and ordinary pytest
output. Pip downloads are cached. Every matrix
cell builds a wheel and runs an isolated public P2 smoke from a temporary working
directory. That smoke supplements the existing installed-delivery gates; it does
not replace them or exercise host integration.

Detailed development receipts remain local. No new external evidence upload is
configured; the proposed upload was rejected by automatic approval review.

Scientific qualification remains a separate, prospectively registered activity.
These profiles never launch the manifests, convergence/performance studies or
reference campaigns under `tools/`. They do not renew consumed run authority,
change a NO_GO, authorize release, or replace independent numerical review.
