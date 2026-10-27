# ANYsolid

For fast local feedback and the complete adapter regression commands, see
[development testing](docs/DEVELOPMENT_TESTING.md). Start with
`python tools/dev_checks.py smoke`; use `full` before an adapter handoff.

A small adapter for three-dimensional small-strain isotropic elasticity. The
numerical backend uses scikit-fem's vector tetrahedral P1/P2 spaces, quadrature,
linear elasticity assembly, physical interpolation and tensor operations.

Install with `python -m pip install ".[skfem]"` from the repository, or
`python -m pip install "ANYsolid[skfem]"` from a package index. Importing
`anysolid` itself is lazy. Preparing a region requires NumPy, SciPy and
scikit-fem, supplied by the optional `skfem` extra; there is no automatic
dependency installation or backend fallback. The base package requires NumPy
and SciPy only.

```python
from anysolid import SolidMesh, prepare

mesh = SolidMesh(
    coordinates=[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]],
    cells=[[0, 1, 2, 3]],
)
solid = prepare(mesh, {"elastic_modulus": 200e9, "poisson_ratio": .3}, order=2)
K = solid.assemble_linear()  # scipy CSR; free-body stiffness has rigid modes
```

Use SI units: coordinates in metres, elastic modulus in pascals, body force
density in N/m³, traction and pressure in N/m². Positive pressure acts inward.
Groups contain external IDs; connectivity contains zero-based coordinate rows.

See [backend contract](docs/backend.md) and the executable
[tetrahedron example](examples/linear_tetrahedron.py). Run the focused backend
checks with `python -m pytest -q tests/test_backend.py`.

The supported backend envelope is positive-orientation straight tet4 geometry,
P1/P2 displacement spaces, finite E > 0 and 0 ≤ nu ≤ 0.45. C3D10/curved geometry,
nonlinear mechanics, dynamics and contact are unsupported. Analytical patch
checks do not establish engineering convergence or production weak coupling.

The ANYsolver integration now provides an explicit `SolidModel` wrapper and
single/multiple-RHS dispatch. See [host example](examples/host_all_solid.py).
The planar Q4 weak connector is **research-only / production NO_GO**. The
approved registered local/normwise residual checks, membrane, bending and
three physical patches pass. The original coarse transverse comparison failed
its fixed shear criterion. Later registered axial-refined cases meet it
(4.56% at Nx16 and 1.41% at Nx32, versus 5%) without operator or tolerance
changes. Arbitrary-mesh accuracy, stability and wider convergence remain
unqualified. See
[candidate theory](docs/shell_solid_theory.md) and
[workflow handoff](docs/WORKFLOW_1_HANDOFF.md) for the actual evidence and gaps.

The revised multiplier passed all 18 registered finite stability assessments
and 12 fresh physical cases. The earlier Candidate A failure remains preserved.
Production remains **NO_GO** pending the remaining Workflow 1 gates; see
[revised results and limits](docs/REVISED_MULTIPLIER_RESULTS.md).
