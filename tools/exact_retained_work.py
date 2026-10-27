"""Retained-only exact work adjudication; no FE imports or new numerical solve."""
from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'docs/exact_retained_work_manifest.json'
CASE='two_replacements_four_transitions'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def emit(value): print(json.dumps(value,allow_nan=False,sort_keys=True),flush=True)


def integer(value):
    if isinstance(value,bool) or not isinstance(value,int): raise ValueError('integer required')
    return value


def number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value): raise ValueError('finite real number required')
    return value


def vector(value,length):
    if not isinstance(value,list) or len(value)!=length: raise ValueError('vector length/type mismatch')
    for v in value: number(v)
    return value


def validate(manifest,deadline):
    if sha(__file__)!=manifest['harness_sha256']: raise ValueError('audit source changed')
    for path,expected in manifest['input_and_source_sha256'].items():
        if sha(path)!=expected: raise ValueError(f'retained identity changed: {path}')
    for proof in manifest['source_ordering_proofs']:
        text=Path(proof['path']).read_text(encoding='utf-8')
        if any(fragment not in text for fragment in proof['required_exact_source_fragments']):
            raise ValueError('frozen node/DOF/block-order source proof missing')
    archive=Path(manifest['archive']);receipt=json.loads((archive/'result.json').read_text());identity=json.loads((archive/'identity.json').read_text())
    if (receipt['status']!='process_error' or receipt['exit_code']!=1 or receipt['timeout_seconds']!=90
            or receipt['cleanup']!={'verified':True,'active_processes':0} or receipt['events']['reader_errors']):
        raise ValueError('original complete scientific-failure receipt absent')
    if identity['command']!=[sys.executable,'tools/revised_broader_physics.py','--execute'] or identity['timeout_seconds']!=90 or Path(identity['cwd']).resolve()!=ROOT:
        raise ValueError('retained outer command differs')
    for path,expected in identity['source_hashes'].items():
        if manifest['input_and_source_sha256'].get(path)!=expected: raise ValueError('outer source inventory not fully pinned')
    records={};header=None;terminal=None;physical={};line_hashes={}
    with (archive/'stdout.jsonl').open(encoding='utf-8') as stream:
        for index,line in enumerate(stream,1):
            if time.perf_counter()>deadline: raise TimeoutError('25s retained audit deadline')
            record=json.loads(line);kind=record['type']
            if kind=='broader_identity':
                if header is not None: raise ValueError('duplicate retained header')
                header=record
            if kind=='broader_terminal': terminal=record
            if kind in ('case_failure','startup_failure'): raise ValueError('retained execution failure')
            if kind=='physical_result': physical[record['case']]=record
            if record.get('case')==CASE and kind in ('metric_start','physical_solve_start','physical_result'):
                if kind in records: raise ValueError('duplicate retained target record')
                records[kind]=record;line_hashes[kind]={'line':index,'sha256':hashlib.sha256(line.encode()).hexdigest()}
    old=json.loads(Path(manifest['broader_manifest_path']).read_text())
    if header is None or header['manifest']!=old or header['manifest']['harness_sha256']!=sha(manifest['broader_harness_path']) or header['manifest_sha256']!=sha(manifest['broader_manifest_path']) or header['execute'] is not True:
        raise ValueError('retained embedded source/registration identity differs')
    if identity['input_hashes']!={str(Path(manifest['broader_harness_path'])):header['manifest']['harness_sha256']}:
        raise ValueError('retained outer input hash differs')
    if terminal is None or terminal['passed'] is not False or terminal['execution_failures']!=0 or terminal['fresh_completed_metric_physical_pairs']!=3 or terminal['fresh_counts']!={'metric_attempts':3,'metric_results':3,'physical_attempts':3,'physical_results':3}:
        raise ValueError('original failed terminal/counts changed')
    if set(physical)!={'mixed_bending_weak',CASE,'s3_width_bending_min3_term'} or any(physical[n]['passed'] is not True for n in physical if n!=CASE):
        raise ValueError('unaffected original two passes must remain unchanged')
    if set(records)!={'metric_start','physical_solve_start','physical_result'} or line_hashes!=manifest['target_records']:
        raise ValueError('missing/out-of-order registered target records')
    if not (line_hashes['metric_start']['line']<line_hashes['physical_solve_start']['line']<line_hashes['physical_result']['line']): raise ValueError('target order changed')
    metric,start,result=(records[n] for n in ('metric_start','physical_solve_start','physical_result'))
    entry=next(e for e in old['cases'] if e['physical_case']['id']==CASE);case=entry['physical_case'];refs=case['references']
    if metric['registration']!=entry or result['references']!=refs or entry!=manifest['registration']: raise ValueError('target physical registration changed')
    expected_checks={k:True for k in result['checks']};expected_checks['energy_external_support_work']=False
    if result['checks']!=expected_checks or result['passed'] is not False or number(result['work_error'])<=1e-10:
        raise ValueError('original isolated double work failure not preserved')
    if number(result['affine_support_work'])!=0 or any(vector(metric['affine_native_support_vector'],108)):
        raise ValueError('nonzero affine/support work outside scope')
    if metric['region_order']!=['solid1','solid2'] or metric['region_order']!=[r['name'] for r in case['regions']]: raise ValueError('region ordering ambiguous')
    expected_nodes={};nid=0
    for xmin,xmax in case['native_intervals']:
        for y in case['shell_corners']:
            for x in (xmin,xmax):
                nid+=1;expected_nodes[str(nid)]=[x,y,0.]
    if nid!=18 or start['native_mesh']['nodes']!=expected_nodes or result['native_coordinates']!=expected_nodes:
        raise ValueError('saved node coordinates do not prove fixture insertion order')
    node_map={str(i):list(range(6*(i-1),6*i)) for i in range(1,19)}
    if node_map!=manifest['node_to_native_dofs']: raise ValueError('unregistered node/DOF map')
    fixed=[d for i in (1,3,5) for d in node_map[str(i)]]
    if result['support_dofs']!=fixed or fixed!=manifest['support_dofs']: raise ValueError('support ownership mismatch')
    q=list(vector(result['native_coefficients'],108));loads=[0.]*108
    if any(q[d]!=0 for d in fixed): raise ValueError('actual fixed coefficients are not exactly zero')
    if vector(start['native_line_weights'],3)!=case['native_right_line_weights'] or set(start['native_loads'])!={'14','16','18'}:
        raise ValueError('retained physical load ownership ambiguous')
    for node,values in start['native_loads'].items():
        vector(values,6)
        if any(values[i]!=0 for i in (0,1,2,3,5)): raise ValueError('unexpected native force/moment component')
        for dof,value in zip(node_map[node],values): loads[dof]=value
    if start['native_loads']!=manifest['actual_saved_native_loads']: raise ValueError('saved actual loads changed')
    if set(start['solid_loads'])!={'solid1','solid2'} or set(result['regions'])!={'solid1','solid2'}: raise ValueError('missing/additional solid load/coefficient block')
    for name,count in (('solid1',405),('solid2',315)):
        q.extend(vector(result['regions'][name]['coefficients'],count))
        force=vector(start['solid_loads'][name],count)
        if any(force): raise ValueError('nonzero solid external load outside homogeneous scope')
        loads.extend(force)
    if len(q)!=828 or len(q)>1000: raise ValueError('physical coefficient bound')
    free=[integer(v) for v in metric['selection_free_rows']]
    expected_free=[i for i in range(828) if i not in set(fixed)]
    if free!=expected_free or free!=manifest['selection_free_rows']: raise ValueError('free-coordinate ordering is ambiguous')
    if any(loads[d]!=0 for d in fixed): raise ValueError('nonzero support load outside scope')
    K=metric['canonical_stored_Kr'];indptr=[integer(v) for v in K['indptr']];indices=[integer(v) for v in K['indices']];data=vector(K['data'],len(indices))
    n=len(free)
    if K['shape']!=[n,n] or n!=810 or len(data)!=32241 or len(data)>50000 or len(indptr)!=n+1 or indptr[0]!=0 or indptr[-1]!=len(data):
        raise ValueError('canonical CSR dimensions/entry bounds differ')
    for i in range(n):
        a,b=indptr[i:i+2];row=indices[a:b]
        if not 0<=a<=b<=len(data) or any(not 0<=j<n for j in row) or any(x>=y for x,y in zip(row,row[1:])) or any(v==0 for v in data[a:b]):
            raise ValueError('noncanonical CSR input')
    if number(refs['twice_energy'])<=0 or refs['twice_energy']!=manifest['original_twice_energy_reference'] or manifest['work_limit']!=1e-10:
        raise ValueError('original normalizer/limit changed')
    return K,[q[i] for i in free],[loads[i] for i in free],refs['twice_energy'],result['work_error']


def rational(value):
    return {'numerator':str(value.numerator),'denominator':str(value.denominator),'rounded_display':float(value)}


def main():
    clock=time.perf_counter();deadline=clock+25.
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    manifest=json.loads(MANIFEST.read_text());emit({'type':'retained_audit_identity','manifest':manifest,'manifest_sha256':sha(MANIFEST),'execute':args.execute})
    K,q,F,reference,old_error=validate(manifest,deadline)
    emit({'type':'retained_schema_validated','case':CASE,'reduced_coefficients':len(q),'matrix_entries':len(K['data']),'original_double_status':'FAILED_UNCHANGED'})
    if not args.execute:
        emit({'type':'proposal_only','exact_contractions_executed':0,'FE_solves':0});return 0
    emit({'type':'exact_contraction_start','case':CASE,'no_new_FE_work':True})
    qr=[Fraction(v) for v in q];fr=[Fraction(v) for v in F];energy=Fraction(0)
    for i in range(len(qr)):
        if time.perf_counter()>deadline: raise TimeoutError('25s exact audit deadline')
        for index in range(K['indptr'][i],K['indptr'][i+1]): energy+=qr[i]*Fraction(K['data'][index])*qr[K['indices'][index]]
    external=sum((a*b for a,b in zip(qr,fr)),Fraction(0));difference=abs(energy-external);normalizer=Fraction(reference);error=difference/normalizer;limit=Fraction(1e-10)
    if time.perf_counter()>deadline: raise TimeoutError('25s exact audit deadline')
    passed=error<=limit
    emit({'type':'exact_retained_work_result','case':CASE,'energy':rational(energy),'actual_external_work':rational(external),'absolute_difference':rational(difference),
          'normalizer':rational(normalizer),'normalized_error':rational(error),'unchanged_limit':rational(limit),'passed':passed,
          'original_double_error':old_error,'original_double_status':'FAILED_UNCHANGED','other_two_original_passes':'UNCHANGED',
          'scope':'exact contraction of retained canonical binary matrices/actual coefficients/actual loads only; no FE rerun or continuum claim',
          'audit_wall_seconds':time.perf_counter()-clock,'FE_solves':0,'production_status':'NO_GO_PRODUCTION_UNQUALIFIED'})
    return int(not passed)


if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc:
        emit({'type':'retained_audit_failure','error_type':type(exc).__name__,'error':str(exc)});traceback.print_exc(file=sys.stderr);raise SystemExit(1)
