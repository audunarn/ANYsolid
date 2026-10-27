"""Candidate B: fresh coarsened-multiplier qualification, old A stays failed.

Default mode validates the proposal and immutable six-reference reuse only.
No old helper main or old candidate result is ever invoked/reused.
"""
from __future__ import annotations
import argparse
import copy
from collections import Counter
from collections.abc import Mapping
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys
import time
import traceback
import types

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'docs/revised_multiplier_manifest.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def emit(value):
    def convert(item):
        if isinstance(item,Mapping): return dict(item)
        if hasattr(item,'tolist'): return item.tolist()
        if hasattr(item,'item'): return item.item()
        raise TypeError(type(item).__name__)
    print(json.dumps(value,allow_nan=False,default=convert,sort_keys=True),flush=True)


def strict_json(text):
    def reject(value): raise ValueError(f'nonfinite JSON constant {value}')
    return json.loads(text,parse_constant=reject)


def real(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError('reference numerical arrays/predicates must contain finite real numbers')
    return value


def shape_numbers(value,shape):
    if not shape:
        real(value);return
    if not isinstance(value,list) or len(value)!=shape[0]:
        raise ValueError(f'reference array shape differs from {shape}')
    for item in value: shape_numbers(item,shape[1:])


def require_metric(record,name,limit,recomputed=None):
    value=real(record[name])
    if value<0 or value>limit: raise ValueError(f'reused reference predicate failed: {name}')
    if recomputed is not None and value!=recomputed:
        raise ValueError(f'reused reference raw predicate mismatch: {name}')


def validate_reference_record(record,start,registration,coarse):
    if record['reference']!=registration or start['reference']!=registration:
        raise ValueError('reference registration differs from frozen input')
    n=registration['subdivisions'];ndof=registration['planned_dofs'];cells=6*n**3
    if start['ndof']!=ndof or start['matrix_shape']!=[ndof,ndof] or start['matrix_nnz']<=0:
        raise ValueError('reference dimensions/assembly provenance mismatch')
    if start['route']!='ANYsolid public backend plus direct SciPy LU; no shell/coupling':
        raise ValueError('reference route is not the independent uncoupled route')
    coordinates=record['coefficient_coordinates'];components=record['components']
    actual=record['actual_coefficients'];exact=record['exact_coefficients']
    shape_numbers(coordinates,(ndof,3));shape_numbers(actual,(ndof,));shape_numbers(exact,(ndof,))
    if len(components)!=ndof or any(type(c) is not int or c not in (0,1,2) for c in components):
        raise ValueError('reference coefficient component map invalid')
    geometry=registration['geometry'];seen={}
    expected_fixed=[];expected_boundary=[]
    for index,(point,component) in enumerate(zip(coordinates,components)):
        if any(not geometry[name][0]<=point[k]<=geometry[name][1] for k,name in enumerate(('x','y','z'))):
            raise ValueError('reference coefficient outside registered full body')
        key=tuple(point)
        if component in seen.setdefault(key,set()): raise ValueError('duplicate reference coefficient/component')
        seen[key].add(component)
        X,Y,Z=point
        expected=(0.,.001*(Y-.5)*Z,-.001*(Y-.5)**2/2)[component]
        if exact[index]!=expected: raise ValueError('raw analytical primary reference changed')
        if X==-1.: expected_fixed.append(index)
        if any(point[k] in geometry[name] for k,name in enumerate(('x','y','z'))): expected_boundary.append(index)
    if len(seen)!=(2*n+1)**3 or any(values!={0,1,2} for values in seen.values()):
        raise ValueError('reference is not the registered complete vector nodal field')
    if record['boundary_dofs']!=expected_boundary or start['fixed_dofs']!=expected_fixed:
        raise ValueError('reference boundary/prescription coverage differs from actual coordinates')
    shape_numbers(start['applied_affine_surface_load'],(ndof,))
    if start['exact_fixed_values']!=[exact[i] for i in expected_fixed]:
        raise ValueError('reference prescribed values differ from exact field')
    full_error=max(abs(a-b) for a,b in zip(actual,exact))/.000125
    boundary_error=max(abs(actual[i]-exact[i]) for i in expected_boundary)/.000125
    require_metric(record,'all_primary_error',1e-4,full_error)
    require_metric(record,'all_boundary_error',1e-4,boundary_error)
    positions=record['all_stress_coordinates'];stress=record['actual_stress'];expected=record['exact_stress']
    shape_numbers(positions,(cells,11,3));shape_numbers(stress,(cells,11,3,3));shape_numbers(expected,(cells,11,3,3))
    stress_error=0.
    for points,values,refs in zip(positions,stress,expected):
        for point,tensor,reference in zip(points,values,refs):
            for i in range(3):
                for j in range(3):
                    analytical=point[2] if (i,j)==(1,1) else 0.
                    if reference[i][j]!=analytical: raise ValueError('raw analytical stress reference changed')
                    stress_error=max(stress_error,abs(tensor[i][j]-reference[i][j]))
    require_metric(record,'stress_error',5e-4,stress_error/(1000.*.001*registration['thickness']/2))
    energy=real(record['energy_twice']);work=real(record['external_plus_support_work']);eref=registration['twice_energy']
    require_metric(record,'energy_error',1e-4,abs(energy-eref)/eref)
    require_metric(record,'work_error',1e-10,abs(energy-work)/eref)
    # K and reaction vectors were not serialized in the old reference result.
    # These numeric predicates are checked directly against their unchanged
    # limits, with exact source/input provenance; no unavailable matrix replay
    # or fresh reference assembly is claimed.
    require_metric(record,'residual',1e-9);require_metric(record,'force_error',1e-8);require_metric(record,'moment_error',1e-8)
    expected_checks={'all_primary_coefficients','all_boundary_coefficients','energy','all_quadrature_stress','residual','work','force','moment'}
    refinement=record['refinement_difference']
    if n==4:
        if coarse is None or refinement is None: raise ValueError('missing coarse/fine reference pair')
        if refinement['common_coordinates']!=coarse['coefficient_coordinates'] or refinement['common_components']!=coarse['components']:
            raise ValueError('refinement comparison coordinates/components changed')
        differences=refinement['common_point_coefficient_differences'];shape_numbers(differences,(coarse['reference']['planned_dofs'],))
        require_metric(refinement,'coarse_fine_common_coefficient_displacement_difference_scaled',1e-4,max(map(abs,differences))/.000125)
        require_metric(refinement,'coarse_fine_energy_difference_relative',1e-4,abs(energy-coarse['energy_twice'])/eref)
        expected_checks|={'refinement_common_field','refinement_energy'}
    elif refinement is not None: raise ValueError('coarse reference has unexpected refinement data')
    if set(record['checks'])!=expected_checks or any(value is not True for value in record['checks'].values()) or record['passed'] is not True:
        raise ValueError('reference reported check map disagrees with raw accepted predicates')


def validate_reused_references(manifest):
    archive=Path(manifest['reference_reuse']['archive'])
    for name,expected in manifest['reference_reuse']['artifact_sha256'].items():
        if sha(archive/name)!=expected: raise ValueError(f'retained artifact changed: {name}')
    old= strict_json(Path(manifest['old_manifest_path']).read_text(encoding='utf-8'))
    receipt=strict_json((archive/'result.json').read_text(encoding='utf-8'))
    identity=strict_json((archive/'identity.json').read_text(encoding='utf-8'))
    if (Path(identity['cwd']).resolve()!=ROOT.resolve() or identity['timeout_seconds']!=180
            or identity['python']!=sys.version
            or identity['command']!=[sys.executable,'tools/finite_stability_study.py','--execute']
            or identity['input_hashes']!={str(Path(manifest['old_helper_path'])):manifest['old_helper_sha256']}):
        raise ValueError('retained outer command/interpreter/input registration changed')
    if not identity['source_hashes']:
        raise ValueError('retained outer source inventory missing')
    for path,expected_hash in identity['source_hashes'].items():
        if sha(path)!=expected_hash: raise ValueError(f'retained outer source changed: {path}')
    if (receipt['status']!='process_error' or receipt['exit_code']!=1 or receipt['timeout_seconds']!=180
            or receipt['cleanup']!={'verified':True,'active_processes':0}
            or not 0<real(receipt['process_wall_seconds'])<=180 or receipt['events']['reader_errors']):
        raise ValueError('old run was not cleanly terminated completed scientific failure')
    expected={r['id']:r for r in old['full_solid_references']};starts={};refs={};summaries=[];counts=Counter();runtime=None;header=None;terminal=None;last=None
    with (archive/'stdout.jsonl').open(encoding='utf-8') as stream:
        for line_number,line in enumerate(stream,1):
            record=strict_json(line);kind=record['type'];counts[kind]+=1;last=kind
            if kind=='study_identity': header=record
            elif kind=='runtime': runtime=record
            elif kind=='full_solid_reference_start':
                if record['reference']!=expected[record['reference']['id']]: raise ValueError('reference start registration changed')
            elif kind=='full_solid_reference_solve_start':
                rid=record['reference']['id']
                if rid in starts: raise ValueError('duplicate reference solve start')
                starts[rid]=record
            elif kind=='full_solid_reference_result':
                registration=record['reference'];rid=registration['id']
                if rid in refs or rid not in starts: raise ValueError('duplicate/out-of-order reference result')
                coarse=next((v for v in refs.values() if v['reference']['thickness']==registration['thickness'] and v['reference']['subdivisions']==2),None)
                validate_reference_record(record,starts[rid],expected[rid],coarse)
                refs[rid]=record
                summaries.append({'reference':registration,'validated':True,'raw_line_number':line_number,
                    'raw_line_sha256':hashlib.sha256(line.encode('utf-8')).hexdigest(),
                    'predicates':{k:record[k] for k in ('all_primary_error','all_boundary_error','energy_error','stress_error','residual','work_error','force_error','moment_error')},
                    'recomputation_scope':'all primary/boundary/stress and energy/work/refinement predicates replayed; residual/force/moment numeric predicates rechecked with immutable source/input provenance; no reference K replay'})
            elif kind=='study_summary': terminal=record
    if set(refs)!=set(expected) or counts['full_solid_reference_solve_start']!=6 or counts['full_solid_reference_result']!=6:
        raise ValueError('exact six reference results are required')
    if header is None or header['manifest_sha256']!=manifest['old_manifest_sha256'] or header['harness_sha256']!=manifest['old_helper_sha256'] or header['manifest']!=old:
        raise ValueError('raw identity does not match frozen old source/input')
    if runtime is None or runtime['python']!=sys.version:
        raise ValueError('reference interpreter identity differs')
    for package in ('numpy','scipy','skfem'):
        distribution='scikit-fem' if package=='skfem' else package
        if importlib.metadata.version(distribution)!=runtime[package]: raise ValueError('reference numerical package version differs')
    if runtime['skfem']!='12.0.2' or any(v!='1' for v in runtime['thread_environment'].values()):
        raise ValueError('reference runtime contract differs')
    if not runtime['actual_threadpools'] or any(p['num_threads']!=1 for p in runtime['actual_threadpools']):
        raise ValueError('reference runtime pools were not single threaded')
    if (terminal is None or last!='study_summary' or terminal['metrics_completed']!=18 or terminal['physical_results']!=12
            or terminal['references_completed']!=6 or terminal['execution_failures']!=0
            or terminal['bounded_registered_cases_met'] is not False):
        raise ValueError('old failed candidate terminal record must remain complete and failed')
    if any(counts[k] for k in ('startup_failure','case_failure','full_solid_reference_failure')):
        raise ValueError('old archive includes execution failure rather than completed scientific failure')
    if len(terminal['reference_results'])!=6:
        raise ValueError('terminal reference summary incomplete')
    for summary in terminal['reference_results']:
        raw=refs[summary['reference']['id']]
        if any(raw[key]!=value for key,value in summary.items()): raise ValueError('terminal/raw reference summary mismatch')
    return {'validated_reference_count':6,'references':summaries,'runtime':runtime,
            'old_candidate_terminal':{'bounded_registered_cases_met':False,'metrics_completed':18,'physical_results':12},
            'reuse_scope':'ONLY six independent references; no A certificates or coupled results reused',
            'old_environment_pythonpath':identity['pythonpath']}


def derive_cases(old_cases):
    from anysolid.multiplier import coarsened_p1_partition
    result=[];applications=[]
    for old in old_cases:
        case=copy.deepcopy(old);physical=case['physical_case'];rows=0
        for interface in physical['interfaces']:
            region=next(r for r in physical['regions'] if r['name']==interface['region'])
            chosen=coarsened_p1_partition(physical['shell_corners'],region['y_corners']).tolist()
            knots=chosen if interface['native_side']=='right' else [1.-y for y in reversed(chosen)]
            interface['multiplier_chart_knots']=knots;rows+=5*len(knots)
            applications.append({'case':old['id'],'region':region['name'],'native_side':interface['native_side'],
                'shell_geometric_corners':physical['shell_corners'],'solid_geometric_corners':region['y_corners'],
                'selected_global_knots':chosen,'explicit_chart_knots':knots})
        physical['planned_multiplier_rows']=rows;case['planned_multiplier']=rows;case['planned_KKT']=case['planned_reduced']+rows
        result.append(case)
    return result,applications


def validate_proposal(manifest):
    if sha(__file__)!=manifest['harness_sha256']: raise ValueError('candidate B harness changed')
    if sha(manifest['old_helper_path'])!=manifest['old_helper_sha256'] or sha(manifest['old_manifest_path'])!=manifest['old_manifest_sha256']:
        raise ValueError('frozen A measurement helper/input changed')
    for path,expected in manifest['source_hashes'].items():
        if sha(path)!=expected: raise ValueError(f'frozen source changed: {path}')
    old=strict_json(Path(manifest['old_manifest_path']).read_text(encoding='utf-8'))
    cases,applications=derive_cases(old['cases'])
    if cases!=manifest['cases'] or applications!=manifest['policy_applications']:
        raise ValueError('candidate B differs from exactly the registered public-policy knot/count delta')
    registration={'physical_references':old['physical_references'],'bounds':{k:old['bounds'][k] for k in ('maximum_primary','maximum_kkt','maximum_multiplier')}}
    if manifest['measurement_registration']!=registration:
        raise ValueError('unchanged physical scaling/dimension registration changed')
    for name in ('certificate','scaled_operator','physical_acceptance','finite_positive_energy'):
        if manifest['unchanged_parameters'][name]!=old[name]: raise ValueError('A/B qualification parameter changed')
    if len(cases)!=18 or sum(c['physical_solve'] for c in cases)!=12:
        raise ValueError('fresh18/12 inventory changed')
    return old


def load_source(path,expected,name):
    payload=Path(path).read_bytes()
    if hashlib.sha256(payload).hexdigest()!=expected: raise ValueError('frozen helper source changed')
    module=types.ModuleType(name);module.__file__=str(path)
    # Compile the exact validated source bytes; do not invoke main or depend on
    # a historical helper bytecode cache. No source namespace is monkeypatched.
    exec(compile(payload,str(path),'exec'),module.__dict__)
    return module


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    manifest=strict_json(MANIFEST.read_text(encoding='utf-8'));old=validate_proposal(manifest)
    emit({'type':'candidate_B_identity','manifest':manifest,'manifest_sha256':sha(MANIFEST),
          'harness_sha256':sha(__file__),'execute':args.execute,'old_A_status':'FAILED_UNCHANGED'})
    reuse=validate_reused_references(manifest)
    emit({'type':'reused_independent_references','fresh_reference_solves':0,**reuse})
    if not args.execute:
        emit({'type':'proposal_only','fresh_metrics':0,'fresh_physical_solves':0,'references_reused_validated':6});return 0
    import numpy as np
    import scipy
    import scipy.linalg
    import scipy.sparse.linalg
    import skfem
    import os
    from threadpoolctl import threadpool_info
    current={'type':'runtime','python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'skfem':skfem.__version__,
             'actual_threadpools':threadpool_info(),'thread_environment':{k:os.environ.get(k) for k in ('MKL_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')}}
    previous=reuse['runtime']
    canonical=lambda pools:sorted(pools,key=lambda p:p['filepath'].casefold())
    if (any(current[k]!=previous[k] for k in ('python','numpy','scipy','skfem','thread_environment'))
            or canonical(current['actual_threadpools'])!=canonical(previous['actual_threadpools'])
            or os.environ.get('PYTHONPATH')!=reuse['old_environment_pythonpath']):
        raise ValueError('fresh runtime/pools/PYTHONPATH differ from independently referenced environment')
    emit(current)
    helper=load_source(manifest['old_helper_path'],manifest['old_helper_sha256'],'_candidate_B_frozen_measurements')
    fixture=load_source(old['fixture_path'],old['fixture_sha256'],'_candidate_B_geometry_load_fixture')
    deadline=time.perf_counter()+175.;records=[];failures=0;attempts=0
    for case in manifest['cases']:
        emit({'type':'fresh_case_start','candidate':'B','case':case['id'],'registration':case})
        started=time.perf_counter();attempts+=1
        try:
            if time.perf_counter()>=deadline: raise TimeoutError('candidate B registered175s deadline')
            record=helper.run_registered_case(np,fixture,case,manifest['measurement_registration'],deadline)
            record['candidate']='B';record['fresh_case_wall_seconds']=time.perf_counter()-started
            emit(record);records.append(record)
        except Exception as exc:
            failures+=1;emit({'type':'fresh_case_failure','candidate':'B','case':case['id'],'error_type':type(exc).__name__,
                'error':str(exc),'diagnostics':getattr(exc,'diagnostics',None)})
            traceback.print_exc(file=sys.stderr);sys.stderr.flush();break
    physical=[r for r in records if r['physical_summary'] is not None]
    finest=[r for r in physical if not r['physical_summary']['coarse_diagnostic_only']]
    accepted=(failures==0 and len(records)==18 and len(physical)==12 and len(finest)==3 and all(r['metric_passed'] for r in records)
              and all(r['physical_summary']['finest_measured_targets_met'] for r in finest)
              and all(all(r['physical_summary']['flags_at_finest_limits'][k] for k in ('residuals','work','force','moment')) for r in physical))
    emit({'type':'candidate_B_terminal','fresh_case_attempts':attempts,'fresh_metric_results':len(records),
          'fresh_physical_results':len(physical),'fresh_reference_solves':0,'validated_reused_reference_results':6,
          'execution_failures':failures,'bounded_candidate_B_cases_met':bool(accepted),'fresh_records':records,
          'old_A_status':'FAILED_UNCHANGED','production_status':'NO_GO_PRODUCTION_UNQUALIFIED'})
    return int(not accepted)


if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc:
        emit({'type':'candidate_B_startup_failure','error_type':type(exc).__name__,'error':str(exc)})
        traceback.print_exc(file=sys.stderr);raise SystemExit(1)
