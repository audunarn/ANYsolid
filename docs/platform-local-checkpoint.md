# Local platform candidate preparation

Owner: this task's local platform worker. ANYsolver is read-only. New staging,
logs and outputs are confined to evidence/w1/platform-local-*.

Plan and acceptance:

1. Stage all tracked ANYsolver HEAD top-level inputs except historical
   .qualification/.development; overlay only the unchanged
   stage_host_candidate.py OVERLAY. Record archive/source identities and protect
   unrelated dirty results files. Acceptance: baseline/overlay hashes and unchanged
   protected file hashes.
2. Audit effective staged host import, sibling roots, numerical pools/JIT and
   canonical complete portable inventory without running tests. Acceptance:
   useful runtime.json and nonempty inventory. Root must review preparation.
3. After root authorization only, run canonical full portable inventory once,
   two workers/2400s inside unchanged run_check.py's <=2460s process-tree bound.
   Acceptance: canonical terminal counts/results and supervisor cleanup receipt;
   failures/timeouts remain failures and do not authorize another attempt.

This is Windows CPython3.11 full tracked baseline plus explicitly owned overlay,
not a clean committed checkout, full platform matrix, installed-wheel acceptance,
scientific qualification or release. Other siblings remain read-only.

Open risks: missing local dependencies, portable tests' reliance on deliberately
excluded historical artifacts, and resource/runtime failures. No installation,
network access, credential change, Git mutation or automatic retry is permitted.

Preparation source is tools/platform_local_checks.py. Its run phase refuses to
execute until the new stage identity has execution_authorized=true set by root.
The attempt flag becomes consumed before canonical execution. No source tests or
portable inventory has run yet. Root review is pending.

## Preparation checkpoint

Staged evidence/w1/platform-local-f41a6b6b84 from tracked HEAD plus explicit unchanged owned overlay. Archive/source/overlay identities and protected dirty file hashes are saved. No portable run occurred.

Runtime preflight failed before inventory/tests because the specified ANYsolid .venv lacks numba. Failure stdout/stderr and identity.json are preserved; no install or network probe followed. Runtime.json is absent and run authorization remains false; this preparation is partial, not verified executable.

Separate stdlib canonical inventory audit produced 769 full merge modules and 100 modules in Windows/Python3.11 shard0/8. The four canonical subshards have 20/33/33/32 modules, with shared modules: their union exactly equals the 100-module cell. Lists and counts are in inventory.json. Root must choose coverage and resolve runtime prerequisite before authorizing execution. Portable attempt remains unconsumed.

Only AST syntax check, archive preparation, failed runtime preflight and stdlib inventory reads ran. No tests, builds, package installation, FE campaign or Git mutation. Detailed state: preparation-handoff.json. No installed artifact byte-equivalence claim is made; changed README/build metadata would require separate artifact identity review.

## Isolated-runtime re-audit ready for root review

Root supplied runtime-env/Scripts/python.exe under the same stage with numba, pywin32, psutil and mpmath. Base qualification .venv remains unchanged; no worker package installs were performed. Re-audit receipt preflight-81946ac0.receipt.json passed with exact staged host import, adapter source origin, JIT enabled and one-thread actual numerical pools. Runtime/source/input identities and full 769-module canonical inventory are in runtime.json; a compact exact command/environment preview is ready-for-root-review.json. Prior missing-numba failure evidence remains preserved.

Root selected full unsharded 769-module coverage, two workers, 2400s inner and 2460s outer. execution_authorized=false and attempt_consumed=false still hold. No portable tests have run. Parent root must review and set explicit stage authorization before the exact outer command may launch. This source-overlay Windows3.11 claim does not replace other OS/Python cells, clean-checkout or installed metadata verification.

Final preparation additionally verifies all four sibling module origins against explicitly allowed read-only source roots. Latest preflight-5f8be5d9.receipt.json passes; ready-for-root-review.json and identity/runtime records carry final wrapper identity. No portable execution occurred.

## Terminal owned attempt: FAILED, no automatic retry

Root reviewed and authorized exactly one full769-module portable attempt. Canonical runner stopped P01 after P02 failed test_package_source_override_is_explicit_and_resolved: its source-snapshot helper needs separate Q1M sibling-root overrides; PYTHONPATH alone is insufficient. This staging environment omission was missed in preparation; no product defect is established. The unchanged CI configuration already documents the required Q1M overrides. No postfailure repair or rerun was performed.

Outer evidence: evidence/w1/platform-local-portable-2da6ea1ac8. Process wall821.6560000000027s, exit1, cleanup verified active0. Canonical wall820.8438796000119s. P02 reported240passed/1failed/9skipped/13deselected/27warnings; mandatory isolated partitions reported8+12+5passed, so known total265passed/1failed. P01 was stopped without terminal counts, and no prefix coverage is inferred. This is an incomplete, failed source-platform attempt, not full portable acceptance.

final-handoff.json records exact evidence/counts/failure and source/dirty-work preservation. Prospective wrapper repair is to set Q1M_ANYMATERIAL_ROOT, Q1M_ANYGEOMETRY_ROOT, Q1M_ANYMESH_ROOT and Q1M_ANYFILEIO_ROOT to the authorized current sibling roots. A full retry is not authorized; the registration remains consumed.
