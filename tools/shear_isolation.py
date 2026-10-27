"""Registered solid-only discrimination; retained coupled failure stays NO_GO.

One process evaluates four analytical nodal interpolants and at most four
analytic-end-displacement solid controls. Neither route establishes a best
approximation bound or production qualification.
"""
from __future__ import annotations
from collections.abc import Mapping
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback
import numpy as np
import scipy
import skfem
from skfem import MeshTet
import anysolid.backend
import anysolid.mesh
import anysolver.solids
import anysolver.solid_residuals
from anysolid import SolidMesh, prepare
from anysolver.solids import SolidModel, ResidualScales


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'docs/shear_isolation_manifest.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_value(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(f'unsupported diagnostic JSON value {type(value).__name__}')


def emit(record):
    print(json.dumps(record, allow_nan=False, default=json_value, sort_keys=True), flush=True)


def load_reference(manifest):
    reference_harness = (MANIFEST.parent / manifest['reference_harness']).resolve()
    reference_manifest_path = (MANIFEST.parent / manifest['reference_manifest']).resolve()
    retained = (MANIFEST.parent / manifest['retained_coupled_evidence']).resolve()
    if sha(reference_harness) != manifest['reference_harness_sha256']:
        raise ValueError('registered reference harness identity changed')
    previous_identity = None
    previous_finest = None
    with (retained / 'stdout.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            record = json.loads(line)
            if record['type'] == 'run_identity':
                previous_identity = record
            if record['type'] == 'level_result':
                previous_finest = record
    if previous_identity is None or previous_finest is None:
        raise ValueError('retained coupled reference evidence is incomplete')
    if sha(reference_manifest_path) != previous_identity['manifest_sha256']:
        raise ValueError('registered analytical reference manifest identity changed')
    reference_manifest = json.loads(reference_manifest_path.read_text(encoding='utf-8'))
    for name, expected in manifest['fixed_scales'].items():
        if reference_manifest['scales'][name] != expected:
            raise ValueError(f'isolation scale differs from retained reference: {name}')
    old_sources = json.loads((retained / 'identity.json').read_text(encoding='utf-8'))['source_hashes']
    changes = [{'path': str(path), 'retained_sha256': old, 'current_sha256': sha(path)}
               for path, old in old_sources.items() if sha(path) != old]
    def canonical_change(change):
        return (Path(change['path']).resolve().as_posix().casefold(),
                change['retained_sha256'].lower(), change['current_sha256'].lower())
    allowed_changes = manifest.get('allowed_source_changes')
    if not isinstance(allowed_changes, list):
        raise ValueError('manifest must register exact allowed_source_changes')
    registered = [canonical_change(change) for change in allowed_changes]
    actual = [canonical_change(change) for change in changes]
    if len(set(registered)) != len(registered) or sorted(actual) != sorted(registered):
        raise ValueError(f'source changes differ from exact registered paths/hash pairs: {changes}')
    spec = importlib.util.spec_from_file_location('_retained_transverse_reference', reference_harness)
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    identity = {'reference_harness_path': str(reference_harness),
                'reference_harness_sha256': sha(reference_harness),
                'reference_manifest_path': str(reference_manifest_path),
                'reference_manifest_sha256': sha(reference_manifest_path),
                'retained_coupled_evidence': str(retained),
                'retained_coupled_stdout_sha256': sha(retained / 'stdout.jsonl'),
                'retained_candidate_source_changes': changes,
                'retained_coupled_finest_summary': {
                    key: previous_finest[key] for key in ('level', 'primary_dofs', 'global_errors',
                                                         'interior_stress_errors', 'passed')}}
    return reference, reference_manifest, previous_finest, identity


def controlled_mesh(mesh_spec, manifest, reference_manifest):
    geometry = manifest['geometry']
    raw = MeshTet.init_tensor(
        np.linspace(*geometry['solid_x_m'], mesh_spec['nx'] + 1),
        np.linspace(*geometry['y_m'], mesh_spec['ny'] + 1),
        np.linspace(*geometry['z_m'], mesh_spec['nz'] + 1)).oriented()
    first = SolidMesh(raw.p.T, raw.t.T)
    facet_x = first.coordinates[first.boundary_facets, 0]
    groups = {name: first.boundary_ids[np.all(abs(facet_x - x) < 1e-12, axis=1)]
              for name, x in zip(('left', 'right'), geometry['solid_x_m'])}
    mesh = SolidMesh(first.coordinates, first.cells, boundary_groups=groups,
        provenance={'investigation': 'registered shear isolation', 'mesh': mesh_spec})
    prepared = prepare(mesh, {'elastic_modulus': reference_manifest['material']['E_Pa'],
                             'poisson_ratio': reference_manifest['material']['nu']}, order=2)
    if prepared.ndof > manifest['bounds']['maximum_primary_dofs']:
        raise ValueError('registered primary-DOF bound exceeded')
    if not len(prepared.boundary_dofs('left')) or not len(prepared.boundary_dofs('right')):
        raise ValueError('analytical end groups must select complete nonempty faces')
    return prepared


def controlling_points(actual, expected, coordinates, mask, manifest):
    a, e, x = actual[mask], expected[mask], coordinates[mask]
    difference = abs(a - e)
    witnesses = {}
    for name, components, scale in (
        ('axial', ((0, 0),), manifest['fixed_scales']['axial_stress_Pa']),
        ('shear', ((0, 2), (2, 0)), manifest['fixed_scales']['shear_stress_Pa'])):
        candidates = np.column_stack([difference[:, i, j] for i, j in components])
        sample, component = np.unravel_index(np.argmax(candidates), candidates.shape)
        i, j = components[component]
        witnesses[name] = {'coordinate_m': x[sample].tolist(), 'tensor_component': [int(i), int(j)],
            'actual_Pa': float(a[sample, i, j]), 'reference_Pa': float(e[sample, i, j]),
            'absolute_error_Pa': float(candidates[sample, component]),
            'scaled_error': float(candidates[sample, component] / scale)}
    return witnesses


def stress_record(route, prepared, coefficients, reference, reference_manifest, manifest):
    recovery = prepared.recover(coefficients)
    coordinates = recovery.coordinates
    exact = reference.reference_fields(coordinates, reference_manifest)[2]
    mask = (coordinates[..., 0] >= .25) & (coordinates[..., 0] <= .75)
    errors = reference.stress_errors(recovery.stress, exact, mask, reference_manifest)
    limit = manifest['acceptance']['retained_shear_accuracy_limit']
    return {'route': route, 'stress_errors': errors,
            'accuracy_diagnostics': {
                'axial_within_retained_5percent': errors['axial_xx_scaled_max'] <= limit,
                'shear_within_retained_5percent': errors['shear_xz_zx_scaled_max'] <= limit},
            'controlling_interior_points': controlling_points(recovery.stress, exact, coordinates, mask, manifest),
            'coordinates_m': coordinates.tolist(), 'actual_stress_Pa': recovery.stress.tolist(),
            'reference_stress_Pa': exact.tolist(), 'fixed_interior_mask': mask.tolist(),
            'quadrature_weights_m3': recovery.weights.tolist(),
            'coefficient_values_m': np.asarray(coefficients).tolist()}


def end_reactions(prepared, coefficients, manifest, reference_manifest):
    # Consistent discrete nodal forces are conjugate to actual physical vector
    # coefficients; sum them using the upstream component/coordinate map.
    nodal_forces = np.asarray(prepared.assemble_linear() @ coefficients)
    Q = reference_manifest['force_N']
    geometry = manifest['geometry']
    records = {}
    for side, xpos, expected_fz, expected_my in (
        ('left', geometry['solid_x_m'][0], -Q, 2 * Q),
        ('right', geometry['solid_x_m'][1], Q, -Q)):
        dofs = prepared.boundary_dofs(side)
        centroid = np.array([xpos, np.mean(geometry['y_m']), np.mean(geometry['z_m'])])
        vectors = np.zeros((len(dofs), 3))
        vectors[np.arange(len(dofs)), prepared.coefficient_components[dofs]] = nodal_forces[dofs]
        resultant = vectors.sum(axis=0)
        moment = np.cross(prepared.coefficient_coordinates[dofs] - centroid, vectors).sum(axis=0)
        expected_force = np.array([0., 0., expected_fz])
        expected_moment = np.array([0., expected_my, 0.])
        records[side] = {'centroid_m': centroid.tolist(), 'force_N': resultant.tolist(),
            'moment_about_face_centroid_Nm': moment.tolist(),
            'reference_force_N': expected_force.tolist(), 'reference_moment_Nm': expected_moment.tolist(),
            'force_error_N': (resultant - expected_force).tolist(),
            'moment_error_Nm': (moment - expected_moment).tolist(),
            'fz_error_relative_diagnostic': float(abs(resultant[2] - expected_fz) / Q),
            'my_error_relative_diagnostic': float(abs(moment[1] - expected_my) / abs(expected_my)),
            'prescribed_dofs': dofs.tolist(), 'conjugate_force_coefficients_N': nodal_forces[dofs].tolist()}
    return records


def module_identities():
    names = ('numpy', 'scipy', 'skfem', 'anysolid.backend', 'anysolid.mesh',
             'anysolver.solids', 'anysolver.solid_residuals', 'anysolver.assembly',
             'anysolver.matrix_assembly')
    result = {}
    for name in names:
        module = sys.modules.get(name)
        path = Path(module.__file__).resolve() if module is not None and getattr(module, '__file__', None) else None
        result[name] = {'path': str(path) if path else None,
                        'sha256': sha(path) if path and path.is_file() else None}
    return result


def main():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    emit({'type': 'run_identity', 'manifest_path': str(MANIFEST), 'manifest_sha256': sha(MANIFEST),
          'manifest': manifest, 'harness_sha256': sha(__file__),
          'versions': {'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__, 'skfem': skfem.__version__},
          'module_identities': module_identities(), 'production_status': 'NO_GO_PRODUCTION_UNQUALIFIED'})
    reference, reference_manifest, old_finest, reference_identity = load_reference(manifest)
    emit({'type': 'reference_identity', **reference_identity})
    meshes = manifest['meshes']
    if len(meshes) != manifest['bounds']['meshes'] or len(meshes) > manifest['bounds']['maximum_solid_solves']:
        raise ValueError('mesh/solve counts violate prospective limits')
    refs = manifest['fixed_scales']
    scales = ResidualScales(refs['length_m'], refs['force_N'], refs['displacement_m'])
    solved_count = 0
    summaries = []
    failures = 0
    for mesh_spec in meshes:
        started = time.perf_counter()
        emit({'type': 'mesh_start', 'mesh': mesh_spec})
        try:
            prepared = controlled_mesh(mesh_spec, manifest, reference_manifest)
            physical = reference.reference_fields(prepared.coefficient_coordinates, reference_manifest)[0]
            interpolant = physical[np.arange(prepared.ndof), prepared.coefficient_components]
            interpolation = stress_record('analytic_nodal_interpolant', prepared, interpolant,
                                         reference, reference_manifest, manifest)
            baseline_same_samples = None
            if mesh_spec['id'] == 'original_solid':
                old_coordinates = np.asarray(old_finest['stress_sample_coordinates_m'])
                baseline_same_samples = np.array_equal(old_coordinates, np.asarray(interpolation['coordinates_m']))
                if not baseline_same_samples:
                    raise ValueError('original-mesh quadrature coordinates differ from retained coupled case')
            emit({'type': 'interpolant_result', 'mesh': mesh_spec, 'ndof': int(prepared.ndof),
                  'meaning': 'analytic nodal interpolation; not a solved state or best-approximation error bound',
                  'matches_retained_coupled_sampling': baseline_same_samples,
                  'mesh_coordinates_m': prepared.mesh.coordinates.tolist(), 'cells': prepared.mesh.cells.tolist(),
                  'coefficient_coordinates_m': prepared.coefficient_coordinates.tolist(),
                  'coefficient_components': prepared.coefficient_components.tolist(), **interpolation})
            model = SolidModel(residual_scales={'isolation': scales})
            region = model.add_region('solid', prepared=prepared)
            fixed = np.unique(np.concatenate([prepared.boundary_dofs(side) for side in ('left', 'right')]))
            region.prescribe_dofs(fixed, interpolant[fixed])
            region.set_load('isolation', np.zeros(prepared.ndof))
            emit({'type': 'solve_start', 'mesh': mesh_spec, 'ndof': int(prepared.ndof),
                  'fixed_coefficient_count': int(len(fixed)), 'solid_solve_attempt': solved_count + 1,
                  'loads': 'zero body force and free lateral surfaces', 'interfaces': 0})
            solved_count += 1
            try:
                result = model.solve_static(('isolation',))
            except Exception as exc:
                emit({'type': 'solve_failure', 'mesh': mesh_spec, 'error_type': type(exc).__name__,
                      'error': str(exc), 'diagnostics': getattr(exc, 'diagnostics', None)})
                raise
            coefficients = result.region_coefficients('solid')[:, 0]
            solved = stress_record('analytic_boundary_solve', prepared, coefficients,
                                   reference, reference_manifest, manifest)
            residuals = result.diagnostics['registered_residual_report']
            reactions = end_reactions(prepared, coefficients, manifest, reference_manifest)
            emit({'type': 'solved_result', 'mesh': mesh_spec, 'ndof': int(prepared.ndof), **solved,
                  'end_support_resultants': reactions, 'registered_residual_report': residuals,
                  'legacy_componentwise_constraint_error': result.diagnostics['legacy_componentwise_constraint_error'],
                  'level_wall_seconds': time.perf_counter() - started,
                  'production_status': 'NO_GO_PRODUCTION_UNQUALIFIED'})
            summaries.append({'mesh': mesh_spec, 'ndof': int(prepared.ndof),
                'interpolant_errors': interpolation['stress_errors'], 'solved_errors': solved['stress_errors'],
                'interpolant_controlling_points': interpolation['controlling_interior_points'],
                'solved_controlling_points': solved['controlling_interior_points'],
                'normalized_equilibrium': residuals['normalized_equilibrium'],
                'normalized_constraint_error': residuals['normalized_constraint_error'],
                'accuracy_diagnostics': solved['accuracy_diagnostics'],
                'end_support_resultants': {side: {key: val for key, val in data.items()
                    if key not in ('prescribed_dofs', 'conjugate_force_coefficients_N')}
                    for side, data in reactions.items()}})
        except Exception as exc:
            failures += 1
            emit({'type': 'mesh_failure', 'mesh': mesh_spec, 'error_type': type(exc).__name__,
                  'error': str(exc), 'level_wall_seconds': time.perf_counter() - started})
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
    emit({'type': 'run_summary', 'meshes_requested': len(meshes), 'meshes_completed': len(summaries),
          'solid_solves_attempted': solved_count, 'execution_failures': failures,
          'status': 'DIAGNOSTIC_COMPLETE' if failures == 0 else 'DIAGNOSTIC_INCOMPLETE',
          'summaries': summaries, 'qualification': 'NOT_A_PRODUCTION_ACCEPTANCE',
          'accuracy_limit': manifest['acceptance']['retained_shear_accuracy_limit'],
          'known_limit': 'interpolant is not an error bound; end interpolation and interior discretization both remain; no automatic interface attribution',
          'production_status': 'NO_GO_PRODUCTION_UNQUALIFIED'})
    return int(failures != 0)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        emit({'type': 'startup_failure', 'error_type': type(exc).__name__, 'error': str(exc)})
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(1)
