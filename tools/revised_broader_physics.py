"""Three admitted changed-profile B cases; default is stdlib proposal audit only."""
from __future__ import annotations
import argparse
import copy
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback
import types

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'docs/revised_broader_manifest.json'
IDS=('mixed_bending_weak','two_replacements_four_transitions','s3_width_bending_min3_term')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def emit(record):
    def convert(value):
        if hasattr(value,'tolist'): return value.tolist()
        if hasattr(value,'item'): return value.item()
        raise TypeError(type(value).__name__)
    print(json.dumps(record,default=convert,allow_nan=False,sort_keys=True),flush=True)


def exact_policy(shell,solid):
    """Stdlib independent registration audit; execution also calls public API."""
    for points in (shell,solid):
        if len(points)<2 or points[0]!=0 or points[-1]<=0 or any(not math.isfinite(x) for x in points):
            raise ValueError('invalid geometric partition')
        intervals=[Fraction(b)-Fraction(a) for a,b in zip(points,points[1:])]
        if min(intervals)<=0 or max(intervals)>2*min(intervals): raise ValueError('invalid input spacing')
    if shell[-1]!=solid[-1]: raise ValueError('different partition endpoints')
    chosen=shell if len(shell)<=len(solid) else solid
    result=chosen[::2]
    if result[-1]!=chosen[-1]: result=result+[chosen[-1]]
    return result


def output_factor(refs):
    U,L=Fraction(refs['displacement_ref']),Fraction(refs['length_ref'])
    ratio=max(U/Fraction(refs['displacement_check_scale']),U/(L*Fraction(refs['rotation_check_scale'])))
    return math.ceil(ratio)


def derived_cases(old):
    result=[]
    for name in IDS:
        case=copy.deepcopy(next(c for c in old['cases'] if c['id']==name));rows=0
        for interface in case['interfaces']:
            region=next(r for r in case['regions'] if r['name']==interface['region'])
            knots=exact_policy(case['shell_corners'],region['y_corners'])
            interface['multiplier_chart_knots']=(knots if interface['native_side']=='right' else [1.-y for y in reversed(knots)])
            rows+=5*len(knots)
        case['planned_multiplier_rows']=rows
        reduced=case['planned_primary_dofs']-6*len(case['shell_corners'])
        result.append({'physical_case':case,'planned_reduced':reduced,'planned_KKT':reduced+rows,
                       'physical_output_factor':output_factor(case['references'])})
    return result


def validate(manifest):
    if sha(__file__)!=manifest['harness_sha256']: raise ValueError('runner changed')
    for path,expected in manifest['source_hashes'].items():
        if sha(path)!=expected: raise ValueError(f'frozen source/input changed: {path}')
    old=json.loads(Path(manifest['old_physical_manifest']).read_text())
    if derived_cases(old)!=manifest['cases']: raise ValueError('unregistered physical or knot/count change')
    finite=json.loads((ROOT/'docs/finite_stability_manifest.json').read_text())
    if manifest['certificate_scope']!=finite['certificate'] or manifest['scaled_operator']!=finite['scaled_operator']:
        raise ValueError('frozen certificate arithmetic/normalization registration changed')
    expected=copy.deepcopy(old)
    expected['bounds']['maximum_primary_dofs']=1000;expected['bounds']['maximum_multiplier_rows']=100
    if manifest['fixture_configuration']!=expected: raise ValueError('unregistered fixture configuration')
    for entry in manifest['cases']:
        c=entry['physical_case']
        if c['planned_primary_dofs']>1000 or c['planned_multiplier_rows']>100 or entry['planned_KKT']>1100:
            raise ValueError('prospective dimensions exceed bounds')
        if any(u!=c['references']['displacement_ref'] for u in c['references']['interface_displacement_refs']):
            raise ValueError('registered common interface U differs')
    return old


def load_source(path,expected,name):
    payload=Path(path).read_bytes()
    if hashlib.sha256(payload).hexdigest()!=expected: raise ValueError('helper changed')
    module=types.ModuleType(name);module.__file__=str(path)
    exec(compile(payload,str(path),'exec'),module.__dict__)
    return module


def run_case(np,fixture,numerics,entry,manifest,deadline,counts):
    from scipy import sparse
    from anysolver.assembly import assemble_system,build_constraint_transformation
    from anysolver.solids import SolidModel,ResidualScales
    from anysolid.multiplier import coarsened_p1_partition
    case=entry['physical_case'];refs=case['references'];name=case['id'];U=refs['displacement_ref'];Fref=refs['force_ref'];L=refs['length_ref'];t=.2
    for interface in case['interfaces']:
        region=next(r for r in case['regions'] if r['name']==interface['region'])
        knots=coarsened_p1_partition(case['shell_corners'],region['y_corners']).tolist()
        chart=knots if interface['native_side']=='right' else [1.-y for y in reversed(knots)]
        if chart!=interface['multiplier_chart_knots']: raise ValueError('public policy/registration differs')
    native,regions,operators,clamp,tip=fixture.build_specimen(np,case,manifest['fixture_configuration'])
    if any(p.elastic_modulus!=1000. or p.poisson_ratio!=0. for p in regions.values()):
        raise ValueError('constructed solid material differs from registration')
    load,F,solid_loads,weights=fixture.make_loads(np,native,regions,tip,case,manifest['fixture_configuration'])
    native.apply_boundary_conditions();Ksh,_,_=assemble_system(native,load)
    _,_,Tsh,u0,_,_=build_constraint_transformation(Ksh,F,native)
    region_names=[r['name'] for r in case['regions']]
    Ks={n:regions[n].assemble_linear() for n in region_names}
    K=sparse.block_diag([Ksh]+[Ks[n] for n in region_names],format='csr')
    P=sparse.block_diag([Tsh]+[sparse.eye(regions[n].ndof) for n in region_names],format='csr');P.sum_duplicates();P.eliminate_zeros()
    columns=P.tocsc()
    if np.any(np.diff(columns.indptr)!=1) or not np.all(columns.data==1.) or np.any(np.diff(P.indptr)>1):
        raise ValueError('selection-only supports required; no MPC')
    free=columns.indices
    C=sparse.vstack([sparse.hstack([op.C_shell]+[-op.C_solid if n==region_name else sparse.csr_matrix((op.C_shell.shape[0],regions[n].ndof)) for n in region_names]) for region_name,op in operators],format='csr')
    C.sum_duplicates();C.eliminate_zeros();Kr=K[free][:,free].tocsr();B=C[:,free].tocsr()
    for matrix in (Kr,B): matrix.sum_duplicates();matrix.eliminate_zeros()
    r,m=B.shape[1],B.shape[0]
    if (K.shape[0]!=case['planned_primary_dofs'] or r!=entry['planned_reduced'] or r+m!=entry['planned_KKT'] or m!=case['planned_multiplier_rows']
            or K.shape[0]>1000 or r+m>1100 or m>100): raise ValueError('actual dimensions/counts exceed registration')
    symmetry=float(sparse.linalg.norm(K-K.T,np.inf)/sparse.linalg.norm(K,np.inf))
    if symmetry>1e-10: raise ValueError('physical symmetry failure')
    if L!=1.: raise ValueError('registered L1 family required')
    D=np.ones(K.shape[0]);s=np.ones(r);T=np.full(r,U);S=np.full(r,Fref)
    G=np.array([float(Fraction(U)*sum(abs(Fraction(float(v))) for v in C.data[C.indptr[i]:C.indptr[i+1]])) for i in range(m)])
    modal=np.array([float(Fraction(Fref)/(Fraction(L)*Fraction(t)))]*3+[float(6*Fraction(Fref)*Fraction(L)/Fraction(t)**2)]*2)
    Lambda=np.tile(modal,m//5)
    H=numerics.build_scaled_kkt(Kr,B,S,T,G,Lambda)
    def csr(matrix): return {'shape':matrix.shape,'indptr':matrix.indptr,'indices':matrix.indices,'data':matrix.data}
    emit({'type':'metric_start','case':name,'registration':entry,'region_order':region_names,'dimensions':{'primary':K.shape[0],'reduced':r,'multiplier':m,'KKT':r+m},
          'canonical_stored_Kr':csr(Kr),'canonical_stored_B':csr(B),'formed_H':csr(H),'selection_free_rows':free,'affine_native_support_vector':u0,
          'scales':{'D':D,'s':s,'T':T,'S':S,'G':G,'Lambda':Lambda},'physical_output_factor':entry['physical_output_factor'],
          'row_units':'five weak section modes node-major; physical moment tests; no knot-dependent normalization',
          'physical_symmetry':symmetry,'csr_H_array_bytes':H.data.nbytes+H.indices.nbytes+H.indptr.nbytes})
    started=time.perf_counter()
    counts['metric_attempts']+=1
    cert=numerics.certify_inverse_action(H,r,physical_output_factor=entry['physical_output_factor'],block_columns=64,deadline=deadline,
        progress=lambda rec:emit({'type':'inverse_progress','case':name,**rec}))
    emit({'type':'inverse_certificate','case':name,'certificate':cert,'phase_wall_seconds':time.perf_counter()-started})
    emit({'type':'positive_energy_start','case':name,'reduced_dimension':r})
    started=time.perf_counter();positive=numerics.finite_positive_energy_check(Kr,B,maximum_reduced=1000,deadline=deadline)
    emit({'type':'positive_energy_result','case':name,**positive,'phase_wall_seconds':time.perf_counter()-started})
    counts['metric_results']+=1
    if time.perf_counter()>=deadline: raise TimeoutError('85s deadline before physical solve')
    scales=ResidualScales(L,Fref,U,tuple(refs['interface_displacement_refs']))
    model=SolidModel(native,research_coupling=True,residual_scales={name:scales})
    for n in region_names: model.add_region(n,prepared=regions[n]).set_load(name,solid_loads[n])
    for n,op in operators: model.add_interface(n,op)
    emit({'type':'physical_solve_start','case':name,'native_loads':load.nodal_loads,'solid_loads':solid_loads,'native_line_weights':weights,
          'registered_scales':vars(scales),'prepared_signatures':{n:p.cache_signature() for n,p in regions.items()},
          'native_mesh':{'nodes':{node.id:node.coords() for node in native.mesh.nodes.values()},
                         'elements':{eid:element.node_ids for eid,element in native.mesh.elements.items()}},
          'solid_meshes':{n:{'coordinates':p.mesh.coordinates,'cells':p.mesh.cells,'boundary_facets':p.mesh.boundary_facets,
                            'boundary_groups':dict(p.mesh.boundary_groups)} for n,p in regions.items()}})
    counts['physical_attempts']+=1
    result=model.solve_static((name,),native_load_cases={name:load});counts['physical_results']+=1;q=result.native_displacements[:,0]
    exact_q=np.zeros_like(q);trans=[];rot=[]
    for node in native.mesh.nodes.values():
        dofs=native.mesh.dof_manager.get_node_dofs(node.id);u,theta=fixture.reference_fields(np,node.coords(),case)
        exact_q[dofs]=np.r_[u,theta];trans.extend(dofs[:3]);rot.extend(dofs[3:])
    native_error=float(abs(q[trans]-exact_q[trans]).max()/refs['displacement_check_scale'])
    rotation=float(abs(q[rot]-exact_q[rot]).max()/refs['rotation_check_scale'])
    energy=float(q@Ksh@q);applied=float(q@F);solid_error=0.;stress=0.;records={}
    for region in case['regions']:
        n=region['name'];p=regions[n];a=result.region_coefficients(n)[:,0]
        exact_values=fixture.reference_fields(np,p.coefficient_coordinates,case)[0];exact_a=exact_values[np.arange(p.ndof),p.coefficient_components]
        field=float(abs(a-exact_a).max()/refs['displacement_check_scale']);solid_error=max(solid_error,field)
        energy+=float(a@Ks[n]@a);applied+=float(a@solid_loads[n])
        recovery=p.recover(a);expected=np.zeros_like(recovery.stress);axis=1 if case['profile']=='width_bending' else 0
        expected[...,axis,axis]=refs['stress_scale'] if case['profile']=='membrane' else 1000.*refs['curvature']*recovery.coordinates[...,2]
        lo,hi=region['stress_roi_x'];mask=(recovery.coordinates[...,0]>=lo)&(recovery.coordinates[...,0]<=hi)
        if not np.any(mask): raise ValueError('empty frozen stress ROI')
        errors=abs(recovery.stress[mask]-expected[mask]);local=float(errors.max()/refs['stress_scale']);stress=max(stress,local)
        idx=np.unravel_index(np.argmax(errors),errors.shape)
        records[n]={'coefficients':a,'reference_coefficients':exact_a,'coefficient_coordinates':p.coefficient_coordinates,'coefficient_components':p.coefficient_components,
            'whole_coefficient_displacement_error':field,'stress_coordinates':recovery.coordinates,'actual_stress':recovery.stress,'reference_stress':expected,
            'fixed_roi_mask':mask,'stress_scaled_max':local,'controlling_stress_coordinate':recovery.coordinates[mask][idx[0]],'controlling_stress_component':idx[1:]}
    fixed=np.array([d for nid in clamp for d in native.mesh.dof_manager.get_node_dofs(nid)],dtype=int)
    support=np.zeros_like(q);support[fixed]=result.reactions[fixed,0];support_work=float(q[fixed]@support[fixed])
    ef,em=fixture.physical_resultant(np,native,F,solid_loads,regions);sf,sm=fixture.physical_resultant(np,native,support,{},regions)
    force_error=float(np.linalg.norm(ef+sf,np.inf)/Fref);moment_error=float(np.linalg.norm(em+sm,np.inf)/(Fref*L))
    work_error=abs(energy-applied-support_work)/refs['twice_energy'];energy_error=abs(energy-refs['twice_energy'])/refs['twice_energy']
    virtual=[]
    for index,(n,op) in enumerate(operators):
        rng=np.random.default_rng(7100+index);vq=rng.normal(size=q.shape)*U
        for node in native.mesh.nodes.values(): vq[native.mesh.dof_manager.get_node_dofs(node.id)[3:]]/=L
        va=rng.normal(size=regions[n].ndof)*U;vl=rng.normal(size=op.C_shell.shape[0])*Fref/t
        fs,fv=op.interface_forces(vl);virtual.append(float(abs(vq@fs+va@fv-vl@(op.C_shell@vq-op.C_solid@va))/(Fref*U)))
    residual=result.diagnostics['registered_residual_report'];displacement=max(native_error,solid_error)
    checks={'verified_inverse':cert['verified'],'physical_output_allocation':cert.get('physical_output_amplification_upper',math.inf)<=1e6,
        'modal_traction_couple_allocation':cert.get('modal_traction_couple_amplification_upper',math.inf)<=5e6,'finite_positive_energy':positive.get('positive_energy',False),
        'global_mixed_displacement':displacement<=.009,'native_rotation':rotation<=.009,'energy':energy_error<=.009,'stress':stress<=.045,
        'residual':bool(residual['passed']),'energy_external_support_work':work_error<=1e-10,'operator_virtual_work':max(virtual)<=1e-10,
        'force':force_error<=1e-8,'moment':moment_error<=1e-8,'symmetry':symmetry<=1e-10}
    emit({'type':'physical_result','case':name,'checks':checks,'passed':bool(all(checks.values())),'references':refs,
          'native_displacement_error':native_error,'whole_solid_displacement_error':solid_error,'global_mixed_displacement_error':displacement,
          'rotation_error':rotation,'energy_error':energy_error,'stress_error':stress,'force_error':force_error,'moment_error':moment_error,
          'original_physical_limits':{'field_energy_met':max(displacement,rotation,energy_error)<=.01,'stress_met':stress<=.05},
          'energy_twice':energy,'external_work':applied,'affine_support_work':support_work,'work_error':work_error,'operator_virtual_work_errors':virtual,
          'native_coefficients':q,'native_reference_coefficients':exact_q,'native_coordinates':{n.id:n.coords() for n in native.mesh.nodes.values()},
          'support_dofs':fixed,'support_reactions':support[fixed],'support_force':sf,'support_moment':sm,'all_applied_force':ef,'all_applied_moment':em,
          'regions':records,'multipliers':result.multipliers,'registered_residual_report':residual,'qualification':result.diagnostics['qualification']})
    return {'case':name,'passed':bool(all(checks.values())),'checks':checks,'displacement':displacement,'rotation':rotation,'energy':energy_error,'stress':stress,
        'physical_output_bound':cert.get('physical_output_amplification_upper'),'modal_bound':cert.get('modal_traction_couple_amplification_upper')}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    manifest=json.loads(MANIFEST.read_text());validate(manifest)
    emit({'type':'broader_identity','manifest':manifest,'manifest_sha256':sha(MANIFEST),'execute':args.execute})
    if not args.execute:
        emit({'type':'proposal_only','fresh_metrics':0,'fresh_physical_solves':0});return 0
    disposition=json.loads(Path(manifest['prerequisite']['path']).read_text())
    if disposition['status']!='PASSED_FINITE_CANDIDATE_B': raise ValueError('parent candidate B disposition prerequisite absent')
    emit({'type':'prerequisite_disposition','sha256':sha(manifest['prerequisite']['path']),'disposition':disposition})
    import numpy as np
    import scipy
    import scipy.linalg
    import skfem
    from threadpoolctl import threadpool_info
    runtime={'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'skfem':skfem.__version__,'actual_threadpools':threadpool_info(),
             'thread_environment':{k:os.environ.get(k) for k in ('MKL_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')}}
    canonical=lambda pools:sorted(pools,key=lambda p:p['filepath'].casefold())
    if (any(runtime[k]!=manifest['runtime'][k] for k in ('python','numpy','scipy','skfem','thread_environment'))
            or not runtime['actual_threadpools'] or any(p['num_threads']!=1 for p in runtime['actual_threadpools'])
            or canonical(runtime['actual_threadpools'])!=canonical(manifest['runtime']['actual_threadpools'])
            or os.environ.get('PYTHONPATH')!=manifest['runtime']['pythonpath']):
        raise ValueError('runtime/version/single-thread configuration differs')
    emit({'type':'runtime',**runtime})
    fixture=load_source(manifest['fixture_path'],manifest['source_hashes'][manifest['fixture_path']],'_broader_frozen_fixture')
    numerics=load_source(manifest['numerics_path'],manifest['source_hashes'][manifest['numerics_path']],'_broader_frozen_numerics')
    deadline=time.perf_counter()+85.;results=[];failures=0;counts=dict.fromkeys(('metric_attempts','metric_results','physical_attempts','physical_results'),0)
    for entry in manifest['cases']:
        name=entry['physical_case']['id'];emit({'type':'case_start','case':name,'registration':entry})
        try:
            if time.perf_counter()>=deadline: raise TimeoutError('registered85s deadline')
            results.append(run_case(np,fixture,numerics,entry,manifest,deadline,counts))
        except Exception as exc:
            failures+=1;emit({'type':'case_failure','case':name,'error_type':type(exc).__name__,'error':str(exc),'diagnostics':getattr(exc,'diagnostics',None)})
            traceback.print_exc(file=sys.stderr);break
    passed=failures==0 and len(results)==3 and all(r['passed'] for r in results)
    emit({'type':'broader_terminal','fresh_counts':counts,'fresh_completed_metric_physical_pairs':len(results),'execution_failures':failures,'passed':bool(passed),'results':results,
          'withheld_profiles':manifest['withheld_profiles'],
          'untested_prior_cases':'Unchanged original profiles are not fresh B tests; no reuse adjudication here','production_status':'NO_GO_PRODUCTION_UNQUALIFIED'})
    return int(not passed)


if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc:
        emit({'type':'startup_failure','error_type':type(exc).__name__,'error':str(exc)});traceback.print_exc(file=sys.stderr);raise SystemExit(1)
