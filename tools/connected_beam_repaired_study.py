"""Prospective connected beam/shell/solid patch; no engineering joint-stress claim."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from fractions import Fraction
import types

ROOT=Path(__file__).resolve().parents[1]


def load(name,path,digest):
    data=Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('helper bytes differ from registered source')
    module=types.ModuleType(name);module.__file__=str(path)
    sys.modules[name]=module
    exec(compile(data,str(path),'exec'),module.__dict__)
    return module


def main():
    manifest=json.loads((ROOT/'docs/connected_beam_repaired_manifest.json').read_text())
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if manifest['state']!='REVIEWED_READY' or sha(__file__)!=manifest['harness_sha256']:
        raise ValueError('connected study not reviewed or source changed')
    disposition=json.loads((ROOT/'docs/revised_multiplier_disposition.json').read_text())
    if disposition['status']!='PASSED_FINITE_CANDIDATE_B':
        raise ValueError('revised multiplier prerequisite not accepted')
    for path,digest in manifest['source_sha256'].items():
        if sha(path)!=digest:raise ValueError('registered source changed: '+path)
    import numpy as np
    import scipy,scipy.linalg,skfem,anysolid,anysolver
    from threadpoolctl import threadpool_info
    from anysolver import LoadCase,BoundaryCondition,assemble_stiffness_matrix
    from anysolver.elements import BeamElement
    from anysolver.solid_trace import ShellEdgeTrace
    from anysolver.solids import SolidModel,ResidualScales,SolidModelError
    from anysolver.assembly import build_constraint_transformation
    from anysolid.coupling import build_weak_connector
    from anysolid.multiplier import coarsened_p1_partition
    from scipy import sparse
    if {'numpy':np.__version__,'scipy':scipy.__version__,'skfem':skfem.__version__}!=manifest['runtime']:
        raise ValueError('registered runtime changed')
    pools=threadpool_info()
    if any(pool['num_threads']!=1 for pool in pools):raise ValueError('effective pools not one thread')
    for module,source in ((anysolid,ROOT/'src/anysolid'),(anysolver,ROOT.parent/'ANYsolver/src/anysolver')):
        if not Path(module.__file__).resolve().is_relative_to(source):raise ValueError('source owner import escaped checkout')
    fixture_path=ROOT.parent/'ANYsolver/tests/test_solid_coupling.py'
    certificate_path=ROOT/'tools/finite_stability_study.py'
    fixture=load('_connected_fixture',fixture_path,manifest['source_sha256'][str(fixture_path)])
    cert=load('_connected_certificate',certificate_path,manifest['source_sha256'][str(certificate_path)])
    native,prepared,left,right,clamp,tip=fixture.specimen(nshell=1,nsolid=1,nu=0.)
    before={nid:tuple(node.dofs) for nid,node in native.mesh.nodes.items()}
    attached=min(tip,key=lambda nid:native.mesh.nodes[nid].y)
    other=next(nid for nid in tip if nid!=attached)
    end=max(native.mesh.nodes)+1
    native.add_node(end,3.,0.,0.)
    section=manifest['beam_section']
    beam_id=max(native.mesh.elements)+1
    beam=BeamElement(beam_id,[attached,end],'m',cross_section=section)
    native.add_element(beam_id,beam)
    if any(tuple(native.mesh.nodes[nid].dofs)!=dofs for nid,dofs in before.items()):
        raise ValueError('existing native numbering changed')
    for old in (left,right):
        try:old.validate()
        except SolidModelError:pass
        else:raise ValueError('old trace did not invalidate after native block growth')
    traces=[ShellEdgeTrace(native,left.edges),ShellEdgeTrace(native,right.edges)]
    knots=coarsened_p1_partition([0.,1.],[0.,1.])
    operators=[build_weak_connector(trace,prepared,group,multiplier_breakpoints=knots)
               for trace,group in zip(traces,('left','right'))]
    native.add_boundary_condition(BoundaryCondition(name='left-clamp',node_ids=clamp,
        dof_constraints={name:0. for name in ('ux','uy','uz','rx','ry','rz')}))
    native.apply_boundary_conditions()
    ns=native.mesh.dof_manager.total_dofs
    rows=sum(op.C_shell.shape[0] for op in operators)
    if ns+prepared.ndof>manifest['bounds']['primary_dofs'] or rows>manifest['bounds']['multiplier_rows']:
        raise ValueError('prospective dimension bound exceeded')
    load_cases={};F=np.zeros((ns,2))
    scales={}
    for col,registration in enumerate(manifest['cases']):
        lc=LoadCase(registration['id'])
        for nid in (end,other):
            lc.add_nodal_load(nid,forces=[registration['half_force'],0.,0.],
                              moments=[0.,registration['half_moment'],0.])
        for nid,value in lc.nodal_loads.items():F[native.mesh.dof_manager.get_node_dofs(nid),col]+=value
        load_cases[registration['id']]=lc
        scales[registration['id']]=ResidualScales(1.,registration['force_reference'],registration['U'],(registration['U'],)*2)
    model=SolidModel(native,research_coupling=True,residual_scales=scales)
    model.add_region('solid',prepared=prepared)
    for op in operators:model.add_interface('solid',op)
    Ksh,_=assemble_stiffness_matrix(native);Kv=prepared.assemble_linear()
    _,_,Tsh,u0,_,_=build_constraint_transformation(Ksh,F[:,0],native)
    if np.any(u0):raise ValueError('shared supports must be homogeneous')
    K=sparse.block_diag((Ksh,Kv),format='csr')
    P=sparse.block_diag((Tsh,sparse.eye(prepared.ndof)),format='csr')
    C=sparse.vstack([sparse.hstack((op.C_shell,-op.C_solid)) for op in operators],format='csr')
    Kr=(P.T@K@P).tocsr();Kr.sum_duplicates();B=(C@P).tocsr();B.sum_duplicates()
    emit=cert.emit
    emit({'type':'identity','manifest':manifest,'manifest_sha256':sha(ROOT/'docs/connected_beam_repaired_manifest.json'),
          'python':sys.version,'effective_pools':pools,'native_dofs':ns,'solid_dofs':int(prepared.ndof),
          'multiplier_rows':rows,'beam_nodes':[attached,end],'existing_numbers_preserved':True,
          'policy_knots':knots,'joint_model':'common native node; not a resolved continuum joint'})
    deadline=time.perf_counter()+55.
    energy_assessment=cert.finite_positive_energy_check(Kr,B,deadline=deadline)
    symmetry=float(sparse.linalg.norm(K-K.T,ord=np.inf)/sparse.linalg.norm(K,ord=np.inf))
    emit({'type':'energy_assessment','assessment':energy_assessment,'stiffness_relative_asymmetry':symmetry})
    metric=[]
    for registration in manifest['cases']:
        U=registration['U'];force=registration['force_reference']
        if np.any(np.diff(P.indptr)>1) or np.any(P.data!=1.):raise ValueError('selection-only reduction required')
        factor=max(Fraction.from_float(U)/Fraction.from_float(registration['translation_check']),
                   Fraction.from_float(U)/Fraction.from_float(registration['rotation_check']))
        if factor>Fraction.from_float(registration['output_factor']):raise ValueError('registered physical-output factor too small')
        g=np.array([float(Fraction.from_float(U)*sum((Fraction.from_float(float(v)) for v in abs(C.data[C.indptr[i]:C.indptr[i+1]])),Fraction(0)))
                    for i in range(C.shape[0])])
        lam=np.tile([force/.2]*3+[6*force/.2**2]*2,rows//5)
        H=cert.build_scaled_kkt(Kr,B,np.full(Kr.shape[0],force),np.full(Kr.shape[0],U),g,lam)
        bound=cert.certify_inverse_action(H,Kr.shape[0],physical_output_factor=registration['output_factor'],deadline=deadline)
        accepted=bound['verified'] and bound['physical_output_amplification_upper']<=1e6 and bound['modal_traction_couple_amplification_upper']<=5e6
        metric.append(accepted);emit({'type':'metric','case':registration['id'],'passed':accepted,'certificate':bound})
    emit({'type':'solve_start','physical_rhs':2,'case_names':list(load_cases)})
    result=model.solve_static(tuple(load_cases),native_load_cases=load_cases)
    if result.diagnostics['factorization_count']!=1 or result.diagnostics['solve_count']!=2:
        raise ValueError('shared matrix/factorization path not active')
    def saved_csr(matrix):
        matrix=matrix.tocsr(copy=True);matrix.sum_duplicates();matrix.sort_indices()
        return {'shape':matrix.shape,'indptr':matrix.indptr,'indices':matrix.indices,'data':matrix.data}
    emit({'type':'solved_state','native_coefficients':result.native_displacements,
          'solid_coefficients':result.region_coefficients('solid'),'native_loads':F,
          'reactions':result.reactions,'native_stiffness':saved_csr(Ksh),
          'solid_stiffness':saved_csr(Kv),'native_node_coordinates':{nid:node.coords() for nid,node in native.mesh.nodes.items()},
          'native_node_dofs':{nid:native.mesh.dof_manager.get_node_dofs(nid) for nid in native.mesh.nodes},
          'solid_coefficient_coordinates':prepared.coefficient_coordinates,
          'solid_coefficient_components':prepared.coefficient_components})
    beam_K=beam.compute_stiffness_matrix(native.mesh,native.get_material(beam.material_name))
    beam_dofs=beam.get_dof_mapping(native.mesh)
    all_checks=[]
    for col,registration in enumerate(manifest['cases']):
        q=result.native_displacements[:,col];a=result.region_coefficients('solid')[:,col]
        expected=np.zeros_like(q);translations=[];rotations=[]
        for nid,node in native.mesh.nodes.items():
            dofs=native.mesh.dof_manager.get_node_dofs(nid);X=node.x+1.
            value=[.005*X,0.,0.,0.,0.,0.] if registration['id']=='axial' else [0.,0.,-.001*X**2/2,0.,.001*X,0.]
            expected[dofs]=value;translations.extend(dofs[:3]);rotations.extend(dofs[3:])
        xyz=prepared.coefficient_coordinates;X=xyz[:,0]+1.
        physical=np.column_stack((.005*X,np.zeros_like(X),np.zeros_like(X))) if registration['id']=='axial' else np.column_stack((.001*X*xyz[:,2],np.zeros_like(X),-.001*X**2/2))
        exact_solid=physical[np.arange(prepared.ndof),prepared.coefficient_components]
        field=max(float(abs(q[translations]-expected[translations]).max()/registration['translation_check']),
                  float(abs(a-exact_solid).max()/registration['translation_check']))
        rotation=float(abs(q[rotations]-expected[rotations]).max()/registration['rotation_check'])
        recovered=prepared.recover(a);stress_ref=np.zeros_like(recovered.stress)
        stress_ref[...,0,0]=5. if registration['id']=='axial' else recovered.coordinates[...,2]
        mask=(recovered.coordinates[...,0]>=.25)&(recovered.coordinates[...,0]<=.75)
        stress=float(abs(recovered.stress[mask]-stress_ref[mask]).max()/registration['stress_check'])
        energy=float(q@Ksh@q+a@Kv@a);work=float(q@F[:,col])
        fixed=np.array([d for nid in clamp for d in native.mesh.dof_manager.get_node_dofs(nid)])
        support=np.zeros_like(q);support[fixed]=result.reactions[fixed,col]
        vector=support+F[:,col];force=np.zeros(3);moment=np.zeros(3)
        for node in native.mesh.nodes.values():
            dofs=node.dofs;force+=vector[dofs[:3]];moment+=np.cross(node.coords(),vector[dofs[:3]])+vector[dofs[3:]]
        internal=beam_K@q[beam_dofs];beam_ref=np.zeros(12)
        beam_ref[0]=-registration['half_force'];beam_ref[6]=registration['half_force']
        beam_ref[4]=-registration['half_moment'];beam_ref[10]=registration['half_moment']
        joint=float(abs(internal-beam_ref).max()/registration['force_reference'])
        virtual=[]
        for op in operators:
            vq=np.linspace(-1.,1.,ns)*registration['U']
            va=np.linspace(.7,-.3,prepared.ndof)*registration['U']
            vl=np.linspace(-.4,.6,op.C_shell.shape[0])*registration['force_reference']/.2
            fs,fv=op.interface_forces(vl)
            virtual.append(abs(vq@fs+va@fv-vl@(op.C_shell@vq-op.C_solid@va))/(registration['force_reference']*registration['U']))
        checks={'field':field<=.009,'rotation':rotation<=.009,'stress':stress<=.045,
                'energy':abs(energy-registration['twice_energy'])/registration['twice_energy']<=.009,
                'work':abs(energy-work)/registration['twice_energy']<=1e-10,
                'support_force':np.linalg.norm(force,np.inf)/registration['force_reference']<=1e-8,
                'support_moment':np.linalg.norm(moment,np.inf)/registration['force_reference']<=1e-8,
                'beam_end_actions':joint<=1e-8,
                'finite_positive_energy':bool(energy_assessment['positive_energy']),
                'symmetry':symmetry<=1e-10,'operator_virtual_work':max(virtual)<=1e-10,
                'residuals':bool(result.diagnostics['registered_residual_report']['per_case'][col]['passed'])}
        checks={key:bool(value) for key,value in checks.items()};all_checks.append(all(checks.values()))
        emit({'type':'physical_result','case':registration['id'],'checks':checks,'field_error':field,
              'rotation_error':rotation,'stress_error':stress,'energy':energy,'work':work,'joint_error':joint,
              'native_coefficients':q,'reference_native_coefficients':expected,'solid_coefficients':a,
              'reference_solid_coefficients':exact_solid,'beam_internal_actions':internal,'beam_reference_actions':beam_ref,
              'registered_report':result.diagnostics['registered_residual_report']['per_case'][col]})
    passed=all(metric) and all(all_checks)
    emit({'type':'study_summary','passed':passed,'metric_cases':2,'physical_rhs':2,
          'host_factorizations':result.diagnostics['factorization_count'],'production':'research_only'})
    return int(not passed)


if __name__=='__main__':raise SystemExit(main())
