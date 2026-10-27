# Adapter eight-cell platform matrix: setup checkpoint

CURRENT FINAL RESULT: all8 requested local owner-CI platform cells PASS.
This is a recorded snapshot matrix, not a clean checkout or full host CI.
The setup notes below are historical; final results and post-matrix impact
are recorded at the end. No further execution is authorized by this document.

Scope: CURRENT owner ANYsolid CI contract, all adapter tests followed by
sdist/wheel build, built-wheel installation and isolated public P2 smoke.
Windows/Linux CPython3.11/3.12/3.13/3.14, all8 cells retained. This is a local
owned-input snapshot, not clean-checkout CI, full ANYsolver coverage or physics
qualification. No scientific study is invoked. No cell tests/build/smoke have
started; root setup review/GO is pending.

Windows runtimes are the four supplied installed interpreters. Elevated WSL
discovery confirms exact distribution Ubuntu-24.04, Python3.12.3 at
/usr/bin/python3.12 and existing managed3.13.12 via
/home/audunarn/.local/bin/python3.13. Linux uv is installed at
/home/audunarn/.local/bin/uv; timeout and setsid are available. Linux3.11 and
3.14 require owned managed installs under the new adapter-platform evidence
directory, using uv python install --install-dir ... --no-bin. Fresh venvs,
cache and temporary directories stay under owned evidence. Main .venv and all
global/sibling installations remain unchanged; Numba is not an adapter dependency.

Planned runner: one immutable source/build-input catalog copied into separate
per-cell worktrees (src/tests/tools/examples and packaging metadata), all current
tests including9 new transition synthetic tests. Each cell records runtime,
versions, one-thread effective pools, source digest, exact commands/full logs,
JUnit counts, wheel hash/origin, isolated public smoke and cleanup. Installed
smoke uses -I and the existing public P2 script. No automatic skipped cell or
test-filter workaround is allowed.

Windows processes use the established suspended-assignment Windows Job Object
supervisor. Linux phases use Linux start_new_session process groups, bounded
waits, SIGKILL on timeout/leftover children and /proc session-member verification;
a Linux SIGTERM handler cleans active owned sessions. A Linux-side GNU timeout
wrap bounds the whole cell, independently of Windows/WSL process handles.
Only owned session IDs are targeted. Windows cannot stand in for Linux cleanup.

Execution plan: prepare snapshot, materialize runner, establish isolated runtimes
and install dependencies; hand over actual setup for root review. Only after GO
run8 cells, each<=300s, cumulative pytest+smoke process budget<=1200s, separate
bounded install/build preparation. First slice aims at a working first cell.
No workers/Git/network authentication/provider changes or sibling edits.

## Actual setup ready for root review

Stage: `evidence/w1/adapter-platform-20261027T122005Z-96bc6a36`.
Manifest SHA256:
`eda625f225439915c8c0b40f4815ec9363162573f8e1bcffcc818cec79c9b0ef`.
52 source/build input identities copied once. Per-cell source worktrees keep
build-generated egg-info/build files away from the canonical input copy.
Environment explicitly removes inherited sibling PYTHONPATH/plugin overrides.
No host/main qualification dependency is installed or needed.

AST parsing passed. Actual Linux cleanup self-check command:
`.venv/Scripts/python.exe tools/adapter_platform_matrix.py probe --stage C:/Github/ANYsolid/evidence/w1/adapter-platform-20261027T122005Z-96bc6a36`.
Linux session404 contained owned parent404/child405. Deliberate1s timeout;
process wall1.018953619s, both processes killed/reaped, remaining_members[],
cleanup verified. Probe passed at `probes/linux-timeout/probe.json`.
The Windows WSL relay separately completed with cleanup0 in4.625s; it does
not substitute for the Linux session proof.

Actual isolated environment setup command:
`.venv/Scripts/python.exe tools/adapter_platform_matrix.py setup --stage C:/Github/ANYsolid/evidence/w1/adapter-platform-20261027T122005Z-96bc6a36 --cell windows311`.
Installed into ONLY this new cell runtime: ANYsolid0.1.0,numpy2.4.6,scipy1.17.1,
scikit-fem12.0.2,pytest9.1.1,build1.6.1,threadpoolctl3.7.0. Dependency check
passed. Full bounded phase receipts/stdout/stderr are under `cells/windows311`.
Main .venv, global runtime packages and siblings remain untouched.

Current counts:0 CI test cells attempted;0 pytest/build/installed-P2 runs;
0/1200s cumulative test-process budget consumed. Root setup review/GO requested
before the first cell command. No scientific study is part of the matrix.

## Final eight-cell result

Root reviewed the setup/source/supervision and authorized the matrix. Every
final cell executed ALL adapter tests without deselection/skip, built sdist
and wheel, force-installed its own wheel, passed the existing isolated `-I`
public P2 smoke and passed installed dependency checks. All effective numerical
pools were single-threaded. The original8-cell CI YAML remains unchanged.

| Cell | Actual Python | Passed | Fail/error/skip | Cell wall(s) | Pytest+smoke wall(s) |
|---|---|---:|---|---:|---:|
| Windows3.11 | 3.11.9 | 194 | 0/0/0 | 11.727252 | 2.734000 |
| Windows3.12 | 3.12.13 | 194 | 0/0/0 | 11.812300 | 3.032000 |
| Windows3.13 | 3.13.9 | 194 | 0/0/0 | 10.619008 | 2.531000 |
| Windows3.14 | 3.14.2 | 194 | 0/0/0 | 10.746653 | 2.547000 |
| Linux3.11 | 3.11.15 | 195 | 0/0/0 | 59.729099 | 11.329475 |
| Linux3.12 | 3.12.3 | 195 | 0/0/0 | 50.956347 | 9.699330 |
| Linux3.13 | 3.13.12 | 195 | 0/0/0 | 49.816672 | 9.093291 |
| Linux3.14 | 3.14.3 | 195 | 0/0/0 | 60.465265 | 11.430263 |

Final matrix total1556 passing test cases,0 failures/errors/skips. Linux adds
one pure tooling temporary-workspace regression compared with the earlier
Windows snapshot. No passed Windows cell was repeated. This is explicitly not
a claim that the snapshots or later ROOT tooling bytes are identical.

Windows passing cell receipts/artifacts are in
`evidence/w1/adapter-platform-20261027T122824Z-a8d13295/cells/windows311` through
`windows314`; manifest SHA
`a28699406e32a5b512a06483a48836afedb6160636fbebbb63d352ec2943b23f`.
Linux passing receipts/artifacts and the final aggregate are in
`evidence/w1/adapter-platform-20261027T124413Z-f423d33f`; manifest SHA
`46245bd2bb12790c71dabc92b7d710026972a719f883f2aaf3018a5ac8bde55e`.
The aggregate `matrix.json` has complete=true and explicit imported Windows
receipt lineage. `runtime-lineage.json` proves unchanged production/packaging
inputs and records runtime reuse. `final-report.json` contains all8 runtime
versions, source identities, complete wheel/sdist SHA256s, phase walls, package
origins, pool settings, snapshot hashes and post-matrix verification accounting.
No large duplicate byte catalog is needed per cell.

Actual Windows invocation was
`.venv/Scripts/python.exe tools/adapter_platform_matrix.py run --stage C:/Github/ANYsolid/evidence/w1/adapter-platform-20261027T122824Z-a8d13295 --cells windows311 windows312 windows313 windows314`.
The final Linux controller invoked the same public `run_matrix` routine with
`linux311 linux312 linux313 linux314` and the final stage. Each Linux cell's
retained relay identity records the exact WSL/GNU-timeout/controller command;
each phase identity records the exact pytest/build/install/smoke command.
These are historical consumed invocations, not instructions to rerun them.

## Failures, repairs and carried resource accounting

All original failed directories and receipts remain unchanged:

- `adapter-platform-20261027T122005Z-96bc6a36`: initial runtime probe log path
  collided with the existing runtime venv directory, before tests. Repaired
  to `runtime-probe`; a synthetic end-to-end phase regression verifies that
  the venv remains intact and every phase can complete.
- `adapter-platform-20261027T122607Z-1b1ba12b`: four Windows suites each had
  190pass/4fail. The4 failures were tooling assertions that incorrectly
  searched checkout ANCESTOR strings for `evidence`. Selection tests now check
  actual targets relative to the checkout, explicitly exercising an ancestor
  named `evidence comparison parent`. No scientific exclusions were weakened.
- Managed Linux3.11/3.14 downloads succeeded, but uv exposed both canonical
  patch paths and minor aliases; the original lookup was ambiguous. Setup
  resumed using explicitly recorded canonical owned bases, not a different
  interpreter. A uv archive-cache rename on the Windows-mounted filesystem
  then failed EACCES. CI-equivalent isolated `pip install --no-cache-dir`
  completed the two environments; failed uv phases remain retained.
- In the Windows passing stage, all4 original Linux attempts stopped BEFORE
  collection: pytest fd capture's unlinked temporary-file truncate failed on
  DrvFS. Root approved private native Linux temporary storage, matching
  Ubuntu CI filesystem semantics. Default capture and all tests remained
  enabled. The final Linux snapshot uses unique `/tmp/anysolid-adapter-platform-<stage>/<cell>`
  workspaces and owned disposable caches; persistent runtimes/source/artifacts
  and every log/receipt remain in ANYsolid evidence.

Failed phase time was carried across each fresh snapshot. Final matrix ledger:
77.91469707399348 cumulative test-process seconds, including earlier failed
cell phases and preceding focused regressions. Subsequent focused tooling
checks, including a preserved failed focused check, bring the complete
recorded total to88.43966170901281s of1200s. No budget reset or additional
scientific authority occurred. All individual processes/cells remained within
their registered bounds. Exact durations are from receipts, not pytest timing.

All48 successful matrix phase receipts verify cleanup. Windows uses suspended
Job Object assignment and active-process0 proof. Linux controller is a child
subreaper; each phase starts a new owned session and checks `/proc` after
kill/reap, with no remaining session members. GNU timeout independently bounds
the whole Linux cell; Windows relay cleanup does not substitute for Linux
proof. The initial deliberate parent/child timeout probe also passed. Private
native temporary directories are retained; no unrelated/global temp was deleted.

## Final ROOT tooling impact and integration

After the matrix completed, ROOT-only loader lookup now deduplicates canonical
physical paths with resolve(), while rejecting zero or multiple physical
interpreters. Actual Linux discovery demonstrated2 aliases ->1 physical
interpreter for both3.11.15 and3.14.3. A portable direct-indirection regression
tests alias identity and real ambiguity without Windows symlink privileges.
One focused audit initially addressed the wrong fresh-stage managed directory;
its refusal is retained in `adapter-platform-loader-linux-5c005f42`. A later
focused assertion incorrectly called a path under its OWNED temporary ancestor
unowned; the test now uses a genuinely neutral absolute path. Its1fail/18pass
is retained in `adapter-platform-loader-linux-ce405c52`. These are tooling
verification failures, not matrix/physical failures, and were not hidden.

Final full-profile integration adds ONLY host
`tests/test_e4_pl_functional_constructor_policy.py` to FULL. No new profile;
fast coupling/other profiles remain unchanged. Expected-inventory regression
was updated. DEVELOPMENT_TESTING.md is outside worker ownership; parent was
asked to add the impact note.

Final focused checks after all ROOT tooling/inventory changes:

- `.venv/Scripts/python.exe tools/run_check.py --name adapter-platform-tooling-integration-final --timeout 90 -- python -m pytest tests/test_dev_checks.py -q`:
  19pass/0fail, process.6090000000112923s, cleanup0;
  `evidence/w1/adapter-platform-tooling-integration-final-98bdba2091`.
- The same19 focused tests ran under the existing isolated Linux3.12 runtime,
  current ROOT inputs, native TMP, Linux session supervision and JUnit receipt:
  19pass/0fail, evidence
  `evidence/w1/adapter-platform-tooling-linux-final-048b71ef`.

Parent then ran the final CURRENT full development profile:331pass,
0fail/error/skip,43.3643615s, evidence
`evidence/development/20261027T125640Z-901c9157`. This separate integration
receipt covers the changed helper tests and constructor-policy inventory; it
does not rewrite any of the8 matrix snapshot identities. Parent independently
reviewed the orchestration/temp/alias regressions and FULL-only inventory diff.

Current owned source SHA256s:

- tools/adapter_platform_matrix.py:
  `f897e1ba00b76a33201bf092f6e72e7226eec2e9783e207d1ebecc51f7a17583`
- tools/dev_checks.py:
  `ca53dbb0783f2302e7c17f4dff6e9f4ee03d4db8b74e460a9ea61ea3994fbb88`
- tests/test_dev_checks.py:
  `2ce6705c91dd27e0c0d62ab3c36deaa15c014d87fc0bb3d87c29bc2cfd62a6e6`

Source/backend/mesh/coupling/multiplier, README, pyproject, LICENSE and the
complete8-cell CI matrix stayed byte-identical across the passing snapshots
and final impact audit. Root's later `capture_beam_verification.py` and future
`stage_host_candidate.py` bookkeeping changes are explicitly listed in the
post-matrix input delta; they are not adapter product/build changes. No sibling
repository files were edited by this worker. No global/main Python packages,
Numba configuration, Git/auth/provider state or frozen scientific artifacts
were changed. Existing sibling dirty/protected results work was not touched.

The owner platform milestone is verified within this local snapshot scope.
Clean-checkout CI, full host CI and production qualification are not claimed.
The separate transition reference convergence gate remains FAILED/consumed;
root's required NLG007 unsupported warped-plastic-Q4 host failures remain
unwaived outside this platform result. No further code/test/process launch is
authorized after this final handoff.
