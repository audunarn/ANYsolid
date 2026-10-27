# Repaired connected beam verification

The fresh connected beam/shell/solid verification passed. The previous attempt
and its material-lookup failure remain unchanged and consumed.

The new harness calls `native.get_material(beam.material_name)` instead of the
nonexistent mesh material mapping. It also saves the solved matrices, actual
coefficients, loads and reactions before physical postprocessing. Geometry,
physical references, loads, supports, normalization and every numerical limit
are unchanged. Native numbering and both rebuilt physical interface traces are
checked.

Command, from ANYsolid:

```console
.venv/Scripts/python.exe tools/run_check.py --name workflow1-connected-beam-repaired --timeout 60 -- python tools/connected_beam_repaired_study.py
```

Evidence: `evidence/w1/workflow1-connected-beam-repaired-a9a7736716`.
Process wall time 2.219 seconds; exit zero; verified zero remaining processes.
Both 197-by-197 KKT certificates and both axial/bending physical cases pass.
The host used one factorization for two RHS. All 12 physical checks pass in
each case, including whole-solid coefficient fields, all stress components in
the fixed ROI, reactions, interface work, beam end actions and residuals.
Maximum field error is approximately 2.18e-11, stress error 1.31e-11 and
beam-action error 1.56e-12 under their registered normalizations.

The source SHA-256 is
`0b66f9c92d6dc52a3df38f2ceec3eeb839a1565db29f51d6d4c5983425c0ae71`.
An independent non-author reviewer checked source/input identities, both
single-thread BLAS pools, counts and every gate. Review used the same model
family. The reviewed manifest state changed only from pending to ready before
execution. See `connected_beam_repaired_disposition.json`.

The registration is consumed. This accepts an idealized shared-native-node FE
patch, not resolved continuum joint stress, transition-distance behavior or a
platform matrix. The old failure is in `connected_beam_disposition.json` and
`evidence/w1/workflow1-connected-beam-d8b983a20d`; neither was rewritten.
