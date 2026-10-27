"""Two prospective matched solid-control/coupled pairs, production NO_GO."""
from __future__ import annotations
from collections.abc import Mapping
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback
import numpy as np
import scipy
from scipy import sparse
import skfem
from anysolver import LoadCase, assemble_stiffness_matrix
from anysolver.solids import SolidModel, ResidualScales


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'docs/paired_axial_manifest.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_value(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(f'unsupported JSON diagnostic {type(value).__name__}')


def emit(record):
    print(json.dumps(record, allow_nan=False, default=json_value, sort_keys=True), flush=True)


def load_references(manifest):
    resolve = lambda name: (MANIFEST.parent / manifest[name]).resolve()
    isolation_path, isolation_manifest_path = resolve('isolation_harness'), resolve('isolation_manifest')
    if sha(isolation_path) != manifest['isolation_harness_sha256']:
        raise ValueError('isolation measurement-helper source identity changed')
    prior_control = resolve('prior_control_evidence')
    with (prior_control / 'stdout.jsonl').open(encoding='utf-8') as stream:
        prior_identity = json.loads(stream.readline())
    if sha(isolation_manifest_path) != prior_identity['manifest_sha256']:
        raise ValueError('isolation measurement-helper manifest identity changed')
    isolation_manifest = json.loads(isolation_manifest_path.read_text(encoding='utf-8'))
    spec = importlib.util.spec_from_file_location('_paired_isolation_measurements', isolation_path)
    isolation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(isolation)
    reference, reference_manifest, _, reference_identity = isolation.load_reference(isolation_manifest)
    if (sha(resolve('reference_harness')) != manifest['reference_harness_sha256']
            or sha(resolve('reference_manifest')) != manifest['reference_manifest_sha256']
            or sha(resolve('reference_harness')) != reference_identity['reference_harness_sha256']
            or sha(resolve('reference_manifest')) != reference_identity['reference_manifest_sha256']):
        raise ValueError('paired analytical reference source/manifest identity mismatch')
    fixed = manifest['fixed_accuracy']
    refs = reference_manifest['scales']
    if (fixed['axial_stress_scale_Pa'] != refs['axial_stress_Pa']
            or fixed['shear_stress_scale_Pa'] != refs['shear_stress_Pa']
            or fixed['stress_scaled_max'] != isolation_manifest['acceptance']['retained_shear_accuracy_limit']
            or fixed['registered_residuals_max'] != reference_manifest['acceptance']['registered_residuals_max']):
        raise ValueError('paired policy differs from retained measurement/reference definitions')
    derived = copy.deepcopy(reference_manifest)
    derived['levels'] = copy.deepcopy(manifest['levels'])
    derived['bounds']['maximum_primary_dofs'] = manifest['bounds']['maximum_primary_dofs']
    derived['bounds']['maximum_multiplier_rows'] = manifest['bounds']['maximum_multiplier_rows']
    if derived['bounds']['process_tree_timeout_seconds'] != manifest['bounds']['process_tree_timeout_seconds']:
        raise ValueError('derived process bound differs from paired authority')
    return isolation, isolation_manifest, reference, reference_manifest, derived, {
        **reference_identity, 'isolation_harness_path': str(isolation_path),
        'isolation_harness_sha256': sha(isolation_path),
        'isolation_measurement_manifest_path': str(isolation_manifest_path),
        'isolation_measurement_manifest_sha256': sha(isolation_manifest_path),
        'prior_control_evidence': str(prior_control),
        'prior_control_identity_sha256': sha(prior_control / 'identity.json'),
        'helper_role': 'read-only geometry/reference/measurement reuse; no prior numerical authority reused',
        'derived_configuration': derived,
        'derived_configuration_changes': {
            'levels': {'retained': reference_manifest['levels'], 'paired': derived['levels']},
            'maximum_primary_dofs': {'retained': reference_manifest['bounds']['maximum_primary_dofs'],
                                     'paired': derived['bounds']['maximum_primary_dofs']}},
        'execution_authority': str(MANIFEST)}


def matrix_storage(matrix):
    matrix = sparse.csr_matrix(matrix)
    return {'shape': [int(n) for n in matrix.shape], 'nnz': int(matrix.nnz),
            'format': 'csr', 'dtype': str(matrix.dtype),
            'data_bytes': int(matrix.data.nbytes), 'indices_bytes': int(matrix.indices.nbytes),
            'indptr_bytes': int(matrix.indptr.nbytes),
            'csr_array_storage_bytes': int(matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes),
            'meaning': 'stored matrix arrays only; excludes factors, Python overhead and process RSS'}


def pointwise_difference(control, coupled, isolation, isolation_manifest, reference, reference_manifest):
    coordinates = np.asarray(control['coordinates_m'])
    coupled_coordinates = np.asarray(coupled['coordinates_m'])
    mask = np.asarray(control['fixed_interior_mask'])
    if not np.array_equal(coordinates, coupled_coordinates) or not np.array_equal(mask, coupled['fixed_interior_mask']):
        raise ValueError('paired physical quadrature coordinates or fixed sampling masks differ')
    c, v = np.asarray(control['actual_stress_Pa']), np.asarray(coupled['actual_stress_Pa'])
    delta = v - c
    metrics = reference.stress_errors(delta, np.zeros_like(delta), mask, reference_manifest)
    witnesses = isolation.controlling_points(v, c, coordinates, mask, isolation_manifest)
    for witness in witnesses.values():
        witness['coupled_Pa'] = witness.pop('actual_Pa')
        witness['control_Pa'] = witness.pop('reference_Pa')
        witness['coupled_minus_control_Pa'] = witness['coupled_Pa'] - witness['control_Pa']
    return {'exact_same_quadrature_coordinates': True, 'exact_same_interior_mask': True,
            'pointwise_delta_errors': metrics, 'pointwise_delta_controlling_points': witnesses,
            'meaning': 'coupled-minus-control tensors evaluated pointwise, not difference of maxima',
            'coordinates_m': coordinates.tolist(), 'fixed_interior_mask': mask.tolist(),
            'pointwise_coupled_minus_control_stress_Pa': delta.tolist()}


def coupled_global_metrics(native, prepared, result, tip, Ksh, Kv, reference_manifest):
    native_u, solid_u = result.native_displacements[:, 0], result.region_coefficients('solid')[:, 0]
    dofs = [native.mesh.dof_manager.get_node_dofs(nid) for nid in tip]
    w = np.array([native_u[d[2]] for d in dofs])
    theta = np.array([native_u[d[4]] for d in dofs])
    energy_native, energy_solid = float(native_u @ Ksh @ native_u), float(solid_u @ Kv @ solid_u)
    energy = energy_native + energy_solid
    refs = reference_manifest['reference']
    errors = {
        'tip_w_relative': float(np.max(abs(w - refs['tip_w_m'])) / abs(refs['tip_w_m'])),
        'tip_theta_y_relative': float(np.max(abs(theta - refs['tip_theta_y_rad'])) / abs(refs['tip_theta_y_rad'])),
        'energy_twice_relative': float(abs(energy - refs['twice_energy_Nm']) / refs['twice_energy_Nm'])}
    return {'tip_w_m': w.tolist(), 'tip_theta_y_rad': theta.tolist(),
            'native_energy_twice_Nm': energy_native, 'solid_energy_twice_Nm': energy_solid,
            'energy_twice_Nm': energy, 'external_work_Nm': float(reference_manifest['force_N'] * w.mean()),
            'global_errors': errors, 'native_coefficients': native_u.tolist()}


def main():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    emit({'type': 'run_identity', 'manifest_path': str(MANIFEST), 'manifest_sha256': sha(MANIFEST),
          'manifest': manifest, 'harness_sha256': sha(__file__),
          'versions': {'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__, 'skfem': skfem.__version__},
          'production_status': 'NO_GO_PRODUCTION_UNQUALIFIED'})
    isolation, isolation_manifest, reference, ref_manifest, derived, reference_identity = load_references(manifest)
    emit({'type': 'reference_and_derived_configuration', **reference_identity,
          'module_identities': isolation.module_identities()})
    levels = manifest['levels']
    if len(levels) != 2 or 2 * len(levels) != manifest['bounds']['maximum_solves']:
        raise ValueError('registered two-pair/four-solve count mismatch')
    ref_scales = ref_manifest['scales']
    control_scales = ResidualScales(ref_scales['length_m'], ref_scales['force_N'], ref_scales['displacement_m'])
    coupled_scales = ResidualScales(ref_scales['length_m'], ref_scales['force_N'], ref_scales['displacement_m'],
                                    tuple(ref_scales['interface_displacements_m']))
    solves = 0
    summaries = []
    failures = 0
    for level in levels:
        emit({'type': 'pair_start', 'level': level, 'authority': str(MANIFEST)})
        started = time.perf_counter()
        try:
            native, prepared, operators, tip, nprimary, nlambda = reference.specimen(derived, level)
            signature = prepared.cache_signature()
            if nprimary > manifest['bounds']['maximum_primary_dofs'] or nlambda > manifest['bounds']['maximum_multiplier_rows']:
                raise ValueError('paired specimen dimension bound exceeded')
            if len(operators) != 2 or any(op.metadata['section_modes'] != 5 for op in operators):
                raise ValueError('paired specimen must retain two five-mode interfaces')
            if len(tip) != 2:
                raise ValueError('one-Q4-wide right edge requires two load nodes')
            Kv, Ksh = prepared.assemble_linear(), assemble_stiffness_matrix(native)[0]
            C = sparse.vstack([sparse.hstack((op.C_shell, -op.C_solid)) for op in operators], format='csr')
            fixed = np.unique(np.concatenate([prepared.boundary_dofs(side) for side in ('left', 'right')]))
            free = np.setdiff1d(np.arange(prepared.ndof), fixed)
            storage = {'solid_stiffness': matrix_storage(Kv), 'native_stiffness': matrix_storage(Ksh),
                       'physical_interface_operator': matrix_storage(C),
                       'control_reduced_stiffness': matrix_storage(Kv[free][:, free])}
            emit({'type': 'pair_specimen', 'level': level, 'primary_dofs': nprimary,
                  'solid_dofs': int(prepared.ndof), 'native_dofs': Ksh.shape[0], 'multiplier_rows': nlambda,
                  'same_prepared_solid_identity': signature, 'matrix_storage': storage,
                  'mesh_coordinates_m': prepared.mesh.coordinates.tolist(), 'cells': prepared.mesh.cells.tolist(),
                  'coefficient_coordinates_m': prepared.coefficient_coordinates.tolist(),
                  'coefficient_components': prepared.coefficient_components.tolist()})
            exact_values = reference.reference_fields(prepared.coefficient_coordinates, ref_manifest)[0]
            exact_coefficients = exact_values[np.arange(prepared.ndof), prepared.coefficient_components]
            control_model = SolidModel(residual_scales={'control': control_scales})
            control_region = control_model.add_region('solid', prepared=prepared)
            control_region.prescribe_dofs(fixed, exact_coefficients[fixed])
            control_region.set_load('control', np.zeros(prepared.ndof))
            emit({'type': 'solve_start', 'level': level, 'route': 'control', 'solve_number': solves + 1,
                  'fixed_coefficient_count': len(fixed), 'registered_scales': vars(control_scales),
                  'prepared_signature': signature, 'interfaces': 0, 'loads': 'zero'})
            if solves >= manifest['bounds']['maximum_solves']:
                raise ValueError('four-solve authority exhausted')
            solves += 1
            try:
                control_result = control_model.solve_static(('control',))
            except Exception as exc:
                emit({'type': 'solve_failure', 'level': level, 'route': 'control',
                      'error': str(exc), 'diagnostics': getattr(exc, 'diagnostics', None)})
                raise
            control_u = control_result.region_coefficients('solid')[:, 0]
            control = isolation.stress_record('control', prepared, control_u, reference, ref_manifest, isolation_manifest)
            control_report = control_result.diagnostics['registered_residual_report']
            control_flags = {**control['accuracy_diagnostics'], 'registered_residuals': control_report['passed']}
            control_passed = bool(all(control_flags.values()))
            if prepared.cache_signature() != signature:
                raise ValueError('control changed the shared immutable prepared solid')
            emit({'type': 'control_result', 'level': level, **control,
                  'passed_registered_diagnostics': control_passed, 'checks': control_flags,
                  'registered_residual_report': control_report,
                  'energy_twice_Nm_diagnostic': float(control_u @ Kv @ control_u),
                  'end_support_resultants': isolation.end_reactions(prepared, control_u, isolation_manifest, ref_manifest),
                  'prepared_signature_after_solve': prepared.cache_signature()})
            load = LoadCase('coupled')
            for nid in tip:
                load.add_nodal_load(nid, forces=[0., 0., ref_manifest['force_N'] / 2])
            coupled_model = SolidModel(native, research_coupling=True, residual_scales={'coupled': coupled_scales})
            coupled_model.add_region('solid', prepared=prepared)
            for operator in operators:
                coupled_model.add_interface('solid', operator)
            if coupled_model.regions['solid'].prepared is not control_region.prepared:
                raise ValueError('paired routes do not share the identical prepared object')
            emit({'type': 'solve_start', 'level': level, 'route': 'coupled', 'solve_number': solves + 1,
                  'registered_scales': vars(coupled_scales), 'prepared_signature': signature,
                  'same_prepared_object_as_control': True, 'interfaces': 2,
                  'right_force_z_N': ref_manifest['force_N'], 'primary_dofs': nprimary, 'multiplier_rows': nlambda})
            if solves >= manifest['bounds']['maximum_solves']:
                raise ValueError('four-solve authority exhausted')
            solves += 1
            try:
                coupled_result = coupled_model.solve_static(('coupled',), native_load_cases={'coupled': load})
            except Exception as exc:
                emit({'type': 'solve_failure', 'level': level, 'route': 'coupled',
                      'error': str(exc), 'diagnostics': getattr(exc, 'diagnostics', None)})
                raise
            coupled_u = coupled_result.region_coefficients('solid')[:, 0]
            coupled = isolation.stress_record('coupled', prepared, coupled_u, reference, ref_manifest, isolation_manifest)
            coupled_report = coupled_result.diagnostics['registered_residual_report']
            global_metrics = coupled_global_metrics(native, prepared, coupled_result, tip, Ksh, Kv, ref_manifest)
            limit = manifest['fixed_accuracy']['coupled_tip_rotation_energy_relative_max']
            coupled_flags = {**coupled['accuracy_diagnostics'],
                             **{key: value <= limit for key, value in global_metrics['global_errors'].items()},
                             'registered_residuals': coupled_report['passed']}
            coupled_passed = bool(all(coupled_flags.values()))
            if prepared.cache_signature() != signature:
                raise ValueError('coupled solve changed the shared immutable prepared solid')
            emit({'type': 'coupled_result', 'level': level, **coupled, **global_metrics,
                  'passed_registered_diagnostics': coupled_passed, 'checks': coupled_flags,
                  'registered_residual_report': coupled_report,
                  'legacy_componentwise_constraint_error': coupled_result.diagnostics['legacy_componentwise_constraint_error'],
                  'prepared_signature_after_solve': prepared.cache_signature(),
                  'production_status': 'NO_GO_PRODUCTION_UNQUALIFIED'})
            delta = pointwise_difference(control, coupled, isolation, isolation_manifest, reference, ref_manifest)
            emit({'type': 'pointwise_paired_difference', 'level': level, **delta,
                  'pair_wall_seconds': time.perf_counter() - started})
            summaries.append({'level': level, 'primary_dofs': nprimary, 'solid_dofs': int(prepared.ndof),
                'multiplier_rows': nlambda, 'matrix_storage': storage,
                'control_analytic_errors': control['stress_errors'], 'coupled_analytic_errors': coupled['stress_errors'],
                'control_flags': control_flags, 'coupled_flags': coupled_flags,
                'control_passed_registered_diagnostics': control_passed,
                'coupled_passed_registered_diagnostics': coupled_passed,
                'coupled_global_errors': global_metrics['global_errors'],
                'pointwise_delta_errors': delta['pointwise_delta_errors'],
                'pointwise_delta_controlling_points': delta['pointwise_delta_controlling_points'],
                'control_normalized_equilibrium': control_report['normalized_equilibrium'],
                'coupled_normalized_equilibrium': coupled_report['normalized_equilibrium'],
                'coupled_normalized_constraint': coupled_report['normalized_constraint_error']})
        except Exception as exc:
            failures += 1
            emit({'type': 'pair_failure', 'level': level, 'error_type': type(exc).__name__,
                  'error': str(exc), 'solves_attempted': solves})
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            # Never consume further solve authority after an implementation or
            # serialization error; retain prefix and report before any repeat.
            break
    emit({'type': 'run_summary', 'pairs_requested': len(levels), 'pairs_completed': len(summaries),
          'solves_attempted': solves, 'execution_failures': failures, 'summaries': summaries,
          'status': 'PAIRED_DIAGNOSTIC_COMPLETE' if failures == 0 else 'PAIRED_DIAGNOSTIC_INCOMPLETE',
          'all_new_coupled_cases_meet_registered_targets': len(summaries) == len(levels) and all(s['coupled_passed_registered_diagnostics'] for s in summaries),
          'interpretation': 'two finite pairs; fixed native4 and end/transition differences prevent unique connector attribution; original failures stay failed',
          'production_status': 'NO_GO_PRODUCTION_UNQUALIFIED'})
    return int(failures != 0)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        emit({'type': 'startup_failure', 'error_type': type(exc).__name__, 'error': str(exc)})
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(1)
