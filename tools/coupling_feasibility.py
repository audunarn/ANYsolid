"""Bounded prospectively registered research coupling diagnostics.

JSONL records flush on every case boundary. Spectra are finite-case diagnostics
only and never establish production qualification or a uniform inf-sup bound.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback
from collections.abc import Mapping
import numpy as np
import scipy
from scipy import sparse, linalg
from scipy.sparse.linalg import splu
import skfem
from skfem import BilinearForm, asm
from skfem.helpers import dot
from anysolid import SolidMesh, prepare
from anysolid.coupling import build_weak_connector
from anysolver import BoundaryCondition, LoadCase, assemble_mass_matrix, assemble_stiffness_matrix
from anysolver.assembly import build_constraint_transformation
from anysolver.solids import SolidModel, ResidualScales


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'docs/coupling_feasibility_manifest.json'
PATCH_MANIFEST = ROOT / 'docs/physical_patch_manifest.json'
FIXTURE = ROOT.parent / 'ANYsolver/tests/test_solid_coupling.py'


def _json_value(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(f'unsupported diagnostic JSON value: {type(value).__name__}')


def emit(record):
    print(json.dumps(record, allow_nan=False, sort_keys=True, default=_json_value), flush=True)


def import_fixture():
    spec = importlib.util.spec_from_file_location('_controlled_coupling_specimen', FIXTURE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def controlled_specimen(fixture, nshell, nsolid, thickness, manifest):
    """Reuse original fixture unchanged; construct own thickness variants."""
    default = manifest['geometry']['default_thickness_m']
    E, nu = manifest['material']['E_Pa'], manifest['material']['nu']
    if thickness == default:
        result = fixture.specimen(nshell=nshell, nsolid=nsolid, nu=nu)
        # Density enters only the diagnostic norm, never physical stiffness.
        result[0].add_material('m', E, nu, density=1.)
        return result
    native = fixture.FEModel('controlled-thickness-coupling-diagnostic')
    native.add_material('m', E, nu, density=1.)
    edges = [[], []]
    clamp, tip = [], []
    for side, xs in enumerate(((-1., 0.), (1., 2.))):
        nodes = {}
        for j, y in enumerate(np.linspace(0., 1., nshell + 1)):
            for i, x in enumerate(xs):
                nid = len(native.mesh.nodes) + 1
                native.add_node(nid, float(x), float(y), 0.)
                nodes[i, j] = nid
                if side == 0 and i == 0:
                    clamp.append(nid)
                if side == 1 and i == 1:
                    tip.append(nid)
        for j in range(nshell):
            eid = len(native.mesh.elements) + 1
            node_ids = [nodes[0, j], nodes[1, j], nodes[1, j + 1], nodes[0, j + 1]]
            native.add_element(eid, fixture.create_shell_element(
                eid, node_ids, 'm', thickness=thickness, reference_normal=(0., 0., 1.)))
            edges[side].append((eid, 1 if side == 0 else 3))
    edges[1].reverse()
    raw = fixture.MeshTet.init_tensor(np.linspace(0., 1., nsolid + 1),
        np.linspace(0., 1., nsolid + 1), np.linspace(-thickness / 2, thickness / 2, 3)).oriented()
    initial = SolidMesh(raw.p.T, raw.t.T)
    facet_x = initial.coordinates[initial.boundary_facets, 0]
    groups = {name: initial.boundary_ids[np.all(np.abs(facet_x - value) < 1e-12, axis=1)]
              for name, value in [('left', 0.), ('right', 1.)]}
    backend = prepare(SolidMesh(initial.coordinates, initial.cells, boundary_groups=groups),
                      {'elastic_modulus': E, 'poisson_ratio': nu})
    return (native, backend, fixture.ShellEdgeTrace(native, edges[0]),
            fixture.ShellEdgeTrace(native, edges[1]), clamp, tip)


def setup_case(fixture, nshell, nsolid, thickness, manifest, *, prescribed_field=None,
               extra_surface_groups=False):
    native, backend, left, right, clamp, tip = controlled_specimen(
        fixture, nshell, nsolid, thickness, manifest)
    E, nu = manifest['material']['E_Pa'], manifest['material']['nu']
    if backend.elastic_modulus != E or backend.poisson_ratio != nu:
        raise ValueError('constructed backend material differs from registered E/nu')
    if left.thickness != thickness or right.thickness != thickness:
        raise ValueError('constructed trace thickness differs from registered thickness')
    if extra_surface_groups:
        mesh = backend.mesh
        groups = dict(mesh.boundary_groups)
        for axis, name in ((1, 'y'), (2, 'z')):
            for side, value in enumerate((mesh.coordinates[:, axis].min(), mesh.coordinates[:, axis].max())):
                groups[f'{name}{side}'] = mesh.boundary_ids[np.all(
                    abs(mesh.coordinates[mesh.boundary_facets, axis] - value) < 1e-12, axis=1)]
        backend = prepare(SolidMesh(mesh.coordinates, mesh.cells, node_ids=mesh.node_ids,
            cell_ids=mesh.cell_ids, boundary_facets=mesh.boundary_facets,
            boundary_ids=mesh.boundary_ids, boundary_groups=groups,
            provenance={'fixture': 'registered controlled physical patch'}),
            {'elastic_modulus': E, 'poisson_ratio': nu})
    keys = ('ux', 'uy', 'uz', 'rx', 'ry', 'rz')
    for nid in clamp:
        values = np.zeros(6) if prescribed_field is None else prescribed_field(native.mesh.nodes[nid].coords())
        native.add_boundary_condition(BoundaryCondition(name=f'left-{nid}', node_ids=[nid],
            dof_constraints={key: float(value) for key, value in zip(keys, values)}))
    native.apply_boundary_conditions()
    knots = manifest['multiplier_partition_m']
    operators = [build_weak_connector(trace, backend, name, multiplier_breakpoints=knots)
                 for trace, name in ((left, 'left'), (right, 'right'))]
    nprimary = native.mesh.dof_manager.total_dofs + backend.ndof
    nrows = sum(op.C_shell.shape[0] for op in operators)
    if nprimary > manifest['bounds']['maximum_primary_dofs'] or nrows > manifest['bounds']['maximum_multiplier_rows']:
        raise ValueError(f'registered dimension bounds exceeded: primary={nprimary}, multipliers={nrows}')
    return native, backend, operators, tip, {'primary_dofs': nprimary, 'multiplier_rows': nrows}


def bending_case(fixture, manifest):
    t = manifest['geometry']['default_thickness_m']
    native, backend, operators, tip, dimensions = setup_case(fixture, 1, 1, t, manifest)
    registered = manifest['pure_bending']
    refs = registered['scales']
    scales = ResidualScales(refs['length_m'], refs['force_N'], refs['displacement_m'],
                            tuple(refs['interface_displacements_m']))
    load = LoadCase('pure_bending')
    for nid in tip:
        load.add_nodal_load(nid, moments=[0., registered['moment_Nm'] / len(tip), 0.])
    model = SolidModel(native, research_coupling=True, residual_scales={'pure_bending': scales})
    model.add_region('solid', prepared=backend)
    for operator in operators:
        model.add_interface('solid', operator)
    try:
        result = model.solve_static(('pure_bending',), native_load_cases={'pure_bending': load})
    except Exception as exc:
        # Scientific/host rejection retains its diagnostics without retuning.
        emit({'type': 'solve_failure', 'case': 'bending', 'error_type': type(exc).__name__,
              'error': str(exc), 'diagnostics': getattr(exc, 'diagnostics', None)})
        raise
    coefficients = result.coefficients[:, 0]
    nsh = result.layout.native_dofs
    native_u, solid_u = coefficients[:nsh], result.region_coefficients('solid')[:, 0]
    Ksh, _ = assemble_stiffness_matrix(native)
    Kv = backend.assemble_linear()
    native_energy_twice = float(native_u @ Ksh @ native_u)
    solid_energy_twice = float(solid_u @ Kv @ solid_u)
    energy = native_energy_twice + solid_energy_twice
    tip_dofs = [native.mesh.dof_manager.get_node_dofs(nid) for nid in tip]
    w = np.array([native_u[dofs[2]] for dofs in tip_dofs])
    theta = np.array([native_u[dofs[4]] for dofs in tip_dofs])
    recovery = backend.recover(solid_u)
    select = (recovery.coordinates[..., 0] >= .25) & (recovery.coordinates[..., 0] <= .75)
    if not np.any(select):
        raise ValueError('registered interior stress sampling selected no points')
    stress = recovery.stress[select]
    exact = np.zeros_like(stress)
    # Independent closed-form continuum reference, not recovered displacement.
    exact[:, 0, 0] = manifest['material']['E_Pa'] * registered['curvature_per_m'] * recovery.coordinates[..., 2][select]
    errors = {
        'tip_w_relative': float(np.max(abs(w - registered['tip_w_reference_m'])) / abs(registered['tip_w_reference_m'])),
        'tip_theta_relative': float(np.max(abs(theta - registered['tip_theta_reference_rad'])) / abs(registered['tip_theta_reference_rad'])),
        'energy_twice_relative': float(abs(energy - registered['energy_twice_reference_Nm']) / abs(registered['energy_twice_reference_Nm'])),
        'stress_scaled_max': float(np.max(abs(stress - exact)) / registered['stress_scale_Pa']),
    }
    limit = manifest['thresholds']['displacement_rotation_energy_relative']
    checks = {name: bool(value <= (manifest['thresholds']['stress_scaled_max'] if name == 'stress_scaled_max' else limit))
              for name, value in errors.items()}
    residual_report = result.diagnostics['registered_residual_report']
    checks['registered_residuals'] = bool(residual_report['passed'])
    return {'type': 'case_result', 'case': 'bending', 'passed': bool(all(checks.values())),
            'qualification': 'research_only_NO_GO_PRODUCTION_UNQUALIFIED', **dimensions,
            'tip_w_m': w.tolist(), 'tip_theta_y_rad': theta.tolist(),
            'energy_twice_Nm': energy, 'native_energy_twice_Nm': native_energy_twice,
            'solid_energy_twice_Nm': solid_energy_twice,
            'applied_moment_Nm': registered['moment_Nm'],
            'external_work_Nm': float(registered['moment_Nm'] * theta.mean()),
            'stress_sample_count': int(select.sum()),
            'stress_sample_coordinates_m': recovery.coordinates[select].tolist(),
            'stress_samples_Pa': stress.tolist(), 'stress_reference_samples_Pa': exact.tolist(),
            'references': registered, 'errors': errors, 'checks': checks,
            'residual_report': residual_report,
            'legacy_componentwise_equilibrium': result.diagnostics['legacy_componentwise_equilibrium'],
            'legacy_componentwise_constraint_error': result.diagnostics['legacy_componentwise_constraint_error']}


def spectrum_case(fixture, manifest, nshell, nsolid, thickness):
    if skfem.__version__ != '12.0.2':
        raise RuntimeError('verification-only private basis access pinned to scikit-fem 12.0.2')
    native, backend, operators, _, dimensions = setup_case(fixture, nshell, nsolid, thickness, manifest)
    Ksh, _ = assemble_stiffness_matrix(native)
    Msh, _ = assemble_mass_matrix(native)
    _, _, Tsh, ush, _, _ = build_constraint_transformation(Ksh, np.zeros(Ksh.shape[0]), native)
    if np.any(ush != 0):
        raise ValueError('stability norm assumes the registered homogeneous clamp')
    Kv = backend.assemble_linear()
    @BilinearForm
    def vector_l2(u, v, w):
        return dot(u, v)
    Mv = sparse.csr_matrix(asm(vector_l2, backend._basis))
    K = sparse.block_diag((Ksh, Kv), format='csr')
    M = sparse.block_diag((Msh, Mv), format='csr')
    P = sparse.block_diag((Tsh, sparse.eye(backend.ndof)), format='csr')
    C = sparse.vstack([sparse.hstack((op.C_shell, -op.C_solid)) for op in operators], format='csr')
    E = manifest['material']['E_Pa']
    length = manifest['stability_diagnostic']['characteristic_length_m']
    V = (P.T @ (K + (E / length**2) * M) @ P).tocsc()
    vnorm = float(sparse.linalg.norm(V, ord=np.inf))
    v_asymmetry = float(sparse.linalg.norm(V - V.T, ord=np.inf) / vnorm)
    if not np.isfinite(V.data).all() or not np.isfinite(v_asymmetry) or v_asymmetry > manifest['thresholds']['spectrum_asymmetry']:
        raise ValueError(f'verification V fails symmetry/finite check: {v_asymmetry}')
    if V.shape[0] > manifest['bounds']['maximum_spd_dense_dimension']:
        raise ValueError('bounded dense verification SPD check dimension exceeded')
    # Explicit SPD certificate only for these bounded norm reference cases;
    # never a physical-system solve or fallback.
    linalg.cholesky(V.toarray(), lower=True, check_finite=True)
    reduced_C = (C @ P).tocsr()
    # Assemble analytic P1 line mass, then the five registered section modes.
    knots = np.array(manifest['multiplier_partition_m'])
    line_mass = np.zeros((len(knots), len(knots)))
    for i, segment in enumerate(np.diff(knots)):
        line_mass[i:i + 2, i:i + 2] += thickness * segment / 6 * np.array([[2., 1.], [1., 2.]])
    interface_mass = np.kron(line_mass, np.diag([1., 1., 1., 1 / 3, 1 / 3]))
    Q = (length / E) * linalg.block_diag(*(interface_mass for _ in operators))
    factor = splu(V)
    response = factor.solve(reduced_C.T.toarray())
    H = np.asarray(reduced_C @ response)
    scale = np.linalg.norm(H, ord=np.inf)
    if not np.isfinite(H).all() or not np.isfinite(Q).all() or scale == 0:
        raise ValueError('nonfinite or zero diagnostic Schur operator')
    asymmetry = float(np.linalg.norm(H - H.T, ord=np.inf) / scale)
    if asymmetry > manifest['thresholds']['spectrum_asymmetry']:
        raise ValueError(f'Schur asymmetry {asymmetry} exceeds registered threshold')
    eigenvalues = linalg.eigh((H + H.T) / 2, Q, eigvals_only=True)
    if not np.isfinite(eigenvalues).all():
        raise ValueError('nonfinite generalized diagnostic spectrum')
    positive = eigenvalues[eigenvalues > 0]
    beta = float(np.sqrt(positive.min())) if len(positive) else None
    beta_full = float(np.sqrt(eigenvalues.min())) if np.all(eigenvalues > 0) else 0.
    return {'type': 'case_result', 'case': 'spectrum', 'nshell': nshell, 'nsolid': nsolid,
            'thickness_m': thickness, **dimensions, 'reduced_primary_dofs': V.shape[0],
            'diagnostic_completed': True, 'qualification': 'NO_GO_PRODUCTION_UNQUALIFIED',
            'claim': manifest['stability_diagnostic']['claim'], 'characteristic_length_m': length,
            'generalized_eigenvalues': eigenvalues.tolist(), 'beta_min_positive': beta,
            'beta_full': beta_full, 'V_relative_asymmetry': v_asymmetry,
            'V_bounded_dense_cholesky_passed': True,
            'nonpositive_eigenvalue_count': int(np.count_nonzero(eigenvalues <= 0)),
            'schur_relative_asymmetry': asymmetry, 'H': H.tolist(), 'Q': Q.tolist(),
            'norm_factor_shape': list(V.shape), 'norm_factor_nnz': int(V.nnz),
            'native_mass_nnz': int(Msh.nnz), 'solid_mass_nnz': int(Mv.nnz),
            'norm_only_mass_addition': True,
            'native_mass_interpretation': manifest['stability_diagnostic']['native_mass_interpretation'],
            'block_rhs_shape': list(response.shape), 'dense_eigensolve_shape': list(H.shape)}


def exact_patch_fields(name, case):
    """Closed-form continuum displacement and physical shell reference traces."""
    def solid(x):
        x = np.asarray(x)
        X, y, z = x[..., 0] + 1., x[..., 1] - .5, x[..., 2]
        zero = np.zeros_like(X)
        if name == 'poisson_membrane':
            eps, nu = case['epsilon'], case['nu']
            return np.stack((eps * X, -nu * eps * y, -nu * eps * z), axis=-1)
        if name == 'in_plane_shear':
            gamma = case['gamma']
            return np.stack((gamma * y / 2, gamma * X / 2, zero), axis=-1)
        if name == 'transverse_shear':
            gamma = case['gamma']
            return np.stack((gamma * z / 2, zero, gamma * X / 2), axis=-1)
        a = case['curvature']
        return np.stack((a * y * z, a * X * z, -a * X * y), axis=-1)

    def shell(x):
        displacement = solid(np.asarray(x))
        rotations = np.zeros(3)
        if name == 'transverse_shear':
            rotations[1] = case['gamma'] / 2
        elif name == 'twist':
            rotations[:2] = [-case['curvature'] * (x[0] + 1.), case['curvature'] * (x[1] - .5)]
        return np.concatenate((displacement, rotations))
    return solid, shell


def native_edge_load(native, load, axis, coordinate, *, force=(0., 0., 0.), moment=(0., 0., 0.)):
    """Consistent constant Q4 boundary line forces/moments: half per end."""
    count = 0
    for element in native.mesh.elements.values():
        nodes = [native.mesh.nodes[nid] for nid in element.node_ids]
        selected = [node for node in nodes if abs(node.coords()[axis] - coordinate) < 1e-12]
        if len(selected) != 2:
            continue
        edge_length = float(np.linalg.norm(selected[1].coords() - selected[0].coords()))
        for node in selected:
            load.add_nodal_load(node.id, forces=np.asarray(force) * edge_length / 2,
                                moments=np.asarray(moment) * edge_length / 2)
        count += 1
    if not count:
        raise ValueError('registered native external edge load selected no edges')


def patch_case(fixture, coupling_manifest, patch_manifest, name):
    case = patch_manifest['cases'][name]
    geometry = patch_manifest['geometry']
    E, t = patch_manifest['E'], geometry['thickness']
    specimen_manifest = json.loads(json.dumps(coupling_manifest))
    specimen_manifest['material'].update(E_Pa=E, nu=case['nu'])
    solid_field, shell_field = exact_patch_fields(name, case)
    native, backend, operators, _, dimensions = setup_case(fixture, geometry['nshell'],
        geometry['nsolid'], t, specimen_manifest, prescribed_field=shell_field, extra_surface_groups=True)
    if dimensions['primary_dofs'] > patch_manifest['bounds']['maximum_primary_dofs']:
        raise ValueError('physical patch primary DOF bound exceeded')
    load = LoadCase(name)
    solid_load = np.zeros(backend.ndof)
    if name == 'poisson_membrane':
        native_edge_load(native, load, 0, 2., force=(case['F'] / geometry['width'], 0., 0.))
    elif name == 'in_plane_shear':
        tau = case['tau']
        native_edge_load(native, load, 0, 2., force=(0., tau * t, 0.))
        for side, sign in ((0, -1), (1, 1)):
            native_edge_load(native, load, 1, float(side), force=(sign * tau * t, 0., 0.))
            solid_load += backend.traction(f'y{side}', [sign * tau, 0., 0.])
    elif name == 'transverse_shear':
        tau = case['tau']
        native_edge_load(native, load, 0, 2., force=(0., 0., tau * t))
        for side, sign in ((0, -1), (1, 1)):
            solid_load += backend.traction(f'z{side}', [sign * tau, 0., 0.])
        for element in native.mesh.elements.values():
            coords = element.get_node_coordinates(native.mesh)
            area = float(np.ptp(coords[:, 0]) * np.ptp(coords[:, 1]))
            for nid in element.node_ids:
                load.add_nodal_load(nid, moments=[0., tau * t * area / 4, 0.])
    elif name == 'twist':
        moment = E * case['curvature'] * t**3 / 12
        native_edge_load(native, load, 0, 2., moment=(-moment, 0., 0.))
        for side, sign in ((0, -1), (1, 1)):
            native_edge_load(native, load, 1, float(side), moment=(0., sign * moment, 0.))
            gradient = np.zeros((3, 3))
            gradient[0, 2] = sign * E * case['curvature']
            solid_load += backend.traction(f'y{side}', [0., 0., 0.], gradient=gradient)
    else:
        raise ValueError(f'unsupported registered physical patch {name}')
    refs = ResidualScales(**case['scales'])
    model = SolidModel(native, research_coupling=True, residual_scales={name: refs})
    region = model.add_region('solid', prepared=backend)
    region.set_load(name, solid_load)
    for operator in operators:
        model.add_interface('solid', operator)
    try:
        result = model.solve_static((name,), native_load_cases={name: load})
    except Exception as exc:
        emit({'type': 'solve_failure', 'case': name, 'error_type': type(exc).__name__,
              'error': str(exc), 'diagnostics': getattr(exc, 'diagnostics', None)})
        raise
    native_u = result.native_displacements[:, 0]
    solid_u = result.region_coefficients('solid')[:, 0]
    native_exact = np.zeros_like(native_u)
    displacement_indices, rotation_indices = [], []
    for node in native.mesh.nodes.values():
        dofs = native.mesh.dof_manager.get_node_dofs(node.id)
        native_exact[dofs] = shell_field(node.coords())
        displacement_indices.extend(dofs[:3])
        rotation_indices.extend(dofs[3:])
    displacement_error = float(np.max(abs(native_u[displacement_indices] - native_exact[displacement_indices])) / refs.displacement)
    rotation_error = float(refs.length * np.max(abs(native_u[rotation_indices] - native_exact[rotation_indices])) / refs.displacement)
    Ksh, _ = assemble_stiffness_matrix(native)
    native_energy = float(native_u @ Ksh @ native_u)
    solid_energy = float(solid_u @ backend.assemble_linear() @ solid_u)
    energy = native_energy + solid_energy
    recovery = backend.recover(solid_u)
    select = (recovery.coordinates[..., 0] >= .25) & (recovery.coordinates[..., 0] <= .75)
    if not np.any(select):
        raise ValueError('physical patch stress sampling selected no points')
    coordinates, stress = recovery.coordinates[select], recovery.stress[select]
    exact_stress = np.zeros_like(stress)
    if name == 'poisson_membrane':
        exact_stress[:, 0, 0] = case['stress_scale']
    elif name in ('in_plane_shear', 'transverse_shear'):
        axis = 1 if name == 'in_plane_shear' else 2
        exact_stress[:, 0, axis] = exact_stress[:, axis, 0] = case['tau']
    else:
        exact_stress[:, 0, 1] = exact_stress[:, 1, 0] = E * case['curvature'] * coordinates[:, 2]
    energy_error = float(abs(energy - case['twice_energy']) / case['twice_energy'])
    stress_error = float(np.max(abs(stress - exact_stress)) / case['stress_scale'])
    thresholds = patch_manifest['thresholds']
    checks = {'native_field': max(displacement_error, rotation_error) <= thresholds['nodal_displacement_rotation_relative'],
              'energy': energy_error <= thresholds['global_energy_relative'],
              'stress': stress_error <= thresholds['interior_stress_max_scaled'],
              'registered_residuals': result.diagnostics['registered_residual_report']['passed']}
    coefficient_exact = solid_field(backend.coefficient_coordinates)[np.arange(backend.ndof), backend.coefficient_components]
    return {'type': 'case_result', 'case': name, 'family': 'physical_patch',
            'passed': bool(all(checks.values())), 'checks': checks, **dimensions,
            'qualification': 'research_only_NO_GO_PRODUCTION_UNQUALIFIED', 'reference': case,
            'native_displacement_error_scaled': displacement_error, 'native_rotation_error_scaled': rotation_error,
            'energy_twice_Nm': energy, 'native_energy_twice_Nm': native_energy, 'solid_energy_twice_Nm': solid_energy,
            'energy_relative_error': energy_error, 'stress_max_scaled_error': stress_error,
            'solid_coefficient_error_scaled_diagnostic': float(np.max(abs(solid_u - coefficient_exact)) / refs.displacement),
            'native_coefficients': native_u.tolist(), 'native_reference_coefficients': native_exact.tolist(),
            'stress_coordinates': coordinates.tolist(), 'stress_tensors': stress.tolist(),
            'stress_reference_tensors': exact_stress.tolist(),
            'registered_residual_report': result.diagnostics['registered_residual_report'],
            'legacy_componentwise_constraint_error': result.diagnostics['legacy_componentwise_constraint_error'],
            'constitutive_contract_note': 'native Q4 uses transverse shear factor 5/6; uniform 3D shear patch may mismatch' if name == 'transverse_shear' else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('bending', 'spectrum', 'patches', 'all'), required=True)
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    patch_manifest = json.loads(PATCH_MANIFEST.read_text(encoding='utf-8')) if args.case in ('patches', 'all') else None
    emit({'type': 'run_identity', 'requested_case': args.case,
          'manifest_path': str(MANIFEST), 'manifest_sha256': hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
          'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'fixture_path': str(FIXTURE), 'fixture_sha256': hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
          'versions': {'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__, 'skfem': skfem.__version__},
          'production_status': 'NO_GO_PRODUCTION_UNQUALIFIED'})
    if patch_manifest is not None:
        emit({'type': 'physical_patch_identity', 'manifest_path': str(PATCH_MANIFEST),
              'manifest_sha256': hashlib.sha256(PATCH_MANIFEST.read_bytes()).hexdigest(),
              'manifest': patch_manifest})
    fixture = import_fixture()
    requests = [('bending', None)] if args.case == 'bending' else []
    if args.case == 'all':
        requests.append(('bending', None))
    if args.case in ('spectrum', 'all'):
        requests.extend(('spectrum', tuple(case)) for case in manifest['stability_diagnostic']['cases_nshell_nsolid_thickness'])
    if args.case in ('patches', 'all'):
        requests.extend(('physical_patch', name) for name in patch_manifest['cases'])
    failed = 0
    executed = 0
    withheld = 0
    for kind, parameters in requests:
        started = time.perf_counter()
        emit({'type': 'case_start', 'case': kind, 'parameters': parameters})
        if kind == 'physical_patch':
            status = patch_manifest['cases'][parameters].get('execution_status')
            if status == 'NOT_EXECUTED_CONSTITUTIVE_MISMATCH':
                withheld += 1
                emit({'type': 'case_not_executed', 'case': parameters,
                      'status': status, 'passed': False, 'qualification': 'NOT_QUALIFIED',
                      'reference': patch_manifest['cases'][parameters],
                      'source': 'ANYsolver/src/anysolver/e4_pl_element.py:5473',
                      'constitutive': 'As=(5/6)*thickness*G',
                      'registered_uniform_shear_resultant_N': .2,
                      'native_exact_field_shear_resultant_N': 1 / 6,
                      'reason': 'registered uniform 3D shear reference is incompatible with production Q4 transverse shear constitutive law'})
                continue
        executed += 1
        try:
            if kind == 'bending':
                record = bending_case(fixture, manifest)
            elif kind == 'spectrum':
                record = spectrum_case(fixture, manifest, *parameters)
            else:
                record = patch_case(fixture, manifest, patch_manifest, parameters)
            record['process_case_wall_seconds'] = time.perf_counter() - started
            emit(record)
            failed += int(not record.get('passed', record.get('diagnostic_completed', False)))
        except Exception as exc:
            failed += 1
            emit({'type': 'case_failure', 'case': kind, 'parameters': parameters,
                  'error_type': type(exc).__name__, 'error': str(exc),
                  'process_case_wall_seconds': time.perf_counter() - started})
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
    emit({'type': 'run_summary', 'requested_cases': len(requests), 'executed_cases': executed,
          'withheld_cases': withheld, 'failures': failed,
          'executed_cases_passed': failed == 0, 'passed': failed == 0 and withheld == 0,
          'production_status': 'NO_GO_PRODUCTION_UNQUALIFIED'})
    return int(failed != 0)


if __name__ == '__main__':
    raise SystemExit(main())
