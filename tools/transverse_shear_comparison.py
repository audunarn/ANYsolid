"""Three-level registered engineering comparison, not an exact coupled patch."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from collections.abc import Mapping
import sys
import time
import traceback
import numpy as np
import scipy
import skfem
from skfem import MeshTet
from anysolid import SolidMesh, prepare
from anysolid.coupling import build_weak_connector
from anysolver import FEModel, BoundaryCondition, LoadCase, assemble_stiffness_matrix
from anysolver.elements import create_shell_element
from anysolver.solid_trace import ShellEdgeTrace
from anysolver.solids import SolidModel, ResidualScales


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'docs/transverse_shear_comparison_manifest.json'


def json_value(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(f'unsupported JSON diagnostic {type(value).__name__}')


def emit(record):
    print(json.dumps(record, default=json_value, allow_nan=False, sort_keys=True), flush=True)


def specimen(manifest, level):
    geometry, material = manifest['geometry'], manifest['material']
    t, width = geometry['thickness_m'], geometry['width_m']
    axial = level['native_axial_elements_per_side']
    native = FEModel('registered-transverse-engineering-comparison')
    native.add_material('m', material['E_Pa'], material['nu'])
    edges, clamp, tip = [], [], []
    for side, ends in enumerate(((geometry['left_x'], geometry['solid_x'][0]),
                                  (geometry['solid_x'][1], geometry['right_x']))):
        nodes = {}
        for j, y in enumerate((0., width)):
            for i, x in enumerate(np.linspace(*ends, axial + 1)):
                nid = len(native.mesh.nodes) + 1
                native.add_node(nid, float(x), float(y), 0.)
                nodes[i, j] = nid
                if side == 0 and i == 0:
                    clamp.append(nid)
                if side == 1 and i == axial:
                    tip.append(nid)
        for i in range(axial):
            eid = len(native.mesh.elements) + 1
            # Same production Q4 CCW xy ordering and physical +z director.
            ids = [nodes[i, 0], nodes[i + 1, 0], nodes[i + 1, 1], nodes[i, 1]]
            native.add_element(eid, create_shell_element(eid, ids, 'm', thickness=t,
                                                        reference_normal=(0., 0., 1.)))
            if side == 0 and i == axial - 1:
                edges.append((eid, 1))
            if side == 1 and i == 0:
                edges.append((eid, 3))
    raw = MeshTet.init_tensor(
        np.linspace(*geometry['solid_x'], level['solid_nx'] + 1),
        np.linspace(0., width, level['solid_ny'] + 1),
        np.linspace(-t / 2, t / 2, level['solid_nz'] + 1)).oriented()
    initial = SolidMesh(raw.p.T, raw.t.T)
    facet_x = initial.coordinates[initial.boundary_facets, 0]
    groups = {name: initial.boundary_ids[np.all(abs(facet_x - xpos) < 1e-12, axis=1)]
              for name, xpos in zip(('left', 'right'), geometry['solid_x'])}
    backend = prepare(SolidMesh(initial.coordinates, initial.cells, boundary_groups=groups,
        provenance={'case': 'registered-transverse-comparison', 'level': level}),
        {'elastic_modulus': material['E_Pa'], 'poisson_ratio': material['nu']})
    left = ShellEdgeTrace(native, [edges[0]])
    right = ShellEdgeTrace(native, [edges[1]])
    if backend.elastic_modulus != material['E_Pa'] or backend.poisson_ratio != material['nu']:
        raise ValueError('constructed backend material differs from reference')
    if left.thickness != t or right.thickness != t:
        raise ValueError('constructed trace thickness differs from reference')
    native.add_boundary_condition(BoundaryCondition(name='clamp', node_ids=clamp,
        dof_constraints={key: 0. for key in ('ux', 'uy', 'uz', 'rx', 'ry', 'rz')}))
    operators = [build_weak_connector(trace, backend, name, multiplier_breakpoints=[0., width])
                 for trace, name in ((left, 'left'), (right, 'right'))]
    nprimary = native.mesh.dof_manager.total_dofs + backend.ndof
    nlambda = sum(op.C_shell.shape[0] for op in operators)
    if nprimary > manifest['bounds']['maximum_primary_dofs'] or nlambda > manifest['bounds']['maximum_multiplier_rows']:
        raise ValueError(f'registered dimension bound exceeded: primary={nprimary}, multipliers={nlambda}')
    return native, backend, operators, tip, int(nprimary), int(nlambda)


def reference_fields(coordinates, manifest):
    geometry, material = manifest['geometry'], manifest['material']
    Q, kappa = manifest['force_N'], manifest['shear_correction']
    E, G = material['E_Pa'], material['G_Pa']
    t, width, L = geometry['thickness_m'], geometry['width_m'], geometry['span_m']
    A, I = width * t, width * t**3 / 12
    coordinates = np.asarray(coordinates)
    xi = coordinates[..., 0] - geometry['left_x']
    z = coordinates[..., 2]
    theta = Q / (E * I) * (xi**2 / 2 - L * xi)
    w = Q * xi / (kappa * G * A) - Q / (E * I) * (xi**3 / 6 - L * xi**2 / 2)
    warp = Q / (G * A) * ((1.5 - 1 / kappa) * z - 2 * z**3 / t**2)
    displacement = np.stack((theta * z + warp, np.zeros_like(w), w), axis=-1)
    stress = np.zeros((*xi.shape, 3, 3))
    stress[..., 0, 0] = Q * (xi - L) * z / I
    stress[..., 0, 2] = stress[..., 2, 0] = 1.5 * Q / A * (1 - 4 * z**2 / t**2)
    return displacement, theta, stress


def stress_errors(actual, expected, mask, manifest):
    if not np.any(mask):
        raise ValueError('prospective stress region selected no quadrature points')
    difference = abs(actual[mask] - expected[mask])
    axial_scale = manifest['scales']['axial_stress_Pa']
    shear_scale = manifest['scales']['shear_stress_Pa']
    other = np.ones((3, 3), dtype=bool)
    other[0, 0] = other[0, 2] = other[2, 0] = False
    return {'sample_count': int(mask.sum()),
            'axial_xx_scaled_max': float(difference[:, 0, 0].max() / axial_scale),
            'shear_xz_zx_scaled_max': float(difference[:, [0, 2], [2, 0]].max() / shear_scale),
            'other_stress_components_max_Pa': float(abs(actual[mask][:, other]).max()),
            'all_component_absolute_error_max_Pa': difference.max(axis=0).tolist()}


def run_level(index, level, manifest):
    native, backend, operators, tip, nprimary, nlambda = specimen(manifest, level)
    refs = manifest['scales']
    scales = ResidualScales(refs['length_m'], refs['force_N'], refs['displacement_m'],
                            tuple(refs['interface_displacements_m']))
    load = LoadCase('transverse_comparison')
    # One width edge, Q4 constant line force: half the total at each endpoint.
    for nid in tip:
        load.add_nodal_load(nid, forces=[0., 0., manifest['force_N'] / 2])
    if len(tip) != 2:
        raise ValueError('registered one-Q4-wide tip requires exactly two edge nodes')
    model = SolidModel(native, research_coupling=True, residual_scales={'transverse_comparison': scales})
    model.add_region('solid', prepared=backend)
    for operator in operators:
        model.add_interface('solid', operator)
    try:
        result = model.solve_static(('transverse_comparison',), native_load_cases={'transverse_comparison': load})
    except Exception as exc:
        emit({'type': 'solve_failure', 'level_index': index, 'level': level,
              'error_type': type(exc).__name__, 'error': str(exc),
              'diagnostics': getattr(exc, 'diagnostics', None)})
        raise
    native_u, solid_u = result.native_displacements[:, 0], result.region_coefficients('solid')[:, 0]
    dofs = [native.mesh.dof_manager.get_node_dofs(nid) for nid in tip]
    w = np.array([native_u[dof[2]] for dof in dofs])
    theta = np.array([native_u[dof[4]] for dof in dofs])
    Ksh, _ = assemble_stiffness_matrix(native)
    native_energy = float(native_u @ Ksh @ native_u)
    solid_energy = float(solid_u @ backend.assemble_linear() @ solid_u)
    energy = native_energy + solid_energy
    reference = manifest['reference']
    global_errors = {
        'tip_w_relative': float(np.max(abs(w - reference['tip_w_m'])) / abs(reference['tip_w_m'])),
        'tip_theta_y_relative': float(np.max(abs(theta - reference['tip_theta_y_rad'])) / abs(reference['tip_theta_y_rad'])),
        'energy_twice_relative': float(abs(energy - reference['twice_energy_Nm']) / reference['twice_energy_Nm'])}
    recovery = backend.recover(solid_u)
    exact_displacement, _, exact_stress = reference_fields(recovery.coordinates, manifest)
    interior = (recovery.coordinates[..., 0] >= .25) & (recovery.coordinates[..., 0] <= .75)
    interior_errors = stress_errors(recovery.stress, exact_stress, interior, manifest)
    interface_errors = stress_errors(recovery.stress, exact_stress, ~interior, manifest)
    native_field_diagnostic = []
    for node in native.mesh.nodes.values():
        physical, rotation, _ = reference_fields(node.coords(), manifest)
        exact = np.r_[physical, [0., rotation, 0.]]
        ndofs = native.mesh.dof_manager.get_node_dofs(node.id)
        dimensional = abs(native_u[ndofs] - exact) * np.r_[np.ones(3), np.full(3, scales.length)]
        native_field_diagnostic.append(float(dimensional.max() / scales.displacement))
    coefficient_exact = reference_fields(backend.coefficient_coordinates, manifest)[0]
    coefficient_exact = coefficient_exact[np.arange(backend.ndof), backend.coefficient_components]
    acceptance = manifest['acceptance']
    residual_report = result.diagnostics['registered_residual_report']
    checks = {
        **{name: value <= acceptance['finest_tip_w_rotation_energy_relative_max'] for name, value in global_errors.items()},
        'axial_stress': interior_errors['axial_xx_scaled_max'] <= acceptance['finest_axial_and_shear_component_error_max'],
        'shear_stress': interior_errors['shear_xz_zx_scaled_max'] <= acceptance['finest_axial_and_shear_component_error_max'],
        'registered_residuals': bool(residual_report['passed'])}
    finest = index == len(manifest['levels']) - 1
    return {'type': 'level_result', 'level_index': index, 'level': level,
            'primary_dofs': nprimary, 'multiplier_rows': nlambda,
            'acceptance_role': 'finest_engineering_comparison' if finest else 'coarse_diagnostic_only',
            'passed': bool(all(checks.values())) if finest else None,
            'meets_finest_targets_diagnostic': bool(all(checks.values())), 'checks': checks,
            'tip_w_m': w.tolist(), 'tip_theta_y_rad': theta.tolist(),
            'native_energy_twice_Nm': native_energy, 'solid_energy_twice_Nm': solid_energy,
            'energy_twice_Nm': energy, 'applied_work_Nm': float(manifest['force_N'] * w.mean()),
            'global_errors': global_errors, 'interior_stress_errors': interior_errors,
            'interface_layer_stress_errors_diagnostic': interface_errors,
            'native_full_node_field_error_scaled_diagnostic': max(native_field_diagnostic),
            'solid_coefficient_error_scaled_diagnostic': float(np.max(abs(solid_u - coefficient_exact)) / scales.displacement),
            'stress_sample_coordinates_m': recovery.coordinates.tolist(),
            'actual_stress_tensors_Pa': recovery.stress.tolist(),
            'reference_stress_tensors_Pa': exact_stress.tolist(),
            'interior_sample_mask': interior.tolist(),
            'registered_residual_report': residual_report,
            'legacy_componentwise_constraint_error': result.diagnostics['legacy_componentwise_constraint_error'],
            'qualification': 'ENGINEERING_COMPARISON_ONLY_NO_GO_PRODUCTION',
            'known_model_discrepancy': manifest['known_model_discrepancy']}


def main():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    fixture = ROOT.parent / 'ANYsolver/tests/test_solid_coupling.py'
    emit({'type': 'run_identity', 'manifest_path': str(MANIFEST),
          'manifest_sha256': hashlib.sha256(MANIFEST.read_bytes()).hexdigest(), 'manifest': manifest,
          'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'inspected_fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
          'versions': {'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__, 'skfem': skfem.__version__},
          'production_status': 'NO_GO_PRODUCTION_UNQUALIFIED'})
    failures = 0
    results = []
    for index, level in enumerate(manifest['levels']):
        emit({'type': 'level_start', 'level_index': index, 'level': level})
        started = time.perf_counter()
        try:
            record = run_level(index, level, manifest)
            record['level_wall_seconds'] = time.perf_counter() - started
            emit(record)
            results.append(record)
        except Exception as exc:
            failures += 1
            emit({'type': 'level_failure', 'level_index': index, 'level': level,
                  'error_type': type(exc).__name__, 'error': str(exc),
                  'level_wall_seconds': time.perf_counter() - started})
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
    finest = next((r for r in results if r['level_index'] == len(manifest['levels']) - 1), None)
    passed = failures == 0 and finest is not None and finest['passed']
    emit({'type': 'run_summary', 'levels_requested': len(manifest['levels']),
          'levels_completed': len(results), 'execution_failures': failures,
          'finest_meets_registered_targets': bool(passed),
          'status': 'BOUNDED_ENGINEERING_COMPARISON_TARGETS_MET' if passed else 'SCIENTIFIC_NO_GO',
          'global_error_trend': [r['global_errors'] for r in results],
          'interior_stress_error_trend': [r['interior_stress_errors'] for r in results],
          'interpretation': 'discretization trends may include persistent interface modeling error; no inferred exact coupled reference',
          'production_status': 'NO_GO_PRODUCTION_UNQUALIFIED'})
    return int(not passed)


if __name__ == '__main__':
    raise SystemExit(main())
