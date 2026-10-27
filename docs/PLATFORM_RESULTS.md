# Local platform verification

All eight adapter owner-platform cells passed. These are local source snapshots,
not clean committed checkouts, remote CI or full ANYsolver qualification.

| OS | Actual Python | Tests passed | Failures/errors/skips |
| --- | --- | ---: | --- |
| Windows | 3.11.9 | 194 | 0/0/0 |
| Windows | 3.12.13 | 194 | 0/0/0 |
| Windows | 3.13.9 | 194 | 0/0/0 |
| Windows | 3.14.2 | 194 | 0/0/0 |
| Ubuntu 24.04 | 3.11.15 | 195 | 0/0/0 |
| Ubuntu 24.04 | 3.12.3 | 195 | 0/0/0 |
| Ubuntu 24.04 | 3.13.12 | 195 | 0/0/0 |
| Ubuntu 24.04 | 3.14.3 | 195 | 0/0/0 |

Every cell also built a wheel and sdist, installed its wheel, passed the isolated
public P2 smoke and dependency check. All 48 successful phase receipts have
verified process cleanup. There are 1,556 passing tests across the successful
cells; failed historical attempts are retained separately, not added to this
count or rewritten as passes.

Aggregate evidence:
`evidence/w1/adapter-platform-20261027T124413Z-f423d33f/final-report.json`.
The matrix ledger records 77.914697 process seconds; post-matrix focused tooling
checks bring the owned total to 88.439662 seconds of the 1,200-second budget.
The checkpoint records exact commands, all runtime/source/artifact hashes,
per-phase times and earlier failed attempts.

Windows results were retained from their completed 194-test snapshot. The Linux
snapshot added one temporary-workspace regression, with identical product and
build inputs. Later driver-lookup and full-profile inventory changes were tested
separately: 19 focused checks passed on Windows and 19 on Linux. The final current
development profile passed 331 tests, zero failures/errors/skips, in 43.3643615
process seconds:

```console
.venv/Scripts/python.exe tools/dev_checks.py full --timeout 180
```

Receipt: `evidence/development/20261027T125640Z-901c9157`. Parent review confirmed
that current adapter product, packaging and CI build-input bytes equal the tested
matrix inputs. This is impact-based reuse, not a claim that later tooling files
were present in every previous snapshot.

## Repairs retained in evidence

The matrix exposed a runtime/log-directory collision, an absolute-path assertion
that confused checkout ancestors with test targets, Linux managed-interpreter
aliases, and DrvFS cache/temporary-file behavior. The harness now uses distinct
phase directories, relative selected-target checks, physical interpreter identity
and native Linux temporary workspaces. Capture was not disabled and tests were
not filtered. Linux child sessions and Windows Job Objects are supervised
separately. All original failures remain available in the checkpoint lineage.

## Host integration remains blocked

The separate 769-module host portable inventory did not pass. The first attempt
omitted the CI's explicit Q1M sibling roots; its repaired continuation surfaced
a constructor-policy inventory mismatch and a failing default verification
report. The closed-world policy inventory was corrected without changing solver
admission or numerical checks; its focused check and current full profile pass.

The captured default report has 126 PASS, 2 FAIL and 2 XFAIL. Required case
`NLG-007` and derived `NLG-003` encounter the unchanged refusal of warped plastic
qualified-Q4 behavior. This is outside the linear Workflow 1 implementation.
Required status, physical guard and expected verification result remain unchanged;
no legacy fallback was used. Evidence:
`evidence/w1/beam-report-diagnostic-917765cabb/final-handoff.json`.

The host's 2,400-second process budget used 1,810.748880 seconds, with 589.251120
unused after diagnosis and focused policy repair. No third full run was attempted.
Neither a failed portable run nor a focused repair establishes full host CI.
Clean-checkout/remote CI and the failed transition reference gate remain open.
No commit, push, merge or publication was performed.
