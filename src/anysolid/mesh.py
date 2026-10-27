"""Validated, owned numerical snapshots. Connectivity uses zero-based rows."""
from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping
import json
import numpy as np


def _immutable(value, dtype=None):
    a = np.ascontiguousarray(value, dtype=dtype)
    # Bytes ownership also prevents callers from re-enabling WRITEABLE.
    return np.frombuffer(a.tobytes(), dtype=a.dtype).reshape(a.shape)


def _integers(value, name, shape=None):
    a = np.asarray(value)
    if a.dtype.kind not in 'iu' or a.dtype.kind == 'b':
        raise ValueError(f'{name} must contain integers')
    if a.dtype.kind == 'u' and a.size and a.max() > np.iinfo(np.int64).max:
        raise ValueError(f'{name} exceeds supported integer range')
    a = np.asarray(a, dtype=np.int64)
    if shape is not None and a.shape != shape:
        raise ValueError(f'{name} must have shape {shape}')
    return _immutable(a)


def _ids(value, n, name):
    if n == 0 and value is not None and np.asarray(value).shape == (0,):
        value = np.empty(0, dtype=np.int64)
    a = _integers(np.arange(n) if value is None else value, name, (n,))
    if len(np.unique(a)) != n:
        raise ValueError(f'{name} must be unique')
    return a


def _groups(groups, ids, name):
    result = {}
    if groups is not None and not isinstance(groups, Mapping):
        raise ValueError(f'{name} must be a mapping')
    for key, values in (groups or {}).items():
        if not isinstance(key, str) or not key:
            raise ValueError(f'{name} names must be nonempty strings')
        # Empty Python lists infer float; explicitly allow empty groups.
        values = np.asarray(values)
        if values.size == 0:
            values = np.empty(0, dtype=np.int64)
        a = _integers(values, f'{name}[{key}]')
        if a.ndim != 1 or len(np.unique(a)) != len(a) or not np.isin(a, ids).all():
            raise ValueError(f'{name}[{key}] must contain unique known external IDs')
        result[key] = a
    return MappingProxyType(result)


def _freeze_json(value):
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze_json(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(v) for v in value)
    return value


def _thaw_json(value):
    if isinstance(value, Mapping):
        return {k: _thaw_json(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(v) for v in value]
    return value


@dataclass(frozen=True, init=False, eq=False)
class SolidMesh:
    """Immutable tet4 SI snapshot with optional externally identified groups.

    Exterior facets/IDs are generated deterministically when omitted. Supplied
    boundary facets may describe a subset of the exterior surface.
    """
    coordinates: np.ndarray
    cells: np.ndarray
    node_ids: np.ndarray
    cell_ids: np.ndarray
    boundary_facets: np.ndarray
    boundary_ids: np.ndarray
    node_groups: Mapping
    cell_groups: Mapping
    boundary_groups: Mapping
    units: str
    geometry_order: int
    provenance: Mapping

    def __init__(self, coordinates, cells, node_ids=None, cell_ids=None,
                 boundary_facets=None, boundary_ids=None, node_groups=None,
                 cell_groups=None, boundary_groups=None, *, units='m',
                 geometry_order=1, provenance=None):
        x = np.asarray(coordinates, dtype=float)
        if x.ndim != 2 or x.shape[1] != 3 or len(x) < 4 or not np.isfinite(x).all():
            raise ValueError('coordinates must be finite (N,3), N>=4')
        t = _integers(cells, 'cells')
        if t.ndim != 2 or t.shape[1] != 4 or not len(t):
            raise ValueError('only nonempty tet4 geometry is supported; C3D10 is unsupported')
        if t.min() < 0 or t.max() >= len(x):
            raise ValueError('cells reference unknown coordinate rows')
        if np.any(np.diff(np.sort(t, axis=1), axis=1) == 0):
            raise ValueError('a cell repeats a vertex')
        if len(np.unique(np.sort(t, axis=1), axis=0)) != len(t):
            raise ValueError('duplicate cells')
        if len(np.unique(t)) != len(x):
            raise ValueError('all coordinate rows must belong to a cell')
        if len(np.unique(x, axis=0)) != len(x):
            raise ValueError('duplicate coordinate rows')
        with np.errstate(over='ignore', invalid='ignore'):
            d = x[t[:, 1:]] - x[t[:, :1]]
        if not np.isfinite(d).all():
            raise ValueError('cell coordinate differences exceed floating-point range')
        coordinate_scale = np.max(np.abs(d), axis=(1, 2))
        if np.any(coordinate_scale == 0):
            raise ValueError('cells must have nondegenerate volume')
        normalized = d / coordinate_scale[:, None, None]
        det = np.linalg.det(normalized)
        scale = np.max(np.linalg.norm(normalized, axis=2), axis=1)
        if np.any(det <= 64 * np.finfo(float).eps * scale**3):
            raise ValueError('cells must have positive orientation and nondegenerate volume')
        faces = np.concatenate([t[:, [0, 1, 2]], t[:, [0, 1, 3]],
                                t[:, [0, 2, 3]], t[:, [1, 2, 3]]])
        opposites = np.concatenate([t[:, 3], t[:, 2], t[:, 1], t[:, 0]])
        unique, first, counts = np.unique(np.sort(faces, axis=1), axis=0,
                                          return_index=True, return_counts=True)
        if np.any(counts > 2):
            raise ValueError('nonmanifold facet shared by more than two cells')
        exterior = unique[counts == 1]
        exterior_first = first[counts == 1]
        opposite_by_face = {tuple(face): opposites[index]
                            for face, index in zip(exterior, exterior_first)}

        def inward_sign(facets):
            if not len(facets):
                return np.empty(0)
            opposite = np.array([opposite_by_face[tuple(sorted(face))] for face in facets])
            vectors = np.concatenate([x[facets[:, 1:]] - x[facets[:, :1]],
                                      (x[opposite] - x[facets[:, 0]])[:, None]], axis=1)
            # Scaling preserves orientation and avoids cross-product overflow.
            vectors /= np.max(np.abs(vectors), axis=(1, 2))[:, None, None]
            return np.einsum('ij,ij->i', np.cross(vectors[:, 0], vectors[:, 1]), vectors[:, 2])

        if boundary_facets is None:
            f = np.array(faces[exterior_first], copy=True)
            reverse = inward_sign(f) > 0
            f[reverse, 1:] = f[reverse, :0:-1]
        else:
            raw = np.asarray(boundary_facets)
            if raw.size == 0:
                raw = np.empty((0, 3), dtype=np.int64)
            f = _integers(raw, 'boundary_facets')
            if f.ndim != 2 or f.shape[1] != 3:
                raise ValueError('boundary_facets must have shape (F,3)')
            canonical = [tuple(row) for row in np.sort(f, axis=1)]
            if len(set(canonical)) != len(canonical) or not set(canonical) <= set(map(tuple, exterior)):
                raise ValueError('boundary facets must be unique exterior cell faces')
            if np.any(inward_sign(f) >= 0):
                raise ValueError('boundary facets must have outward vertex orientation')
        if units != 'm' or isinstance(geometry_order, bool) or geometry_order != 1:
            raise ValueError("only units='m', geometry_order=1 are supported")
        ni, ci, fi = _ids(node_ids, len(x), 'node_ids'), _ids(cell_ids, len(t), 'cell_ids'), _ids(boundary_ids, len(f), 'boundary_ids')
        if provenance is not None and not isinstance(provenance, Mapping):
            raise ValueError('provenance must be a JSON-compatible mapping')
        try:
            metadata = json.loads(json.dumps(_thaw_json(provenance or {}), allow_nan=False, sort_keys=True))
        except (ValueError, TypeError) as exc:
            raise ValueError('provenance must be finite JSON-compatible data') from exc
        values = dict(coordinates=_immutable(x), cells=t, node_ids=ni, cell_ids=ci,
                      boundary_facets=_immutable(f, np.int64), boundary_ids=fi,
                      node_groups=_groups(node_groups, ni, 'node_groups'),
                      cell_groups=_groups(cell_groups, ci, 'cell_groups'),
                      boundary_groups=_groups(boundary_groups, fi, 'boundary_groups'),
                      units='m', geometry_order=1, provenance=_freeze_json(metadata))
        for key, value in values.items():
            object.__setattr__(self, key, value)

    @classmethod
    def snapshot(cls, mesh):
        if isinstance(mesh, cls):
            return mesh
        names = ('coordinates', 'cells', 'node_ids', 'cell_ids', 'boundary_facets',
                 'boundary_ids', 'node_groups', 'cell_groups', 'boundary_groups',
                 'units', 'geometry_order', 'provenance')
        try:
            return cls(**{name: getattr(mesh, name) for name in names})
        except AttributeError as exc:
            raise ValueError('mesh does not implement the SolidMesh structural protocol') from exc
