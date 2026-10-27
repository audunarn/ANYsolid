# Numerical backend contract

`anysolid` lazily exports `SolidMesh`, `PreparedSolid`, `Recovery`, `prepare`.
No ANYmesher, ANYgeometry or ANYsolver imports occur in the backend. Numerical
dependencies are loaded on first access to a numerical class or operation.
Importing `prepare` is also lazy. scikit-fem is optional through the `skfem`
extra; preparation without it reports `python -m pip install "ANYsolid[skfem]"`.

## Input snapshot

`SolidMesh(coordinates, cells, node_ids=None, cell_ids=None,
boundary_facets=None, boundary_ids=None, node_groups=None, cell_groups=None,
boundary_groups=None, *, units='m', geometry_order=1, provenance=None)` takes
owned copies. Arrays are backed by immutable bytes, mappings are read-only,
and nested finite JSON provenance is frozen. `prepare` also consumes a
structural object exposing all these named attributes; missing attributes are
an error. A `SolidMesh` already satisfies the immutable contract and is reused.

Coordinates have shape `(N,3)` and connectivity `(M,4)` uses coordinate row
indices. Each cell must have distinct vertices, positive orientation and a
determinant greater than `64*eps*max_edge_from_first_vertex**3`. Duplicate cells,
duplicate coordinates, unused coordinates, nonfinite inputs, and facets with
more than two incident cells are rejected. This is local and topological
validation; it does not certify global intersection-free conforming geometry.
Callers remain responsible for that geometric property.

Node/cell/boundary IDs are unique int64 identifiers, defaulting to zero-based
rows. Named groups contain unique external IDs of the appropriate type. Empty
groups are allowed. Supplied boundary facets `(F,3)` must be distinct exterior
faces with outward vertex winding; a subset is allowed. Inward winding is
rejected, preserving explicit orientation semantics. If omitted, all exterior
faces are generated with outward winding using their owning cell's opposite
vertex, ordered lexicographically by their sorted-vertex keys. The stored
cross-product normal is outward and boundary IDs default to face rows.
Only `units='m'`, `geometry_order=1` are accepted. C3D10 connectivity is explicitly
unsupported; there is no unverified conversion or permutation.

## Preparation and assembly

`prepare(mesh, material, *, order=2)` accepts order 1 or 2 and material mapping
keys or attributes `elastic_modulus`, `poisson_ratio`. Constants must be finite
scalars with E > 0 and 0 ≤ nu ≤ 0.45. The material is snapshotted into scalar
values. The prepared object's public state is immutable; prepare a fresh region
to change inputs. `ndof` is the upstream vector-space coefficient count.

`assemble_linear()` returns a fresh SciPy CSR copy of the cached unconstrained
stiffness. Essential constraints and solution belong to the host. Upstream
`linear_elasticity` uses isotropic Lamé parameters; no element shape functions,
quadrature or constitutive element kernels are implemented locally. P2 uses
`ElementVector(ElementTetP2())` over the straight tet4 geometry. Integration
order is twice the displacement order.

`coefficient_coordinates` `(ndof,3)` and `coefficient_components` `(ndof,)`
describe each coefficient in physical xyz, with component 0, 1 or 2. Components
come from upstream `Basis.split_indices()`, not an assumed host node stride.

`rigid_modes()` returns an immutable `(ndof,6*ncomponents)` matrix with three
translations followed by three rotations per vertex-connected mesh component.
Rotations are centered at that component's vertex centroid and scaled by its
maximum vertex radius. Membership follows connectivity and upstream
`Basis.element_dofs`, including P2 edges; spatial proximity never joins parts.
The host may inspect support/constraint action on these modes to diagnose
unrestrained free parts. Point/edge-connected pathological meshes can have
additional mechanisms, so this physical rigid subspace is not a complete
stiffness-nullspace certificate.

`boundary_dofs(group, components=(0,1,2))` returns sorted coefficient indices.
Boundary groups select every face DOF, including P2 edge coefficients. Node
groups select only coefficients at explicitly named mesh vertices. If both
types have the same name, the boundary group takes precedence. Cell groups are
retained metadata and do not select boundary DOFs.

## Loads and physical traces

`body_load(vector)` integrates a constant physical force per volume.
`traction(group,vector, *, gradient=None, origin=(0,0,0))` integrates a physical
force per area. Its default is constant; a finite `(3,3)` gradient supplies
`vector + gradient @ (x-origin)` at upstream facet quadrature coordinates.
The origin must be a finite physical `(3,)` vector. This permits affine stress
tractions such as the exact nu=0 pure-bending end load `t=(E*a*z,0,0)`.
`pressure(group,value)` integrates `-value * outward_normal`, so positive
pressure is compressive. Surface operations require boundary groups. Vector
inputs have shape `(3,)`; results have shape `(ndof,)`. These are consistent
upstream linear-form integrals, including the signed P2 basis contributions.

`trace(points)` accepts finite physical coordinates `(N,3)` inside or on the
solid and returns CSR `(3*N,ndof)` in point-major xyz order. Upstream probes
find elements and evaluate the basis; their component-major rows are reordered
explicitly. Exterior points are rejected, with no nearest-point projection or
extrapolation. `trace(points).T` therefore transfers physical point forces
using exactly the same interpolation operator and preserves discrete work.

## Recovery and identity

`recover(coefficients)` returns frozen `Recovery`:

| Field | Shape / meaning |
| --- | --- |
| `strain` | `(ncells,nquadrature,3,3)` physical small-strain tensor |
| `stress` | `(ncells,nquadrature,3,3)` Cauchy stress in Pa |
| `coordinates` | `(ncells,nquadrature,3)` physical sampling points |
| `weights` | `(ncells,nquadrature)` physical integration weights |
| `cell_ids` | `(ncells,)` original external cell identifiers |
| `sampling` | `element_quadrature` |
| `tensor_convention` | `physical_tensor` |

Shear strain entries are tensor strains (half engineering shear). Recovery
uses upstream `sym_grad` and `linear_stress`; it does not smooth nodal stresses
or project between elements. Quadrature points/weights belong to the selected
upstream integration rule; consumers should use the weights explicitly.

`cache_signature()` is a deterministic SHA-256 of snapshot arrays, group names
and IDs, provenance, material, displacement/geometry orders, units, backend
version and schema. It identifies the supplied discrete content, not a
geometry equivalence class. Callers cannot mutate source inputs to change an
existing signature or cached assembly.

## Verification boundary

The focused analytical cases cover both orders, nu=0/.3/.45, full affine
stress/strain/energy including shear, six rigid modes per disconnected region,
symmetry, force/moment/work of consistent loads, quadratic P2 interpolation and
strain, connected cube traction equilibrium and constrained affine solve,
snapshot mutation, lazy imports and explicit refusal paths. The registered
relative patch/resultant/rigid thresholds are 1e-10 with documented physical
scales for zero-reference quantities. These bounded checks do not establish
engineering bending convergence, global mesh validity, near-incompressibility,
or production coupling acceptance. Backend authored tests require parent
inspection and independent review before final acceptance.
