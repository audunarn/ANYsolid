"""Prospective Q4 generalized-section physical-offset patches; no promotion."""
from __future__ import annotations
import argparse
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'docs/offset_patch_manifest.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def emit(value):
    def convert(item):
        if isinstance(item,Mapping): return dict(item)
        if hasattr(item,'tolist'): return item.tolist()
        if hasattr(item,'item'): return item.item()
        raise TypeError(f'unsupported diagnostic JSON value {type(item).__name__}')
    print(json.dumps(value,default=convert,allow_nan=False,sort_keys=True),flush=True)


def validate_manifest(manifest):
    if sha(__file__)!=manifest['harness_sha256']:
        raise ValueError('prospective offset harness identity changed')
    for path,expected in manifest['source_hashes'].items():
        if sha(path)!=expected: raise ValueError(f'frozen source/fixture changed: {path}')
    if len(manifest['cases'])!=4 or manifest['bounds']['maximum_solves']!=4:
        raise ValueError('exact four-case offset inventory required')
    if {(c['offset'],c['profile']) for c in manifest['cases']}!={(e,p) for e in (-.05,.05) for p in ('membrane','bending')}:
        raise ValueError('offset case inventory changed')
    for case in manifest['cases']:
        if case['native_reference_z']!=-case['offset'] or case['trace_offset']!=case['offset']:
            raise ValueError('native reference plane/physical transport registration mismatch')
        if case['planned_primary_dofs']>manifest['bounds']['maximum_primary_dofs'] or case['planned_multiplier_rows']>manifest['bounds']['maximum_multiplier_rows']:
            raise ValueError('registered dimension bound exceeded')


def exact_fields(np,points,case):
    points=np.asarray(points)
    X,z=points[...,0]+1.,points[...,2]
    zero=np.zeros_like(X)
    if case['profile']=='membrane':
        displacement=np.stack((case['references']['epsilon']*X,zero,zero),axis=-1)
        rotations=np.stack((zero,zero,zero),axis=-1)
    else:
        a=case['references']['curvature']
        displacement=np.stack((a*X*z,zero,-a*X**2/2),axis=-1)
        rotations=np.stack((zero,a*X,zero),axis=-1)
    return displacement,rotations


def build_case(np,case,manifest):
    from skfem import MeshTet
    from anysolid import SolidMesh,prepare
    from anysolid.coupling import build_weak_connector
    from anysolver import FEModel,BoundaryCondition
    from anysolver.elements import create_shell_element
    from anysolver.shell_sections import GeneralizedShellSection
    from anysolver.solid_trace import ShellEdgeTrace
    native=FEModel(case['id'])
    native.add_material('m',manifest['material']['E'],manifest['material']['nu'])
    section=GeneralizedShellSection(A=case['section']['A'],B=case['section']['B'],
        D=case['section']['D'],As=case['section']['As'],name=case['id'])
    zref=case['native_reference_z']
    ys=manifest['geometry']['y_corners']
    edges=[];clamp=[];tip=[]
    for side,(xmin,xmax) in enumerate(manifest['geometry']['native_intervals']):
        nodes={}
        for j,y in enumerate(ys):
            for i,x in enumerate((xmin,xmax)):
                nid=len(native.mesh.nodes)+1
                native.add_node(nid,x,y,zref)
                nodes[i,j]=nid
                if side==0 and i==0: clamp.append(nid)
                if side==1 and i==1: tip.append(nid)
        selected=[]
        for j in range(len(ys)-1):
            eid=len(native.mesh.elements)+1
            native.add_element(eid,create_shell_element(eid,[nodes[0,j],nodes[1,j],nodes[1,j+1],nodes[0,j+1]],
                'm',thickness=manifest['geometry']['thickness'],reference_normal=(0.,0.,1.),
                director_polarity=1,shell_section=section))
            selected.append((eid,1 if side==0 else 3))
        if side==1: selected.reverse()
        edges.append(selected)
    for nid in clamp:
        u,theta=exact_fields(np,native.mesh.nodes[nid].coords(),case)
        native.add_boundary_condition(BoundaryCondition(name=f'left-{nid}',node_ids=[nid],
            dof_constraints=dict(zip(('ux','uy','uz','rx','ry','rz'),map(float,np.r_[u,theta])))))
    raw=MeshTet.init_tensor(manifest['geometry']['solid_x_corners'],ys,manifest['geometry']['solid_z_corners']).oriented()
    initial=SolidMesh(raw.p.T,raw.t.T)
    groups={name:initial.boundary_ids[np.all(abs(initial.coordinates[initial.boundary_facets,0]-x)<1e-12,axis=1)]
            for name,x in (('left',0.),('right',1.))}
    mesh=SolidMesh(initial.coordinates,initial.cells,boundary_groups=groups,
        provenance={'case':case['id'],'physical_core_center_z':0.,'native_reference_z':zref})
    prepared=prepare(mesh,{'elastic_modulus':manifest['material']['E'],'poisson_ratio':manifest['material']['nu']},order=2)
    traces=[ShellEdgeTrace(native,selected,offset=case['trace_offset']) for selected in edges]
    operators=[build_weak_connector(trace,prepared,name,multiplier_breakpoints=[0.,1.])
               for trace,name in zip(traces,('left','right'))]
    actual=native.mesh.dof_manager.total_dofs+prepared.ndof
    rows=sum(op.C_shell.shape[0] for op in operators)
    if actual!=case['planned_primary_dofs'] or rows!=case['planned_multiplier_rows']:
        raise ValueError(f'actual offset dimensions differ from registration: {actual}/{rows}')
    return native,prepared,operators,clamp,tip,section


def resultant(np,native,vector):
    force,moment=np.zeros(3),np.zeros(3)
    for node in native.mesh.nodes.values():
        dofs=native.mesh.dof_manager.get_node_dofs(node.id)
        force+=vector[dofs[:3]]
        moment+=np.cross(node.coords(),vector[dofs[:3]])+vector[dofs[3:]]
    return force,moment


def run_case(np,case,manifest,solve_number):
    from anysolver import LoadCase,assemble_stiffness_matrix
    from anysolver.solids import SolidModel,ResidualScales
    native,prepared,operators,clamp,tip,section=build_case(np,case,manifest)
    refs=case['references']
    scales=ResidualScales(refs['length_ref'],refs['force_ref'],refs['displacement_ref'],tuple(refs['interface_displacement_refs']))
    load=LoadCase(case['id'])
    ys=np.array(manifest['geometry']['y_corners'])
    weights=np.zeros(len(ys));weights[:-1]+=np.diff(ys)/2;weights[1:]+=np.diff(ys)/2
    if not np.array_equal(weights,np.array(manifest['geometry']['native_line_weights'])):
        raise ValueError('consistent edge weights differ from registration')
    for nid,weight in zip(tip,weights):
        load.add_nodal_load(nid,forces=[case['edge_force_x']*weight,0.,0.],
                            moments=[0.,case['edge_moment_y']*weight,0.])
    F=np.zeros(native.mesh.dof_manager.total_dofs)
    for nid,values in load.nodal_loads.items(): F[native.mesh.dof_manager.get_node_dofs(nid)]+=values
    model=SolidModel(native,research_coupling=True,residual_scales={case['id']:scales})
    model.add_region('solid',prepared=prepared)
    for op in operators: model.add_interface('solid',op)
    emit({'type':'solve_start','case':case['id'],'solve_number':solve_number,'configuration':case,
          'registered_scales':vars(scales),'native_nodal_loads':load.nodal_loads,'consistent_line_weights':weights,
          'actual_section':{'A':section.A,'B':section.B,'D':section.D,'As':section.As},
          'physical_core_coordinates':prepared.mesh.coordinates,'physical_core_cells':prepared.mesh.cells,
          'coefficient_coordinates':prepared.coefficient_coordinates,'coefficient_components':prepared.coefficient_components,
          'prepared_signature':prepared.cache_signature(),'production_status':'NO_GO_PRODUCTION_UNQUALIFIED'})
    result=model.solve_static((case['id'],),native_load_cases={case['id']:load})
    q=result.native_displacements[:,0]; a=result.region_coefficients('solid')[:,0]
    Ksh=assemble_stiffness_matrix(native)[0]; Kv=prepared.assemble_linear()
    energy=float(q@Ksh@q+a@Kv@a)
    exact=np.zeros_like(q)
    trans=[];rot=[];actual_center=[];exact_center=[]
    for node in native.mesh.nodes.values():
        dofs=native.mesh.dof_manager.get_node_dofs(node.id)
        u,theta=exact_fields(np,node.coords(),case)
        exact[dofs]=np.r_[u,theta];trans.extend(dofs[:3]);rot.extend(dofs[3:])
        point=np.array(node.coords(),copy=True);point[2]=0.
        center,_=exact_fields(np,point,case)
        exact_center.append(center)
        actual_center.append(q[dofs[:3]]+np.cross(q[dofs[3:]],np.array([0.,0.,case['offset']])))
    displacement_error=float(abs(q[trans]-exact[trans]).max()/refs['displacement_check_scale'])
    rotation_error=float(abs(q[rot]-exact[rot]).max()/refs['rotation_check_scale'])
    center_error=float(abs(np.asarray(actual_center)-np.asarray(exact_center)).max()/refs['displacement_check_scale'])
    recovery=prepared.recover(a)
    expected_stress=np.zeros_like(recovery.stress)
    expected_stress[...,0,0]=(refs['stress_scale'] if case['profile']=='membrane'
        else manifest['material']['E']*refs['curvature']*recovery.coordinates[...,2])
    lo,hi=manifest['sampling']['core_roi_x']
    mask=(recovery.coordinates[...,0]>=lo)&(recovery.coordinates[...,0]<=hi)
    if not np.any(mask): raise ValueError('registered offset stress ROI is empty')
    errors=abs(recovery.stress[mask]-expected_stress[mask]);index=np.unravel_index(np.argmax(errors),errors.shape)
    stress_error=float(errors.max()/refs['stress_scale'])
    fixed=np.array([d for nid in clamp for d in native.mesh.dof_manager.get_node_dofs(nid)],dtype=int)
    support=np.zeros_like(q);support[fixed]=result.reactions[fixed,0]
    external_force,external_moment=resultant(np,native,F)
    support_force,support_moment=resultant(np,native,support)
    force_error=float(np.linalg.norm(external_force+support_force,np.inf)/refs['force_ref'])
    moment_error=float(np.linalg.norm(external_moment+support_moment,np.inf)/refs['moment_ref'])
    external_work=float(q@F);support_work=float(q[fixed]@support[fixed])
    work_error=abs(energy-external_work-support_work)/refs['twice_energy']
    virtual_work=[]
    for i,op in enumerate(operators):
        rng=np.random.default_rng(900+i)
        virtual_q=rng.normal(size=q.shape)*refs['displacement_ref']
        for node in native.mesh.nodes.values(): virtual_q[native.mesh.dof_manager.get_node_dofs(node.id)[3:]]/=refs['length_ref']
        virtual_a=rng.normal(size=prepared.ndof)*refs['displacement_ref']
        lam=rng.normal(size=op.C_shell.shape[0])*refs['force_ref']/(manifest['geometry']['thickness']*manifest['geometry']['width'])
        fs,fv=op.interface_forces(lam)
        left=virtual_q@fs+virtual_a@fv;right=lam@(op.C_shell@virtual_q-op.C_solid@virtual_a)
        virtual_work.append(float(abs(left-right)/refs['virtual_work_ref']))
    energy_error=abs(energy-refs['twice_energy'])/refs['twice_energy']
    residual=result.diagnostics['registered_residual_report'];gates=manifest['thresholds']
    checks={'native_reference_displacement':displacement_error<=gates['field_energy_relative'],
        'native_rotation':rotation_error<=gates['field_energy_relative'],
        'transported_material_center_displacement':center_error<=gates['field_energy_relative'],
        'energy':energy_error<=gates['field_energy_relative'],'stress':stress_error<=gates['stress_scaled_max'],
        'registered_residuals':bool(residual['passed']),'energy_external_support_work':work_error<=gates['work'],
        'operator_virtual_work':max(virtual_work)<=gates['work'],
        'physical_support_plus_all_loads_force':force_error<=gates['resultant'],
        'physical_support_plus_all_loads_moment':moment_error<=gates['resultant']}
    return {'type':'case_result','case':case['id'],'passed':bool(all(checks.values())),'checks':checks,
        'offset_m':case['offset'],'references':refs,'native_reference_coordinates':np.array([n.coords() for n in native.mesh.nodes.values()]),
        'native_coefficients':q,'native_exact_coefficients':exact,'material_center_actual_displacements':actual_center,
        'material_center_exact_displacements':exact_center,'solid_coefficients':a,
        'displacement_error_scaled':displacement_error,'rotation_error_scaled':rotation_error,'center_displacement_error_scaled':center_error,
        'energy_twice_Nm':energy,'energy_relative_error':float(energy_error),'stress_scaled_max':stress_error,
        'stress_coordinates':recovery.coordinates,'actual_stress_Pa':recovery.stress,'reference_stress_Pa':expected_stress,'fixed_roi_mask':mask,
        'controlling_stress_coordinate':recovery.coordinates[mask][index[0]],'controlling_stress_component':list(index[1:]),
        'actual_external_force_N':external_force,'actual_external_moment_Nm':external_moment,
        'support_only_force_N':support_force,'support_only_moment_Nm':support_moment,
        'force_balance_scaled':force_error,'moment_balance_scaled':moment_error,
        'external_work_Nm':external_work,'prescribed_support_work_Nm':support_work,'energy_work_error_scaled':float(work_error),
        'operator_virtual_work_errors':virtual_work,'native_support_dofs':fixed,'native_support_reactions':support[fixed],
        'registered_residual_report':residual,'multipliers':result.multipliers,
        'qualification':'research_only_offset_section_fixture','production_status':'NO_GO_PRODUCTION_UNQUALIFIED'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true',help='Requires independent parent review and explicit numerical authorization')
    args=parser.parse_args();manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    validate_manifest(manifest)
    emit({'type':'study_identity','manifest':manifest,'manifest_sha256':sha(MANIFEST),'harness_sha256':sha(__file__),
          'execution_requested':args.execute,'production_status':'NO_GO_PRODUCTION_UNQUALIFIED'})
    if not args.execute:
        emit({'type':'proposal_only','assemblies':0,'solves':0});return 0
    import numpy as np
    import scipy
    import skfem
    if skfem.__version__!=manifest['runtime']['skfem']: raise ValueError('registered upstream backend version changed')
    emit({'type':'runtime_identity','python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'skfem':skfem.__version__})
    summaries=[];failures=0;attempts=0
    for case in manifest['cases']:
        emit({'type':'case_start','case':case['id'],'configuration':case});started=time.perf_counter()
        try:
            if attempts>=4: raise ValueError('four-case authority exhausted')
            attempts+=1;record=run_case(np,case,manifest,attempts);record['case_wall_seconds']=time.perf_counter()-started
            emit(record)
            summaries.append({k:record[k] for k in ('case','passed','checks','offset_m','displacement_error_scaled','rotation_error_scaled',
                'center_displacement_error_scaled','energy_relative_error','stress_scaled_max','force_balance_scaled','moment_balance_scaled','energy_work_error_scaled')})
        except Exception as exc:
            failures+=1;emit({'type':'case_failure','case':case['id'],'error_type':type(exc).__name__,'error':str(exc),
                'diagnostics':getattr(exc,'diagnostics',None),'case_wall_seconds':time.perf_counter()-started})
            traceback.print_exc(file=sys.stderr);sys.stderr.flush();break
    passed=failures==0 and len(summaries)==4 and all(r['passed'] for r in summaries)
    emit({'type':'study_summary','case_attempts':attempts,'results':summaries,'execution_failures':failures,'passed':bool(passed),
          'claim':'four physical offset section fixtures only; no general offset or production qualification',
          'production_status':'NO_GO_PRODUCTION_UNQUALIFIED'})
    return int(not passed)


if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc:
        emit({'type':'startup_failure','error_type':type(exc).__name__,'error':str(exc)})
        traceback.print_exc(file=sys.stderr);raise SystemExit(1)
