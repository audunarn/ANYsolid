# Backend implementation checkpoint

2026-10-26: source scaffold did not exist. Environment inspected: scikit-fem
12.0.2. Upstream `Basis.split_indices()` supplies physical vector components;
`Basis.probes` uses component-major physical rows, so trace will reorder these
to point-major xyz. Upstream interpolation supplies displacement gradients and
quadrature coordinates/weights for tensor recovery. No native element kernels.

Frozen API: `prepare(mesh, material, order=2)`; prepared `ndof`,
`coefficient_coordinates`, `coefficient_components`, `assemble_linear`,
`boundary_dofs`, `body_load`, `traction`, `pressure`, `trace`, `recover`,
`cache_signature`. `SolidMesh` accepts coordinates, cells, node_ids, cell_ids,
boundary_facets, boundary_ids, node_groups, cell_groups, boundary_groups,
units, geometry_order, provenance. Groups identify external entity IDs.

Recovery fields: strain/stress `(ncells,nquadrature,3,3)`, coordinates
`(ncells,nquadrature,3)`, weights `(ncells,nquadrature)`, cell_ids `(ncells,)`,
sampling=`element_quadrature`, tensor_convention=`physical_tensor`.

Plan and acceptance:
1. Immutable validated tet4 snapshot and lazy package: malformed and mutation
   paths rejected; package imports without numerical dependencies loaded.
2. Upstream vector P1/P2 assembly, loads, probes, recovery: affine tensor patch,
   six rigid modes, symmetry, work and analytical resultants within 1e-10.
3. Focused refusal/integration tests, example and docs: bounded backend pytest.

Remaining: implementation and verification. C3D10 is initially unsupported;
straight C3D10 may be added only with verified ordering. No engineering
convergence qualification is registered, and no broad campaign will run.
No blockers. Host/coupling ownership remains with parent.

## Implemented handoff

Backend complete against assigned analytical criteria. Added immutable
`rigid_modes()` with six physical modes per connectivity component; DOF
membership comes from upstream element ownership, including P2 edges.
Read-only prepared state protects caches against public attribute replacement.

Files authored: `src/anysolid/{__init__,mesh,backend}.py`, `pyproject.toml`,
`tests/test_backend.py`, `tests/conftest.py`,
`examples/linear_tetrahedron.py`, `README.md`, `docs/backend.md`, this checkpoint.
Parent-owned coupling/host sources and tests were not edited. Existing
`.gitignore`, project docs, verification manifest and parent additions retained.

Verification performed:

- `.venv/Scripts/python.exe -m pytest -q tests/test_backend.py`: first run
  54 passed / 1 failed because the lazy-import child lacked `PYTHONPATH`.
  Fixed the test child environment; no numerical failure was observed.
- Subsequent expanded runs passed: 55, 59, 60 and 61 cases respectively.
  Final run after robust scale-normalized geometry validation: 61 passed
  in 0.66 s pytest time (not process-wall accounting).
- `.venv/Scripts/python.exe -m compileall -q src`: exit 0.
- `PYTHONPATH=src .venv/Scripts/python.exe examples/linear_tetrahedron.py`:
  exit 0; free-equilibrium norm 2.800403880926209e-12 N; tip displacement
  [-1.51536595e-7, -1.51536595e-7, -1.64741029e-7] m.

Checks are small analytical tests, not resource-bounded performance cases.
Raw command output is retained in the agent tool transcript; parent owns
additional evidence logs. Final parent inspection and independent review
remain required. No Git integration or installed-artifact verification was
performed by this worker. No license was invented: repository license choice
is outside this numerical assignment's established contract.

Limits: C3D10/curved geometry explicitly rejected; no engineering convergence
or general coupling acceptance; no global self-intersection certification.
Physical rigid modes do not cover extra mechanisms of point/edge-connected
pathological meshes. See backend contract for node-group versus face-group
P2 support semantics.

## Review repair: outward facets and optional backend

Parent review identified that sorted auto-facet vertex rows did not encode
outward normals. Auto faces now use the owning cell/opposite vertex to choose
outward winding. Explicit inward rows are rejected rather than rewritten.
Fixtures/example use outward winding. Added every-face outward tests on one
and two cells, rejection of each reversed tetrahedron face, cyclic orientation
preservation, and pressure agreement with stored normals for P1/P2.

Distribution name is `ANYsolid` at 0.1.0. Base dependencies are NumPy/SciPy;
scikit-fem belongs to optional `[skfem]`. Importing `prepare` remains lazy, and
simulated missing-backend execution verifies actionable installation guidance.
No host/coupling source or tests were edited during this repair.

Repair verification: `.venv/Scripts/python.exe -m pytest -q
tests/test_backend.py` passed 70 tests (1.04 s pytest time). Compileall and
the tetrahedron example passed again; example equilibrium residual unchanged
at 2.800403880926209e-12 N. Independent parent review/acceptance remains open.

## Authorized affine traction extension

Added optional `gradient`/`origin` to `traction` using upstream facet physical
quadrature coordinates. Constant API is unchanged. Added finite-shape refusal
tests, analytical triangular resultant/moment/work for `t=(slope*z,0,0)`, and
a connected P2 rectangular-block solve for exact nu=0 pure bending
`u=(a*x*z,0,-a*x*x/2)` with zero clamp displacement and affine end traction.
Parent owns the independent qualification/convergence harness.

Extension verification: `.venv/Scripts/python.exe -m pytest -q
tests/test_backend.py` passed 77 tests (1.12 s pytest time), including all
previous regressions. No failure occurred in this extension's test run.
