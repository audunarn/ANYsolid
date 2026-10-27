# W1.5 all-solid repeated-load measurement

## Coupled follow-through

A separate reviewed measurement now covers the retained two-region/four-interface
research fixture: 828 primary coefficients and 60 multipliers. Batches
1/10/100/1,000 use a non-proportional two-load subspace (axial force plus bending
moment), with one host factorization reused for all 1,111 RHS. Both regions'
complete tensors are recovered for every RHS. One separate explicit reference
LU solves two basis RHS; this is discrete equivalence, not independent physics.

Receipt `evidence/w1/workflow1-coupled-loads-52683f83ef` completed in 14.047
process seconds. Independent source/evidence review supports the cache counts,
per-RHS checks and measurements. Maximum coefficient/tensor error is 7.29e-12
and work error 1.05e-13; physical support-only balance and existing registered
residual gates pass. Whole-process lifetime peak working set is 387,960,832
bytes, not factor storage or memory savings. Single-thread pools were verified.

The registration is consumed. No speedup ratio, broad load-space coverage,
independent elasticity accuracy, condensation benefit or production coupling
qualification is claimed. Condensation remains disabled. Raw phase timings,
source/input identities, all four batch maxima and memory snapshots are retained.

## Earlier all-solid measurement

One registered attempt completed in 5.125 seconds, with zero execution failures
and verified zero remaining owned processes. Receipt:
`evidence/w1/workflow1-repeated-load-592f7fc533`.

The workload has 1,275 P2 coefficients and 192 straight tetrahedra. One native
host factorization served batches of 1, 10, 100 and 1,000 RHS: 1,111 total.
A separate explicit reference LU solved three basis RHS; it is not counted as
the host factorization. Every RHS's full strain/stress tensors were recovered
and compared separately with those reference combinations.

| Batch RHS | Host total seconds | Incremental solve seconds | All-RHS recovery seconds | Cache hit |
| --- | ---: | ---: | ---: | --- |
| 1 | 0.0125053 | 0.0 | 0.0012734 | false |
| 10 | 0.0218996 | 0.0009997 | 0.0078620 | true |
| 100 | 0.1691705 | 0.0059998 | 0.0728532 | true |
| 1,000 | 1.9670945 | 0.0545807 | 1.0827583 | true |

Cold conversion/preparation/assembly were 0.0022858/0.0073167/0.0550462 seconds;
the warm operator copy took 0.0000936 seconds. Existing host factorization time
was 0.0053847 seconds. Its solver-phase timers have finite clock resolution;
the first reported solve increment of zero does not mean no computation.
Coupling assembly is inapplicable to this all-solid workload.

Maximum per-RHS errors were 3.584e-13 for coefficients, 2.214e-13 for strain,
2.199e-13 for stress and 1.343e-12 for energy/work. Prescribed-support reactions
plus external loads balance force/moment within 1.838e-13 of their registered
scales. The existing physical/local and normwise residual policy passed, with
maximum equilibrium error 6.987e-14. No tolerance or physical operator changed.

The stiffness CSR arrays use 894,940 bytes; 1,000 coefficient columns use
10,200,000 bytes. Whole-process lifetime peak working set was 489,439,232 bytes,
including preparation, references, result arrays, detailed residual reports
and recovery. This is not factor memory, a per-batch peak or measured savings.

Independent non-author evidence review supports these scoped measurements.
During execution the concurrently developed S3 trace changed from the outer
receipt's initial hash; it is unused by this all-solid workload. Later host
changes only admit/tag explicit strong diagnostic interfaces; they were not
part of this measurement. Exact receipt identities remain authoritative.
Do not rerun this consumed study to reconstruct source identity.

This establishes finite host reuse/recovery equivalence, not engineering
elasticity accuracy, coupled performance or a speedup ratio. No demonstrated
condensation benefit exists; condensation remains disabled. Coupled repeated
load qualification depends on the unresolved coupling gates.
