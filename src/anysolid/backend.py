"""Linear elasticity delegated to scikit-fem's tetrahedral vector spaces."""
from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import numpy as np
from scipy.sparse import csr_matrix, coo_matrix
from scipy.sparse.csgraph import connected_components
try:
    import skfem
    from skfem import MeshTet, Basis, FacetBasis, ElementVector, ElementTetP1, ElementTetP2, LinearForm, asm
    from skfem.helpers import dot, sym_grad
    from skfem.models.elasticity import linear_elasticity, linear_stress
except ModuleNotFoundError as exc:
    if exc.name == 'skfem':
        raise ModuleNotFoundError(
            'The optional scikit-fem backend is required; install it with '
            'python -m pip install "ANYsolid[skfem]"', name='skfem') from exc
    raise
from .mesh import SolidMesh, _immutable, _thaw_json


@dataclass(frozen=True)
class Recovery:
    strain: np.ndarray
    stress: np.ndarray
    coordinates: np.ndarray
    weights: np.ndarray
    cell_ids: np.ndarray
    sampling: str = 'element_quadrature'
    tensor_convention: str = 'physical_tensor'


def _vector(value, name):
    a = np.asarray(value, dtype=float)
    if a.shape != (3,) or not np.isfinite(a).all():
        raise ValueError(f'{name} must be a finite vector of shape (3,)')
    return a


def prepare(mesh, material, *, order=2):
    return PreparedSolid(mesh, material, order=order)


class PreparedSolid:
    """Prepared constant-isotropic small-strain region in physical xyz DOFs."""

    def __setattr__(self, name, value):
        if getattr(self, '_locked', False):
            raise AttributeError('prepared regions are immutable; prepare a new region')
        object.__setattr__(self, name, value)

    def __init__(self, mesh, material, *, order=2):
        if isinstance(order, bool) or order not in (1, 2):
            raise ValueError('order must be 1 or 2')
        self.mesh = SolidMesh.snapshot(mesh)
        try:
            if isinstance(material, Mapping):
                E, nu = material['elastic_modulus'], material['poisson_ratio']
            else:
                E, nu = material.elastic_modulus, material.poisson_ratio
            if np.ndim(E) != 0 or np.ndim(nu) != 0 or isinstance(E, (bool, np.bool_)) or isinstance(nu, (bool, np.bool_)):
                raise ValueError('material constants must be scalars')
            E, nu = float(E), float(nu)
        except (AttributeError, KeyError, TypeError, OverflowError) as exc:
            raise ValueError('material requires elastic_modulus and poisson_ratio') from exc
        if not np.isfinite([E, nu]).all() or E <= 0 or not 0 <= nu <= .45:
            raise ValueError('material envelope: finite E>0, 0<=nu<=0.45')
        self.order, self.elastic_modulus, self.poisson_ratio = int(order), E, nu
        self._mu = E / (2 * (1 + nu))
        self._lam = E * nu / ((1 + nu) * (1 - 2 * nu))
        self._skmesh = MeshTet(np.array(self.mesh.coordinates.T), np.array(self.mesh.cells.T), sort_t=False)
        self._element = ElementVector(ElementTetP1() if order == 1 else ElementTetP2())
        self._basis = Basis(self._skmesh, self._element, intorder=2 * order)
        self.ndof = self._basis.N
        self.coefficient_coordinates = _immutable(self._basis.doflocs.T)
        components = np.empty(self.ndof, dtype=np.int64)
        self._component_indices = self._basis.split_indices()
        for component, indices in enumerate(self._component_indices):
            components[indices] = component
        self.coefficient_components = _immutable(components)
        face_index = {tuple(sorted(f)): i for i, f in enumerate(self._skmesh.facets.T)}
        self._boundary_indices = np.array([face_index[tuple(sorted(f))] for f in self.mesh.boundary_facets], dtype=np.int32)
        self._stiffness = None
        self._locked = True

    def assemble_linear(self):
        if self._stiffness is None:
            object.__setattr__(self, '_stiffness', csr_matrix(asm(linear_elasticity(self._lam, self._mu), self._basis)))
        return self._stiffness.copy()

    def rigid_modes(self):
        """Three translations and three scaled rotations per vertex-connected part.

        Columns are grouped by connected component, translation xyz then
        rotation xyz. Element DOF ownership determines coefficient membership.
        This supplies the physical rigid subspace, not a complete mechanism
        diagnosis for meshes connected only at a point or edge.
        """
        cells = self.mesh.cells
        rows = np.repeat(cells[:, 0], 3)
        cols = cells[:, 1:].ravel()
        graph = coo_matrix((np.ones(2 * len(rows)),
                            (np.concatenate([rows, cols]), np.concatenate([cols, rows]))),
                           shape=(len(self.mesh.coordinates),) * 2).tocsr()
        count, labels = connected_components(graph, directed=False)
        cell_components = labels[cells[:, 0]]
        dof_components = np.empty(self.ndof, dtype=np.int64)
        # Any shared coefficient belongs to the same connectivity component.
        for local in self._basis.element_dofs:
            dof_components[local] = cell_components
        modes = np.zeros((self.ndof, 6 * count))
        for component in range(count):
            indices = np.flatnonzero(dof_components == component)
            vertices = self.mesh.coordinates[labels == component]
            center = vertices.mean(axis=0)
            scale = np.linalg.norm(vertices - center, axis=1).max()
            local_coordinates = (self.coefficient_coordinates[indices] - center) / scale
            physical_components = self.coefficient_components[indices]
            for axis in range(3):
                modes[indices, 6 * component + axis] = physical_components == axis
                rotations = np.cross(np.eye(3)[axis], local_coordinates)
                modes[indices, 6 * component + 3 + axis] = rotations[np.arange(len(indices)), physical_components]
        return _immutable(modes)

    def _facets(self, group):
        try:
            ids = self.mesh.boundary_groups[group]
        except (KeyError, TypeError) as exc:
            raise ValueError(f'unknown boundary group: {group!r}') from exc
        return self._boundary_indices[np.isin(self.mesh.boundary_ids, ids)]

    def boundary_dofs(self, group, components=(0, 1, 2)):
        selected = tuple(components)
        if any(isinstance(c, (bool, np.bool_)) or not isinstance(c, (int, np.integer)) or c not in (0, 1, 2) for c in selected) or len(set(selected)) != len(selected):
            raise ValueError('components must be distinct physical indices 0,1,2')
        if group in self.mesh.boundary_groups:
            dofs = self._basis.get_dofs(facets=self._facets(group)).all()
        elif group in self.mesh.node_groups:
            nodes = np.flatnonzero(np.isin(self.mesh.node_ids, self.mesh.node_groups[group]))
            dofs = self._basis.get_dofs(nodes=nodes).all()
        else:
            raise ValueError(f'unknown boundary or node group: {group!r}')
        return np.asarray(dofs[np.isin(self.coefficient_components[dofs], selected)], dtype=np.int64)

    def body_load(self, vector):
        force = _vector(vector, 'body force density')
        @LinearForm
        def form(v, w):
            return np.einsum('i,i...->...', force, v)
        return np.asarray(asm(form, self._basis))

    def traction(self, group, vector, *, gradient=None, origin=(0., 0., 0.)):
        force = _vector(vector, 'traction')
        reference = _vector(origin, 'traction origin')
        affine_gradient = np.zeros((3, 3)) if gradient is None else np.asarray(gradient, dtype=float)
        if affine_gradient.shape != (3, 3) or not np.isfinite(affine_gradient).all():
            raise ValueError('traction gradient must be a finite (3,3) matrix')
        facets = self._facets(group)
        if len(facets) == 0:
            return np.zeros(self.ndof)
        @LinearForm
        def form(v, w):
            traction = force[:, None, None] + np.einsum(
                'ij,j...->i...', affine_gradient, w.x - reference[:, None, None])
            return dot(traction, v)
        return np.asarray(asm(form, FacetBasis(self._skmesh, self._element, facets=facets, intorder=2 * self.order)))

    def pressure(self, group, value):
        try:
            if np.ndim(value) != 0 or isinstance(value, (bool, np.bool_)):
                raise ValueError('pressure must be a finite scalar')
            pressure = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError('pressure must be a finite scalar') from exc
        if not np.isfinite(pressure):
            raise ValueError('pressure must be a finite scalar')
        facets = self._facets(group)
        if len(facets) == 0:
            return np.zeros(self.ndof)
        @LinearForm
        def form(v, w):
            return -pressure * dot(w.n, v)
        return np.asarray(asm(form, FacetBasis(self._skmesh, self._element, facets=facets, intorder=2 * self.order)))

    def trace(self, points):
        x = np.asarray(points, dtype=float)
        if x.ndim != 2 or x.shape[1] != 3 or not np.isfinite(x).all():
            raise ValueError('trace points must be finite (N,3)')
        if len(x) == 0:
            return csr_matrix((0, self.ndof))
        try:
            component_major = self._basis.probes(x.T).tocsr()
        except ValueError as exc:
            raise ValueError('trace points must lie inside the solid (including its boundary)') from exc
        permutation = np.arange(3 * len(x)).reshape(3, len(x)).T.ravel()
        return csr_matrix(component_major[permutation])

    def recover(self, coefficients):
        a = np.asarray(coefficients, dtype=float)
        if a.shape != (self.ndof,) or not np.isfinite(a).all():
            raise ValueError(f'coefficients must be finite ({self.ndof},)')
        field = self._basis.interpolate(a)
        eps = sym_grad(field)
        sigma = linear_stress(self._lam, self._mu)(eps)
        return Recovery(_immutable(np.moveaxis(eps, (0, 1), (-2, -1))),
                        _immutable(np.moveaxis(sigma, (0, 1), (-2, -1))),
                        _immutable(np.moveaxis(self._basis.global_coordinates(), 0, -1)),
                        _immutable(self._basis.dx), self.mesh.cell_ids)

    def cache_signature(self):
        h = hashlib.sha256()
        h.update(json.dumps(dict(backend='scikit-fem', version=skfem.__version__,
                                 schema=1, order=self.order, E=self.elastic_modulus,
                                 nu=self.poisson_ratio, units=self.mesh.units,
                                 geometry_order=self.mesh.geometry_order,
                                 provenance=_thaw_json(self.mesh.provenance)), sort_keys=True).encode())
        for name in ('coordinates', 'cells', 'node_ids', 'cell_ids', 'boundary_facets', 'boundary_ids'):
            a = getattr(self.mesh, name)
            h.update(name.encode() + str(a.shape).encode() + a.dtype.str.encode() + a.tobytes())
        for name in ('node_groups', 'cell_groups', 'boundary_groups'):
            h.update(name.encode())
            for key, a in sorted(getattr(self.mesh, name).items()):
                h.update(json.dumps(key).encode() + str(a.shape).encode() + a.tobytes())
        return h.hexdigest()
