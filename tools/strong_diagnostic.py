"""Tools-only point tying control, deliberately excluded from the public adapter API.

Point forces are diagnostic multipliers, not a qualified distributed traction.
This may overconstrain solid deformation and must never become a silent fallback.
"""
import hashlib
from types import MappingProxyType
import numpy as np
from scipy import sparse
from anysolid.coupling import CouplingOperator, build_weak_connector


def signature(matrix):
    digest = hashlib.sha256(str(matrix.shape).encode())
    for array in (matrix.indptr,matrix.indices,matrix.data):
        digest.update(array.tobytes())
    return digest.hexdigest()


def build_strong_point_control(trace,prepared,group):
    """Tie every current backend boundary-coefficient location after coverage validation.

    Only research fixtures use this tool. Unlike weak section moments, these
    are pointwise constraints. No rank truncation, stabilization or penalty.
    """
    checked = build_weak_connector(trace,prepared,group,multiplier_breakpoints=[0.,trace.length])
    if type(prepared).__module__ != "anysolid.backend" or prepared.order not in (1,2):
        raise ValueError("strong point control is restricted to the verified nodal scikit-fem P1/P2 backend")
    locations = prepared.coefficient_coordinates[prepared.boundary_dofs(group)]
    points = np.unique(locations,axis=0)
    if 3*len(points) > 256 or prepared.ndof+trace.ndof > 4000:
        raise ValueError("strong diagnostic exceeds bounded research matrix dimensions")
    chart = trace.chart(points)
    shell = trace.displacement_operator(points).tocsr()
    solid = prepared.trace(points).tocsr()
    combined = sparse.hstack((shell,-solid),format="csr")
    if np.linalg.matrix_rank(combined.toarray()) != combined.shape[0]:
        raise ValueError("strong diagnostic collocation constraints are redundant")
    affine = np.frombuffer(np.zeros(shell.shape[0]).tobytes(),dtype=float)
    metadata = MappingProxyType({"geometry_validation":checked.metadata,"diagnostic_only":True,
        "traction_interpretation":"point forces only; no distributed-traction qualification",
        "chart_points":tuple(map(tuple,chart)),"constraint_rows":int(shell.shape[0]),
        "strong_grid":"all unique boundary coefficient locations",
        "continuity_scope":"nodal collocation; full piecewise continuity only on compatible trace partitions"})
    return CouplingOperator(shell,solid,affine,metadata,trace,prepared.cache_signature(),
                            (signature(shell),signature(solid)),
                            formulation="strong_point_diagnostic_v1")
