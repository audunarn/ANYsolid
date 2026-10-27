"""Small analytical qualification cases, no engineering convergence claim."""
import dataclasses
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from scipy.sparse import isspmatrix_csr
from anysolid import SolidMesh, prepare


X = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
T = np.array([[0, 1, 2, 3]])
MATERIAL = {'elastic_modulus': 1000., 'poisson_ratio': .3}


def mesh(**kwargs):
    args = dict(coordinates=X, cells=T, node_ids=[10, 20, 30, 40], cell_ids=[100],
                boundary_facets=[[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]],
                boundary_ids=[50, 60, 70, 80],
                boundary_groups={'base': [50], 'all': [50, 60, 70, 80], 'empty': []},
                node_groups={'tip': [40]}, cell_groups={'bulk': [100]},
                provenance={'source': 'analytical tetra', 'nested': {'labels': ['one']}})
    args.update(kwargs)
    return SolidMesh(**args)


def affine(p, gradient, shift=np.zeros(3)):
    return (p.coefficient_coordinates @ gradient.T + shift)[np.arange(p.ndof), p.coefficient_components]


@pytest.mark.parametrize('order', [1, 2])
@pytest.mark.parametrize('nu', [0., .3, .45])
def test_affine_patch_full_tensor_energy(order, nu):
    p = prepare(mesh(), dict(elastic_modulus=1000., poisson_ratio=nu), order=order)
    # Nonzero diagonal, engineering shear, and skew rotation contributions.
    g = np.array([[.03, .08, -.02], [.04, -.01, .05], [.02, -.03, .06]])
    a = affine(p, g, [.1, -.2, .3])
    r = p.recover(a)
    eps = (g + g.T) / 2
    mu = 1000 / (2 * (1 + nu))
    lam = 1000 * nu / ((1 + nu) * (1 - 2 * nu))
    stress = 2 * mu * eps + lam * np.trace(eps) * np.eye(3)
    np.testing.assert_allclose(r.strain, np.broadcast_to(eps, r.strain.shape), atol=1e-13, rtol=1e-10)
    np.testing.assert_allclose(r.stress, np.broadcast_to(stress, r.stress.shape), atol=1e-10, rtol=1e-10)
    k = p.assemble_linear()
    assert isspmatrix_csr(k)
    np.testing.assert_allclose(k.toarray(), k.T.toarray(), atol=1e-11)
    np.testing.assert_allclose(a @ k @ a, np.sum(stress * eps) / 6, rtol=1e-10)
    np.testing.assert_allclose(r.weights.sum(), 1 / 6, rtol=1e-13)
    assert r.coordinates.shape == (*r.weights.shape, 3)
    assert r.tensor_convention == 'physical_tensor'
    assert r.sampling == 'element_quadrature'
    np.testing.assert_array_equal(r.cell_ids, [100])


@pytest.mark.parametrize('order', [1, 2])
def test_six_rigid_modes(order):
    p = prepare(mesh(), MATERIAL, order=order)
    k = p.assemble_linear()
    for c in range(3):
        u = (p.coefficient_components == c).astype(float)
        assert np.linalg.norm(k @ u) / (1000 / 6) < 1e-10
        axis = np.eye(3)[c]
        values = np.cross(axis, p.coefficient_coordinates)
        a = values[np.arange(p.ndof), p.coefficient_components]
        assert np.linalg.norm(k @ a) / (1000 / 6) < 1e-10
    assert np.count_nonzero(np.linalg.eigvalsh(k.toarray()) < 1e-9) == 6


@pytest.mark.parametrize('order', [1, 2])
def test_load_resultants_moments_and_virtual_work(order):
    p = prepare(mesh(), MATERIAL, order=order)
    g = np.array([[.03, .08, -.02], [.04, -.01, .05], [.02, -.03, .06]])
    shift = np.array([.1, -.2, .3])
    a = affine(p, g, shift)
    force = np.array([2., -3., 5.])
    cases = [(p.body_load(force), force / 6, np.array([.25, .25, .25])),
             (p.traction('base', force), force / 2, np.array([1 / 3, 1 / 3, 0.])),
             (p.pressure('base', 7.), np.array([0., 0., 3.5]), np.array([1 / 3, 1 / 3, 0.]))]
    for f, resultant, centroid in cases:
        found = np.bincount(p.coefficient_components, weights=f, minlength=3)
        np.testing.assert_allclose(found, resultant, atol=1e-13, rtol=1e-10)
        nodal_forces = np.zeros((p.ndof, 3))
        nodal_forces[np.arange(p.ndof), p.coefficient_components] = f
        moment = np.cross(p.coefficient_coordinates, nodal_forces).sum(axis=0)
        np.testing.assert_allclose(moment, np.cross(centroid, resultant), atol=1e-13, rtol=1e-10)
        np.testing.assert_allclose(a @ f, (g @ centroid + shift) @ resultant, atol=1e-13)
    np.testing.assert_allclose(np.bincount(p.coefficient_components, weights=p.pressure('all', 5.), minlength=3), 0., atol=1e-13)
    np.testing.assert_array_equal(p.traction('empty', force), np.zeros(p.ndof))


@pytest.mark.parametrize('order', [1, 2])
def test_trace_point_major_and_transpose_work(order):
    p = prepare(mesh(), MATERIAL, order=order)
    points = np.array([[.1, .2, .3], [0., 0., 0.], [.2, .3, .1], [0., .4, .6]])
    g = np.array([[.03, .08, -.02], [.04, -.01, .05], [.02, -.03, .06]])
    shift = np.array([.1, -.2, .3])
    a = affine(p, g, shift)
    trace = p.trace(points)
    assert isspmatrix_csr(trace)
    np.testing.assert_allclose(trace @ a, (points @ g.T + shift).ravel(), rtol=1e-12, atol=1e-13)
    f = np.arange(12.)
    np.testing.assert_allclose((trace @ a) @ f, a @ (trace.T @ f), atol=1e-13)
    assert p.trace(np.empty((0, 3))).shape == (0, p.ndof)
    with pytest.raises(ValueError, match='inside'):
        p.trace([[2., 2., 2.]])


def test_p2_recovery_linear_strain_and_quadratic_trace():
    p = prepare(mesh(), MATERIAL)
    x = p.coefficient_coordinates
    values = np.column_stack([x[:, 0]**2, x[:, 1] * x[:, 2], x[:, 2]**2])
    a = values[np.arange(p.ndof), p.coefficient_components]
    points = np.array([[.1, .2, .3], [.2, .1, .4]])
    expected = np.column_stack([points[:, 0]**2, points[:, 1] * points[:, 2], points[:, 2]**2])
    np.testing.assert_allclose((p.trace(points) @ a).reshape(-1, 3), expected, atol=1e-14)
    r = p.recover(a)
    expected_strain = np.zeros_like(r.strain)
    expected_strain[..., 0, 0] = 2 * r.coordinates[..., 0]
    expected_strain[..., 1, 1] = r.coordinates[..., 2]
    expected_strain[..., 2, 2] = 2 * r.coordinates[..., 2]
    expected_strain[..., 1, 2] = expected_strain[..., 2, 1] = r.coordinates[..., 1] / 2
    np.testing.assert_allclose(r.strain, expected_strain, atol=1e-13)


@pytest.mark.parametrize('order,count', [(1, 9), (2, 18)])
def test_boundary_dofs_use_external_ids_and_physical_components(order, count):
    p = prepare(mesh(), MATERIAL, order=order)
    dofs = p.boundary_dofs('base')
    assert len(dofs) == count
    np.testing.assert_allclose(p.coefficient_coordinates[dofs, 2], 0.)
    y = p.boundary_dofs('base', (1,))
    assert len(y) == count // 3
    assert np.all(p.coefficient_components[y] == 1)
    assert len(p.boundary_dofs('tip')) == 3
    assert not len(p.boundary_dofs('base', ()))
    assert not len(p.boundary_dofs('empty'))


def test_snapshot_prevents_input_and_return_mutation():
    x, t = X.copy(), T.copy()
    groups = {'base': [50]}
    provenance = {'nested': ['first']}
    m = mesh(coordinates=x, cells=t, boundary_groups=groups, provenance=provenance)
    p = prepare(m, MATERIAL)
    before = p.cache_signature()
    k = p.assemble_linear()
    x[:] = 99
    t[:] = 0
    groups['base'].append(60)
    provenance['nested'].append('second')
    assert p.cache_signature() == before
    for a in (m.coordinates, m.cells, m.boundary_groups['base'], p.coefficient_coordinates,
              p.coefficient_components, p.recover(p.body_load([0, 0, 0])).strain):
        with pytest.raises(ValueError):
            a.setflags(write=True)
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.units = 'mm'
    with pytest.raises(TypeError):
        m.provenance['new'] = 1
    k.data[:] = 0
    assert p.assemble_linear().nnz > 0
    assert np.linalg.norm(p.assemble_linear().data) > 0
    with pytest.raises(AttributeError):
        p.order = 1
    with pytest.raises(AttributeError):
        p.coefficient_coordinates = np.zeros_like(p.coefficient_coordinates)


def test_signature_tracks_inputs_and_structural_protocol():
    m = mesh()
    p = prepare(m, MATERIAL)
    structural = SimpleNamespace(**{f.name: getattr(m, f.name) for f in dataclasses.fields(m)})
    assert prepare(structural, MATERIAL).cache_signature() == p.cache_signature()
    assert prepare(m, dict(elastic_modulus=1001., poisson_ratio=.3)).cache_signature() != p.cache_signature()
    assert prepare(m, MATERIAL, order=1).cache_signature() != p.cache_signature()
    assert prepare(mesh(boundary_groups={'only': [50]}), MATERIAL).cache_signature() != p.cache_signature()
    assert prepare(mesh(provenance={'source': 'changed'}), MATERIAL).cache_signature() != p.cache_signature()


@pytest.mark.parametrize('changes', [
    {'cells': [[0, 2, 1, 3]]}, {'cells': [[0, 1, 2, 2]]},
    {'cells': [[0, 1, 2, 4]]}, {'cells': [[0., 1., 2., 3.]]},
    {'cells': np.zeros((1, 10), dtype=int)}, {'cells': np.vstack([T, T])},
    {'coordinates': X * np.array([1., 1., 0.])},
    {'coordinates': X * np.nan}, {'coordinates': np.vstack([X, [[2., 2., 2.]]])},
    {'node_ids': [10, 10, 30, 40]}, {'node_ids': [10., 20., 30., 40.]},
    {'cell_ids': [100, 200]}, {'boundary_ids': [50, 50, 70, 80]},
    {'boundary_groups': {'bad': [0]}}, {'node_groups': {'bad': [0]}},
    {'cell_groups': {'bad': [0]}}, {'node_groups': {'bad': [10, 10]}},
    {'boundary_facets': [[0, 1, 1]]}, {'boundary_facets': [[0, 1, 2], [2, 1, 0]]},
    {'units': 'mm'}, {'geometry_order': 2}, {'provenance': {'bad': np.nan}},
])
def test_mesh_refusal(changes):
    with pytest.raises(ValueError):
        mesh(**changes)


@pytest.mark.parametrize('material', [
    {'elastic_modulus': 0., 'poisson_ratio': .3},
    {'elastic_modulus': -1., 'poisson_ratio': .3},
    {'elastic_modulus': np.inf, 'poisson_ratio': .3},
    {'elastic_modulus': 1000., 'poisson_ratio': -.1},
    {'elastic_modulus': 1000., 'poisson_ratio': .46},
    {'elastic_modulus': 1000., 'poisson_ratio': np.nan},
    {'elastic_modulus': [1000.], 'poisson_ratio': .3},
    {'E': 1000., 'nu': .3}, {'elastic_modulus': True, 'poisson_ratio': .3},
])
def test_material_refusal(material):
    with pytest.raises(ValueError):
        prepare(mesh(), material)


@pytest.mark.parametrize('order', [0, 3, True, '2'])
def test_order_refusal(order):
    with pytest.raises(ValueError):
        prepare(mesh(), MATERIAL, order=order)


def test_call_refusal():
    p = prepare(mesh(), MATERIAL)
    for bad in ([1, 2], [1, 2, np.nan]):
        with pytest.raises(ValueError):
            p.body_load(bad)
        with pytest.raises(ValueError):
            p.traction('base', bad)
    for components in ((3,), (0, 0), (True,), (1.,)):
        with pytest.raises(ValueError):
            p.boundary_dofs('base', components)
    for action in (lambda: p.traction('unknown', [1, 2, 3]),
                   lambda: p.pressure('base', np.nan),
                   lambda: p.pressure('base', [1, 2]),
                   lambda: p.trace([[np.nan, 0, 0]]),
                   lambda: p.recover(np.zeros(p.ndof + 1)),
                   lambda: p.recover(np.full(p.ndof, np.nan))):
        with pytest.raises(ValueError):
            action()


def test_import_is_lazy_and_has_no_sibling_imports():
    code = "import anysolid,sys; assert not {'numpy','scipy','skfem','anysolver','anymesher','anygeometry'} & sys.modules.keys()"
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
    subprocess.run([sys.executable, '-c', code], check=True, timeout=10, env=env)


def test_two_cell_shared_face_and_internal_facet_refusal():
    x = np.vstack([X, [[0., 0., -1.]]])
    t = np.array([[0, 1, 2, 3], [0, 2, 1, 4]])
    m = SolidMesh(x, t)
    assert len(m.boundary_facets) == 6
    for order in (1, 2):
        p = prepare(m, MATERIAL, order=order)
        a = affine(p, np.eye(3))
        r = p.recover(a)
        np.testing.assert_allclose(r.strain, np.broadcast_to(np.eye(3), r.strain.shape), atol=1e-13)
        np.testing.assert_allclose(r.weights.sum(), 1 / 3, rtol=1e-13)
    with pytest.raises(ValueError, match='exterior'):
        SolidMesh(x, t, boundary_facets=[[0, 1, 2]])


@pytest.mark.parametrize('order', [1, 2])
def test_connected_cube_affine_equilibrium_with_all_surface_tractions(order):
    # Upstream creates mesh geometry too; reorient input cells to our explicit
    # positive-orientation contract, without relying on generic DOF strides.
    from skfem import MeshTet
    raw = MeshTet.init_tensor(np.linspace(0., 1., 3), np.linspace(0., 1., 3), np.linspace(0., 1., 3))
    x, t = raw.p.T.copy(), raw.t.T.copy()
    negative = np.linalg.det(x[t[:, 1:]] - x[t[:, :1]]) < 0
    t[negative, :2] = t[negative, 1::-1]
    initial = SolidMesh(x, t)
    facets = initial.boundary_facets
    groups = {}
    for axis in range(3):
        for side in (0, 1):
            groups[f'{axis}:{side}'] = initial.boundary_ids[np.all(x[facets, axis] == side, axis=1)]
    p = prepare(SolidMesh(x, t, boundary_groups=groups), MATERIAL, order=order)
    g = np.array([[.03, .08, -.02], [.04, -.01, .05], [.02, -.03, .06]])
    eps = (g + g.T) / 2
    E, nu = MATERIAL.values()
    stress = E / (1 + nu) * eps + E * nu / ((1 + nu) * (1 - 2 * nu)) * np.trace(eps) * np.eye(3)
    surface = np.zeros(p.ndof)
    for axis in range(3):
        for side in (0, 1):
            surface += p.traction(f'{axis}:{side}', stress[:, axis] * (2 * side - 1))
    a = affine(p, g, [.1, -.2, .3])
    assert np.linalg.norm(p.assemble_linear() @ a - surface) / (E * np.linalg.norm(g)) < 1e-10
    # A prescribed displacement solve exercises assembly and recovered fields
    # through a connected interior rather than only one free tetrahedron.
    constrained = np.unique(np.concatenate([p.boundary_dofs(group) for group in groups]))
    free = np.setdiff1d(np.arange(p.ndof), constrained)
    from scipy.sparse.linalg import spsolve
    k = p.assemble_linear()
    solved = a.copy()
    solved[free] = spsolve(k[free][:, free], surface[free] - k[free][:, constrained] @ a[constrained])
    np.testing.assert_allclose(solved, a, rtol=1e-10, atol=1e-13)
    r = p.recover(solved)
    np.testing.assert_allclose(r.strain, np.broadcast_to(eps, r.strain.shape), rtol=1e-10, atol=1e-12)


@pytest.mark.parametrize('order', [1, 2])
def test_each_disconnected_component_has_six_rigid_modes(order):
    m = SolidMesh(np.vstack([X, X + [3., 0., 0.]]), np.vstack([T, T + 4]))
    p = prepare(m, MATERIAL, order=order)
    eigenvalues = np.linalg.eigvalsh(p.assemble_linear().toarray())
    assert np.count_nonzero(np.abs(eigenvalues) < 1e-9) == 12
    modes = p.rigid_modes()
    assert modes.shape == (p.ndof, 12)
    assert np.linalg.matrix_rank(modes) == 12
    assert np.linalg.norm(p.assemble_linear() @ modes) / (1000 / 6) < 1e-10
    with pytest.raises(ValueError):
        modes.setflags(write=True)
    # Exactly disjoint DOF support follows vertex connectivity and upstream
    # element maps, including all P2 edge coefficients.
    assert not np.any(np.any(modes[:, :6] != 0, axis=1) & np.any(modes[:, 6:] != 0, axis=1))


def test_rigid_mode_topology_is_not_coordinate_proximity():
    # Very close but noncoincident disconnected tets must remain distinct.
    tiny = X * 1e-9
    p = prepare(SolidMesh(np.vstack([tiny, tiny + [2e-9, 0., 0.]]), np.vstack([T, T + 4])), MATERIAL)
    modes = p.rigid_modes()
    assert modes.shape == (p.ndof, 12)
    assert np.linalg.matrix_rank(modes) == 12


def test_empty_boundary_snapshot_and_material_attribute_protocol():
    m = mesh(boundary_facets=[], boundary_ids=[], boundary_groups={'empty': []})
    p = prepare(m, SimpleNamespace(**MATERIAL))
    assert not len(p.boundary_dofs('empty'))
    np.testing.assert_array_equal(p.pressure('empty', 1.), np.zeros(p.ndof))


@pytest.mark.parametrize('multiple_cells', [False, True])
def test_auto_boundary_facets_have_outward_cross_product_normals(multiple_cells):
    x = np.vstack([X, [[0., 0., -1.]]]) if multiple_cells else X
    t = np.array([[0, 1, 2, 3], [0, 2, 1, 4]]) if multiple_cells else T
    m = SolidMesh(x, t)
    for face in m.boundary_facets:
        owners = [cell for cell in t if set(face) <= set(cell)]
        assert len(owners) == 1
        opposite, = set(owners[0]) - set(face)
        a, b, c = x[face]
        assert np.cross(b - a, c - a) @ (x[opposite] - a) < 0
    # Roundtrip preserves explicit outward semantics and supplied row order.
    roundtrip = SolidMesh(x, t, boundary_facets=m.boundary_facets)
    np.testing.assert_array_equal(roundtrip.boundary_facets, m.boundary_facets)


@pytest.mark.parametrize('face', [[0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]])
def test_explicit_inward_boundary_facet_is_rejected(face):
    with pytest.raises(ValueError, match='outward'):
        SolidMesh(X, T, boundary_facets=[face])


def test_prepare_import_is_lazy_and_missing_backend_error_is_actionable():
    code = '''
import importlib.abc
import sys
class BlockSkfem(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'skfem':
            raise ModuleNotFoundError('backend unavailable for this test', name='skfem')
sys.meta_path.insert(0, BlockSkfem())
from anysolid import prepare
assert not {'numpy', 'scipy', 'skfem'} & sys.modules.keys()
try:
    prepare(None, {})
except ModuleNotFoundError as exc:
    assert 'ANYsolid[skfem]' in str(exc)
    assert 'pip install' in str(exc)
else:
    raise AssertionError('missing optional backend did not fail')
'''
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
    subprocess.run([sys.executable, '-c', code], check=True, timeout=10, env=env)


@pytest.mark.parametrize('order', [1, 2])
def test_pressure_matches_each_stored_outward_normal(order):
    initial = SolidMesh(X, T)
    groups = {str(i): [int(fid)] for i, fid in enumerate(initial.boundary_ids)}
    # Cyclic vertex permutations retain winding and must be kept unchanged.
    facets = np.roll(initial.boundary_facets, 1, axis=1)
    m = SolidMesh(X, T, boundary_facets=facets, boundary_groups=groups)
    np.testing.assert_array_equal(m.boundary_facets, facets)
    p = prepare(m, MATERIAL, order=order)
    for i, face in enumerate(m.boundary_facets):
        a, b, c = m.coordinates[face]
        outward_area_vector = np.cross(b - a, c - a) / 2
        pressure = 3.
        f = p.pressure(str(i), pressure)
        resultant = np.bincount(p.coefficient_components, weights=f, minlength=3)
        np.testing.assert_allclose(resultant, -pressure * outward_area_vector, rtol=1e-10, atol=1e-13)


@pytest.mark.parametrize('order', [1, 2])
def test_affine_traction_analytical_resultant_moment_and_work(order):
    p = prepare(mesh(boundary_groups={'x0': [70]}), MATERIAL, order=order)
    slope = 6.
    gradient = np.zeros((3, 3))
    gradient[0, 2] = slope
    # Offset origin and matching base value still give t=(slope*z,0,0).
    f = p.traction('x0', [slope * .2, 0., 0.], gradient=gradient, origin=[.1, .3, .2])
    resultant = np.bincount(p.coefficient_components, weights=f, minlength=3)
    np.testing.assert_allclose(resultant, [slope / 6, 0., 0.], rtol=1e-10, atol=1e-13)
    nodal_forces = np.zeros((p.ndof, 3))
    nodal_forces[np.arange(p.ndof), p.coefficient_components] = f
    moment = np.cross(p.coefficient_coordinates, nodal_forces).sum(axis=0)
    np.testing.assert_allclose(moment, [0., slope / 12, -slope / 24], rtol=1e-10, atol=1e-13)
    # u_x=z gives surface work slope*integral(z²)dA=slope/12.
    g = np.zeros((3, 3))
    g[0, 2] = 1.
    np.testing.assert_allclose(affine(p, g) @ f, slope / 12, rtol=1e-10)
    np.testing.assert_allclose(p.traction('x0', [1., 2., 3.]),
                               p.traction('x0', [1., 2., 3.], gradient=np.zeros((3, 3))), atol=1e-14)


@pytest.mark.parametrize('gradient,origin', [
    ([1., 2., 3.], [0., 0., 0.]),
    (np.full((3, 3), np.nan), [0., 0., 0.]),
    (np.eye(3), [0., 0.]),
    (None, [0., np.inf, 0.]),
])
def test_affine_traction_refusal(gradient, origin):
    p = prepare(mesh(), MATERIAL)
    with pytest.raises(ValueError):
        p.traction('base', [0., 0., 0.], gradient=gradient, origin=origin)


def test_p2_connected_pure_bending_exact_solution():
    from skfem import MeshTet
    from scipy.sparse.linalg import spsolve
    raw = MeshTet.init_tensor(np.linspace(0., 2., 3), np.linspace(0., 1., 2), np.linspace(-.5, .5, 3))
    x, t = raw.p.T.copy(), raw.t.T.copy()
    negative = np.linalg.det(x[t[:, 1:]] - x[t[:, :1]]) < 0
    t[negative, :2] = t[negative, 1::-1]
    initial = SolidMesh(x, t)
    groups = {name: initial.boundary_ids[np.all(x[initial.boundary_facets, 0] == xpos, axis=1)]
              for name, xpos in [('clamp', 0.), ('tip', 2.)]}
    E, curvature = 1000., .01
    p = prepare(SolidMesh(x, t, boundary_groups=groups), dict(elastic_modulus=E, poisson_ratio=0.), order=2)
    gradient = np.zeros((3, 3))
    gradient[0, 2] = E * curvature
    f = p.traction('tip', [0., 0., 0.], gradient=gradient)
    fixed = p.boundary_dofs('clamp')
    free = np.setdiff1d(np.arange(p.ndof), fixed)
    k = p.assemble_linear()
    a = np.zeros(p.ndof)
    a[free] = spsolve(k[free][:, free], f[free])
    q = p.coefficient_coordinates
    values = np.column_stack([curvature * q[:, 0] * q[:, 2], np.zeros(p.ndof), -curvature * q[:, 0]**2 / 2])
    exact = values[np.arange(p.ndof), p.coefficient_components]
    np.testing.assert_allclose(a, exact, rtol=1e-10, atol=1e-12)
    r = p.recover(a)
    exact_stress = np.zeros_like(r.stress)
    exact_stress[..., 0, 0] = E * curvature * r.coordinates[..., 2]
    np.testing.assert_allclose(r.stress, exact_stress, rtol=1e-10, atol=1e-10)
    np.testing.assert_allclose(a @ k @ a, E * curvature**2 * 2. / 12, rtol=1e-10)
