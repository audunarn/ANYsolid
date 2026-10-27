"""Prepared bounded physical-patch proposal; execution needs parent preflight.

Default invocation only describes the frozen inventory. No automatic retry,
penalty fallback, multiplier refinement or production promotion is implemented.
"""
from __future__ import annotations
import argparse
from collections.abc import Mapping
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'docs/extended_patch_manifest.json'


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
        raise ValueError('prospective harness source identity changed')
    cases=manifest['cases']
    bounds=manifest['bounds']
    if len(cases)!=manifest['inventory']['solves'] or len(cases)>bounds['maximum_solves']:
        raise ValueError('prospective solve inventory/count mismatch')
    if len({case['id'] for case in cases})!=len(cases):
        raise ValueError('duplicate prospective case identity')
    for path,expected in manifest['source_and_fixture_hashes'].items():
        if sha(path)!=expected:
            raise ValueError(f'frozen source/fixture changed: {path}')
    for case in cases:
        if case['planned_primary_dofs']>bounds['maximum_primary_dofs'] or case['planned_multiplier_rows']>bounds['maximum_multiplier_rows']:
            raise ValueError('prospective dimensional count exceeds bound')
        if len(case['interfaces'])!=2*len(case['regions']):
            raise ValueError('each replacement needs exactly two distinct transitions')
        corners=case['shell_corners']
        if corners[0]!=0. or corners[-1]!=manifest['geometry']['width'] or any(b<=a for a,b in zip(corners,corners[1:])):
            raise ValueError('native corner partition must increase across the registered width')
        if len(case['shell_cell_types'])!=len(corners)-1 or len(case['native_intervals'])!=len(case['regions'])+1:
            raise ValueError('unsupported shell partition/replacement topology')
        stations=[]
        for i,region in enumerate(case['regions']):
            x0,x1=region['x_corners'][0],region['x_corners'][-1]
            if x0!=case['native_intervals'][i][1] or x1!=case['native_intervals'][i+1][0] or x1<=x0:
                raise ValueError('replaced core and native strips overlap or leave an undeclared gap')
            stations.extend((x0,x1))
            coarse=corners if len(corners)<=len(region['y_corners']) else region['y_corners']
            pair=[f for f in case['interfaces'] if f['region']==region['name']]
            for interface in pair:
                expected=coarse if interface['native_side']=='right' else [manifest['geometry']['width']-y for y in reversed(coarse)]
                if interface['coarser_global_y_corners']!=coarse or interface['multiplier_chart_knots']!=expected:
                    raise ValueError('multiplier partition must retain the frozen coarser corner stations')
        if len(set(stations))!=len(stations):
            raise ValueError('crosspoints/coincident transition stations are outside admission')


def reference_fields(np,points,case):
    points=np.asarray(points)
    X,y,z=points[...,0]+1.,points[...,1]-.5,points[...,2]
    zeros=np.zeros_like(X)
    refs=case['references']
    if case['profile']=='membrane':
        u=np.stack((refs['epsilon']*X,zeros,zeros),axis=-1)
        theta=np.stack((zeros,zeros,zeros),axis=-1)
    elif case['profile']=='bending':
        a=refs['curvature']
        u=np.stack((a*X*z,zeros,-a*X**2/2),axis=-1)
        theta=np.stack((zeros,a*X,zeros),axis=-1)
    elif case['profile']=='width_bending':
        a=refs['curvature']
        u=np.stack((zeros,a*y*z,-a*y**2/2),axis=-1)
        theta=np.stack((-a*y,zeros,zeros),axis=-1)
    else: raise ValueError('unregistered physical profile')
    return u,theta


def build_specimen(np,case,manifest):
    from skfem import MeshTet
    from anysolid import SolidMesh,prepare
    from anysolid.coupling import build_weak_connector
    from anysolver import FEModel,BoundaryCondition
    from anysolver.elements import create_shell_element
    from anysolver.solid_trace import ShellEdgeTrace
    native=FEModel(case['id'])
    E,nu,t=manifest['material']['E'],manifest['material']['nu'],manifest['geometry']['thickness']
    native.add_material('m',E,nu)
    ys=case['shell_corners']
    strip_nodes=[]
    strip_edges=[]
    for strip,(xmin,xmax) in enumerate(case['native_intervals']):
        nodes={}
        for j,y in enumerate(ys):
            for i,x in enumerate((xmin,xmax)):
                nid=len(native.mesh.nodes)+1
                native.add_node(nid,float(x),float(y),0.)
                nodes[i,j]=nid
        edges={'left':[],'right':[]}
        for j,kind in enumerate(case['shell_cell_types']):
            A,B,C,D=nodes[0,j],nodes[1,j],nodes[1,j+1],nodes[0,j+1]
            eid=len(native.mesh.elements)+1
            if kind=='Q4':
                native.add_element(eid,create_shell_element(eid,[A,B,C,D],'m',thickness=t,reference_normal=(0.,0.,1.)))
                edges['right'].append((eid,1)); edges['left'].append((eid,3))
            elif kind=='S3':
                native.add_element(eid,create_shell_element(eid,[A,B,C],'m',thickness=t,reference_normal=(0.,0.,1.)))
                native.add_element(eid+1,create_shell_element(eid+1,[A,C,D],'m',thickness=t,reference_normal=(0.,0.,1.)))
                edges['right'].append((eid,1)); edges['left'].append((eid+1,2))
            else: raise ValueError('unknown prospective shell cell type')
        edges['left'].reverse()
        strip_nodes.append(nodes); strip_edges.append(edges)
    clamp=[strip_nodes[0][0,j] for j in range(len(ys))]
    tip=[strip_nodes[-1][1,j] for j in range(len(ys))]
    for nid in clamp:
        node=native.mesh.nodes[nid]
        u,theta=reference_fields(np,node.coords(),case)
        native.add_boundary_condition(BoundaryCondition(name=f'left-{nid}',node_ids=[nid],
            dof_constraints=dict(zip(('ux','uy','uz','rx','ry','rz'),map(float,np.r_[u,theta])))))
    regions={}
    for region in case['regions']:
        raw=MeshTet.init_tensor(np.array(region['x_corners']),np.array(region['y_corners']),np.array(region['z_corners'])).oriented()
        first=SolidMesh(raw.p.T,raw.t.T)
        groups={}
        for axis,name,values in ((0,'x',(region['x_corners'][0],region['x_corners'][-1])),
                                 (1,'y',(region['y_corners'][0],region['y_corners'][-1]))):
            for side,value in enumerate(values):
                groups[f'{name}{side}']=first.boundary_ids[np.all(abs(first.coordinates[first.boundary_facets,axis]-value)<1e-12,axis=1)]
        mesh=SolidMesh(first.coordinates,first.cells,boundary_groups=groups,
            provenance={'prospective_case':case['id'],'replacement_region':region['name']})
        regions[region['name']]=prepare(mesh,{'elastic_modulus':E,'poisson_ratio':nu},order=2)
    strong=None
    if case['formulation']=='strong_point_diagnostic_v1':
        path=ROOT/'tools/strong_diagnostic.py'
        spec=importlib.util.spec_from_file_location('_extended_strong_point_diagnostic',path)
        strong=importlib.util.module_from_spec(spec); spec.loader.exec_module(strong)
    operators=[]
    for interface in case['interfaces']:
        trace=ShellEdgeTrace(native,strip_edges[interface['native_strip']][interface['native_side']],offset=0.)
        prepared=regions[interface['region']]
        knots=interface['multiplier_chart_knots']
        # Frozen corner knots only: the numerical integration union is never
        # used to select the multiplier space.
        op=(strong.build_strong_point_control(trace,prepared,interface['solid_group']) if strong is not None
            else build_weak_connector(trace,prepared,interface['solid_group'],multiplier_breakpoints=knots))
        operators.append((interface['region'],op))
    count=native.mesh.dof_manager.total_dofs+sum(p.ndof for p in regions.values())
    rows=sum(op.C_shell.shape[0] for _,op in operators)
    if count!=case['planned_primary_dofs'] or rows!=case['planned_multiplier_rows']:
        raise ValueError(f'constructed dimensions differ from registered count: {count}/{rows}')
    if count>manifest['bounds']['maximum_primary_dofs'] or rows>manifest['bounds']['maximum_multiplier_rows']:
        raise ValueError('actual dimensions exceed prospective bounds')
    if any(nid in clamp for nid in tip) or getattr(native,'constraint_equations',()):
        raise ValueError('unsupported support/crosspoint/MPC topology')
    return native,regions,operators,clamp,tip


def physical_resultant(np,native,native_vector,region_vectors,regions):
    force,moment=np.zeros(3),np.zeros(3)
    for node in native.mesh.nodes.values():
        dofs=native.mesh.dof_manager.get_node_dofs(node.id)
        force+=native_vector[dofs[:3]]
        moment+=np.cross(node.coords(),native_vector[dofs[:3]])+native_vector[dofs[3:]]
    for name,values in region_vectors.items():
        prepared=regions[name]
        physical=np.zeros((prepared.ndof,3))
        physical[np.arange(prepared.ndof),prepared.coefficient_components]=values
        force+=physical.sum(axis=0)
        moment+=np.cross(prepared.coefficient_coordinates,physical).sum(axis=0)
    return force,moment


def make_loads(np,native,regions,tip,case,manifest):
    from anysolver import LoadCase
    load=LoadCase(case['id'])
    ys=np.array(case['shell_corners'])
    weights=np.zeros(len(ys))
    weights[:-1]+=np.diff(ys)/2; weights[1:]+=np.diff(ys)/2
    if not np.array_equal(weights,np.array(case['native_right_line_weights'])):
        raise ValueError('physical line weights differ from prospective segment integrals')
    refs=case['references']
    solid_loads={name:np.zeros(p.ndof) for name,p in regions.items()}
    if case['profile'] in ('membrane','bending'):
        for nid,weight in zip(tip,weights):
            force=[refs['applied_force']/manifest['geometry']['width']*weight,0.,0.] if case['profile']=='membrane' else [0.,0.,0.]
            moments=[0.,refs['applied_moment']/manifest['geometry']['width']*weight,0.] if case['profile']=='bending' else [0.,0.,0.]
            load.add_nodal_load(nid,forces=force,moments=moments)
    else:
        M=refs['applied_moment']
        for element in native.mesh.elements.values():
            for yvalue,sign in ((0.,1.),(1.,-1.)):
                selected=[native.mesh.nodes[nid] for nid in element.node_ids if abs(native.mesh.nodes[nid].y-yvalue)<1e-12]
                if len(selected)==2:
                    length=np.linalg.norm(selected[1].coords()-selected[0].coords())
                    for node in selected: load.add_nodal_load(node.id,moments=[sign*M*length/2,0.,0.])
        for name,p in regions.items():
            for side,sign in ((0,-1.),(1,1.)):
                gradient=np.zeros((3,3)); gradient[1,2]=sign*manifest['material']['E']*refs['curvature']
                solid_loads[name]+=p.traction(f'y{side}',[0.,0.,0.],gradient=gradient)
    F=np.zeros(native.mesh.dof_manager.total_dofs)
    for nid,values in load.nodal_loads.items():
        F[native.mesh.dof_manager.get_node_dofs(nid)]+=values
    return load,F,solid_loads,weights


def run_case(np,case,manifest,attempt):
    from anysolver import assemble_stiffness_matrix
    from anysolver.solids import SolidModel,ResidualScales
    native,regions,operators,clamp,tip=build_specimen(np,case,manifest)
    load,F,solid_loads,line_weights=make_loads(np,native,regions,tip,case,manifest)
    refs=case['references']
    scales=ResidualScales(refs['length_ref'],refs['force_ref'],refs['displacement_ref'],tuple(refs['interface_displacement_refs']))
    model=SolidModel(native,research_coupling=True,residual_scales={case['id']:scales})
    for name,p in regions.items(): model.add_region(name,prepared=p).set_load(case['id'],solid_loads[name])
    diagnostic=case['formulation']=='strong_point_diagnostic_v1'
    for name,op in operators:
        if diagnostic: model.add_interface(name,op,diagnostic_strong_tying=True)
        else: model.add_interface(name,op)
    emit({'type':'solve_start','case':case['id'],'solve_number':attempt,'configuration':case,
        'registered_scales':vars(scales),'native_line_integral_weights':line_weights,
        'native_nodal_loads':load.nodal_loads,'solid_loads':solid_loads,
        'prepared_signatures':{name:p.cache_signature() for name,p in regions.items()},
        'operators':[{'region':name,'formulation':op.formulation,'rows':op.C_shell.shape[0],
                      'metadata':dict(op.metadata)} for name,op in operators],
        'production_status':'NO_GO_PRODUCTION_UNQUALIFIED'})
    result=model.solve_static((case['id'],),native_load_cases={case['id']:load})
    q=result.native_displacements[:,0]
    Ksh=assemble_stiffness_matrix(native)[0]
    energy=float(q@Ksh@q)
    applied_work=float(q@F)
    solid_records={}
    stress_error=0.
    for region in case['regions']:
        name=region['name']; p=regions[name]
        a=result.region_coefficients(name)[:,0]
        energy+=float(a@p.assemble_linear()@a)
        applied_work+=float(a@solid_loads[name])
        recovered=p.recover(a)
        exact=np.zeros_like(recovered.stress)
        axis=1 if case['profile']=='width_bending' else 0
        exact[...,axis,axis]=(refs['stress_scale'] if case['profile']=='membrane'
                             else manifest['material']['E']*refs['curvature']*recovered.coordinates[...,2])
        lo,hi=region['stress_roi_x']
        mask=(recovered.coordinates[...,0]>=lo)&(recovered.coordinates[...,0]<=hi)
        if not np.any(mask): raise ValueError('registered core stress region has no quadrature samples')
        errors=abs(recovered.stress[mask]-exact[mask])
        error=float(errors.max()/refs['stress_scale']); stress_error=max(stress_error,error)
        index=np.unravel_index(np.argmax(errors),errors.shape)
        coords=recovered.coordinates[mask]
        solid_records[name]={'coefficients':a,'coordinates_m':recovered.coordinates,
            'actual_stress_Pa':recovered.stress,'reference_stress_Pa':exact,'fixed_roi_mask':mask,
            'stress_scaled_max':error,'controlling_coordinate_m':coords[index[0]],
            'controlling_component':list(index[1:]),'all_component_absolute_errors_Pa':errors.max(axis=0)}
    exact_q=np.zeros_like(q)
    translations=[]; rotations=[]
    for node in native.mesh.nodes.values():
        dofs=native.mesh.dof_manager.get_node_dofs(node.id)
        u,theta=reference_fields(np,node.coords(),case)
        exact_q[dofs]=np.r_[u,theta]
        translations.extend(dofs[:3]); rotations.extend(dofs[3:])
    displacement_error=float(abs(q[translations]-exact_q[translations]).max()/refs['displacement_check_scale'])
    rotation_error=float(abs(q[rotations]-exact_q[rotations]).max()/refs['rotation_check_scale'])
    fixed=np.array([d for nid in clamp for d in native.mesh.dof_manager.get_node_dofs(nid)],dtype=int)
    support=np.zeros_like(q)
    support[fixed]=result.reactions[fixed,0]
    support_work=float(q[fixed]@support[fixed])
    external_force,external_moment=physical_resultant(np,native,F,solid_loads,regions)
    support_force,support_moment=physical_resultant(np,native,support,{},regions)
    force_error=float(np.linalg.norm(external_force+support_force,np.inf)/refs['force_ref'])
    moment_error=float(np.linalg.norm(external_moment+support_moment,np.inf)/(refs['force_ref']*refs['length_ref']))
    work_error=abs(energy-applied_work-support_work)/refs['twice_energy']
    virtual_work_errors=[]
    offset=0
    for interface_index,(name,op) in enumerate(operators):
        rng=np.random.default_rng(7100+interface_index)
        virtual_q=rng.normal(size=q.shape)*refs['displacement_ref']
        for node in native.mesh.nodes.values():
            virtual_q[native.mesh.dof_manager.get_node_dofs(node.id)[3:]]/=refs['length_ref']
        virtual_a=rng.normal(size=regions[name].ndof)*refs['displacement_ref']
        lam_scale=refs['force_ref'] if diagnostic else refs['force_ref']/(manifest['geometry']['width']*manifest['geometry']['thickness'])
        virtual_lam=rng.normal(size=op.C_shell.shape[0])*lam_scale
        fs,fv=op.interface_forces(virtual_lam)
        lhs=virtual_q@fs+virtual_a@fv
        rhs=virtual_lam@(op.C_shell@virtual_q-op.C_solid@virtual_a)
        virtual_work_errors.append(float(abs(lhs-rhs)/(refs['force_ref']*refs['displacement_ref'])))
        offset+=op.C_shell.shape[0]
    energy_error=abs(energy-refs['twice_energy'])/refs['twice_energy']
    residual=result.diagnostics['registered_residual_report']
    gates=manifest['thresholds']
    checks={'native_displacement':displacement_error<=gates['global_field_energy_relative'],
        'native_rotation':rotation_error<=gates['global_field_energy_relative'],
        'energy':energy_error<=gates['global_field_energy_relative'],'stress':stress_error<=gates['stress_scaled_max'],
        'registered_residuals':bool(residual['passed']),'energy_external_support_work':work_error<=gates['work'],
        'operator_virtual_work':max(virtual_work_errors,default=0.)<=gates['work'],
        'support_plus_all_loads_force':force_error<=gates['resultant'],
        'support_plus_all_loads_moment':moment_error<=gates['resultant']}
    return {'type':'case_result','case':case['id'],'passed':bool(all(checks.values())),'checks':checks,
        'qualification':result.diagnostics['qualification'],'formulation':case['formulation'],
        'primary_dofs':case['planned_primary_dofs'],'multiplier_rows':offset,'references':refs,
        'displacement_error_scaled':displacement_error,'rotation_error_scaled':rotation_error,
        'energy_twice_Nm':energy,'energy_relative_error':float(energy_error),'stress_scaled_max':stress_error,
        'support_only_force_N':support_force,'all_applied_force_N':external_force,
        'support_only_moment_Nm':support_moment,'all_applied_moment_Nm':external_moment,
        'force_balance_scaled':force_error,'moment_balance_scaled':moment_error,
        'external_work_Nm':applied_work,'prescribed_support_work_Nm':support_work,
        'energy_work_error_scaled':float(work_error),'operator_virtual_work_errors':virtual_work_errors,
        'native_coefficients':q,'native_reference_coefficients':exact_q,'native_support_dofs':fixed,
        'native_support_reactions':support[fixed],'regions':solid_records,
        'multipliers':result.multipliers,'registered_residual_report':residual,
        'production_status':'NO_GO_PRODUCTION_UNQUALIFIED'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true',help='Only after independent parent preflight and explicit execution authorization')
    args=parser.parse_args()
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    validate_manifest(manifest)
    emit({'type':'study_identity','manifest':manifest,'manifest_sha256':sha(MANIFEST),'harness_sha256':sha(__file__),
          'execution_requested':args.execute,'production_status':'NO_GO_PRODUCTION_UNQUALIFIED'})
    if not args.execute:
        emit({'type':'proposal_only','solves_executed':0,'inventory':manifest['inventory']})
        return 0
    import numpy as np
    import scipy
    import skfem
    if skfem.__version__!=manifest['runtime']['skfem']:
        raise ValueError('registered scikit-fem version changed')
    emit({'type':'runtime_identity','python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'skfem':skfem.__version__})
    summaries=[]; failures=0; attempts=0
    for case in manifest['cases']:
        emit({'type':'case_start','case':case['id'],'configuration':case})
        started=time.perf_counter()
        try:
            if attempts>=manifest['bounds']['maximum_solves']: raise ValueError('registered solve budget exhausted')
            attempts+=1
            record=run_case(np,case,manifest,attempts)
            record['case_wall_seconds']=time.perf_counter()-started
            emit(record)
            summaries.append({k:record[k] for k in ('case','passed','checks','qualification','primary_dofs','multiplier_rows',
                'displacement_error_scaled','rotation_error_scaled','energy_relative_error','stress_scaled_max',
                'force_balance_scaled','moment_balance_scaled','energy_work_error_scaled')})
        except Exception as exc:
            failures+=1
            emit({'type':'case_failure','case':case['id'],'error_type':type(exc).__name__,'error':str(exc),
                  'diagnostics':getattr(exc,'diagnostics',None),'case_wall_seconds':time.perf_counter()-started})
            traceback.print_exc(file=sys.stderr); sys.stderr.flush()
            break
    passed=failures==0 and len(summaries)==len(manifest['cases']) and all(r['passed'] for r in summaries)
    emit({'type':'study_summary','case_attempts':attempts,'case_results':len(summaries),'execution_failures':failures,
          'passed_registered_cases':sum(r['passed'] for r in summaries),'passed':bool(passed),'results':summaries,
          'claim':'finite physical patch cases only, no uniform stability or production promotion',
          'production_status':'NO_GO_PRODUCTION_UNQUALIFIED'})
    return int(not passed)


if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc:
        emit({'type':'startup_failure','error_type':type(exc).__name__,'error':str(exc)})
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(1)
