"""Bounded repeated-load measurement on the reviewed two-region research fixture."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import sys
from unittest.mock import patch
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
from anysolver import LoadCase,assemble_stiffness_matrix
from anysolver.assembly import build_constraint_transformation
from anysolver.solids import SolidModel,ResidualScales

ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def main():
    path=ROOT/'docs/coupled_load_manifest.json'
    manifest=json.loads(path.read_text())
    if manifest['state']!='REVIEWED_READY':raise ValueError('measurement registration is not ready or is consumed')
    import scipy,skfem
    from threadpoolctl import threadpool_info
    pools=threadpool_info()
    if any(pool['num_threads']!=1 for pool in pools):raise ValueError('effective numeric pools must be single threaded')
    if {'numpy':np.__version__,'scipy':scipy.__version__,'skfem':skfem.__version__}!=manifest['runtime']:
        raise ValueError('registered numerical runtime changed')
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    if sha(__file__)!=manifest['harness_sha256']:
        raise ValueError('measurement harness changed')
    for source,digest in manifest['source_sha256'].items():
        if sha(source)!=digest: raise ValueError('frozen source changed: '+source)
    counts=manifest['counts']
    if sum(counts)>manifest['bounds']['host_rhs'] or manifest['bounds']['reference_rhs']!=2:
        raise ValueError('prospective RHS budget mismatch')
    helper=load('_reviewed_extended_fixture',ROOT/'tools/extended_patch_study.py')
    measurement=load('_all_solid_measurement_helpers',ROOT/'tools/repeated_load_study.py')
    emit=helper.emit
    emit({'type':'identity','manifest':manifest,'manifest_sha256':sha(path),'memory':measurement.memory(),
          'python':sys.version,'effective_pools':pools})
    original=json.loads((ROOT/'docs/extended_patch_manifest.json').read_text())
    case=copy.deepcopy(next(c for c in original['cases'] if c['id']=='two_replacements_four_transitions'))
    import anysolid
    import anysolid.coupling
    prepare=anysolid.prepare; couple=anysolid.coupling.build_weak_connector
    timing={'backend_preparation_seconds':0.,'coupling_seconds':0.,'coupling_build_count':0}
    def timed_prepare(*args,**kwargs):
        started=time.perf_counter();value=prepare(*args,**kwargs)
        timing['backend_preparation_seconds']+=time.perf_counter()-started;return value
    def timed_coupling(*args,**kwargs):
        started=time.perf_counter();value=couple(*args,**kwargs)
        timing['coupling_seconds']+=time.perf_counter()-started
        timing['coupling_build_count']+=1;return value
    started=time.perf_counter()
    with patch.object(anysolid,'prepare',timed_prepare),patch.object(anysolid.coupling,'build_weak_connector',timed_coupling):
        native,regions,operators,clamp,tip=helper.build_specimen(np,case,original)
    setup_seconds=time.perf_counter()-started
    native.apply_boundary_conditions()
    ns=native.mesh.dof_manager.total_dofs
    started=time.perf_counter()
    Ksh,_=assemble_stiffness_matrix(native)
    Ks=[p.assemble_linear() for p in regions.values()]
    K=sparse.block_diag([Ksh,*Ks],format='csr')
    assembly_seconds=time.perf_counter()-started
    _,_,Tsh,u0,_,_=build_constraint_transformation(Ksh,np.zeros(ns),native)
    if np.any(u0): raise ValueError('registered shared supports must be homogeneous')
    P=sparse.block_diag([Tsh,*[sparse.eye(p.ndof) for p in regions.values()]],format='csr')
    rows=[]
    for name,op in operators:
        rows.append(sparse.hstack([op.C_shell,*[-op.C_solid if key==name else sparse.csr_matrix((op.C_shell.shape[0],p.ndof))
                            for key,p in regions.items()]],format='csr'))
    C=sparse.vstack(rows,format='csr'); B=(C@P).tocsr()
    D=sparse.diags(1/np.sqrt(np.asarray(B.multiply(B).sum(axis=1)).ravel()))
    A=sparse.bmat([[P.T@K@P,(D@B).T],[D@B,None]],format='csc')
    if K.shape[0]>manifest['bounds']['primary_dofs'] or C.shape[0]>manifest['bounds']['multiplier_rows']:
        raise ValueError('prospective dimension bound exceeded before factorization')
    weights=np.asarray(case['native_right_line_weights'])
    moment=case['references']['applied_moment']
    basis=np.zeros((K.shape[0],2))
    for nid,weight in zip(tip,weights):
        dofs=native.mesh.dof_manager.get_node_dofs(nid)
        basis[dofs[0],0]=weight
        basis[dofs[4],1]=weight*moment
    reference_load=np.vstack((np.asarray(P.T@basis),np.zeros((C.shape[0],2))))
    ref=splu(A).solve(reference_load)
    reference=np.asarray(P@ref[:P.shape[1]])
    model=SolidModel(native,research_coupling=True)
    slices={}; cursor=ns
    for name,p in regions.items():
        model.add_region(name,prepared=p)
        slices[name]=slice(cursor,cursor+p.ndof); cursor+=p.ndof
    for name,op in operators:model.add_interface(name,op)
    tensors={name:[p.recover(reference[slices[name],i]) for i in range(2)] for name,p in regions.items()}
    signatures={name:p.cache_signature() for name,p in regions.items()}
    map6=np.zeros((6,ns))
    for nid,node in native.mesh.nodes.items():
        dofs=native.mesh.dof_manager.get_node_dofs(nid)
        map6[:3,dofs[:3]]=np.eye(3)
        map6[3:,dofs[:3]]=np.cross(node.coords(),np.eye(3)).T
        map6[3:,dofs[3:]]=np.eye(3)
    fixed=np.array([d for nid in clamp for d in native.mesh.dof_manager.get_node_dofs(nid)])
    scales=ResidualScales(1.,manifest['force_reference'],manifest['displacement_reference'],
                         (manifest['displacement_reference'],)*len(operators))
    emit({'type':'preparation','primary_dofs':K.shape[0],'multiplier_rows':C.shape[0],
          'regions':len(regions),'interfaces':len(operators),'setup_including_conversion_and_coupling_seconds':setup_seconds,
          **timing,'native_geometry_and_mesh_conversion_remainder_seconds':setup_seconds-timing['backend_preparation_seconds']-timing['coupling_seconds'],
          'stiffness_assembly_seconds':assembly_seconds,'reference_factorizations':1,'reference_rhs':2,
          'stiffness_array_bytes':K.data.nbytes+K.indices.nbytes+K.indptr.nbytes,
          'constraint_array_bytes':C.data.nbytes+C.indices.nbytes+C.indptr.nbytes})
    total=0; previous_solve=0.
    for count in counts:
        names=tuple(f'rhs-{i}' for i in range(count))
        i=np.arange(count); combination=np.vstack((1+.1*np.sin(i),.2*np.cos(i)))
        native_cases={}
        for k,name in enumerate(names):
            lc=LoadCase(name)
            for nid,weight in zip(tip,weights):
                lc.add_nodal_load(nid,forces=[combination[0,k]*weight,0.,0.],
                                  moments=[0.,combination[1,k]*moment*weight,0.])
            native_cases[name]=lc
        started=time.perf_counter()
        result=model.solve_static(names,native_load_cases=native_cases,residual_scales={name:scales for name in names})
        host_seconds=time.perf_counter()-started
        total+=count; diag=result.diagnostics
        if diag['factorization_count']!=1 or diag['solve_count']!=total or bool(diag['cache_hit'])!=(total>count):
            raise ValueError('host factorization reuse counters mismatch')
        expected=reference@combination
        coeff=max(measurement.relative(result.coefficients[:,k],expected[:,k]) for k in range(count))
        stress=0.; strain=0.; recovery_seconds=0.
        for name,p in regions.items():
            for k in range(count):
                started=time.perf_counter(); actual=p.recover(result.region_coefficients(name)[:,k]); recovery_seconds+=time.perf_counter()-started
                stress=max(stress,measurement.relative(actual.stress,sum(combination[j,k]*tensors[name][j].stress for j in range(2))))
                strain=max(strain,measurement.relative(actual.strain,sum(combination[j,k]*tensors[name][j].strain for j in range(2))))
        loads=basis@combination
        energies=np.sum(result.coefficients*(K@result.coefficients),axis=0)
        work=np.sum(result.coefficients*loads,axis=0)
        work_error=max(measurement.relative(energies[k:k+1],work[k:k+1]) for k in range(count))
        support=np.zeros((ns,count));support[fixed]=result.reactions[fixed]
        balance=map6@(support+loads[:ns])
        force=float(np.max(abs(balance[:3]))/scales.force)
        couple=float(np.max(abs(balance[3:]))/(scales.force*scales.length))
        checks={'coefficient_tensor_equivalence':max(coeff,strain,stress)<=manifest['equivalence_limit'],
                'work':work_error<=1e-10,'force_moment':max(force,couple)<=1e-8,
                'registered_residual':bool(diag['registered_residual_report']['passed']),
                'signatures':signatures=={name:p.cache_signature() for name,p in regions.items()},
                'research_only':diag['qualification']=='research_only'}
        emit({'type':'batch','rhs':count,'recovered_rhs_per_region':count,'host_total_seconds':host_seconds,
              'factorization_seconds_cumulative':diag['factorization_time'],'solve_seconds_increment':diag['solve_time']-previous_solve,
              'complete_recovery_seconds':recovery_seconds,'host_factorizations':diag['factorization_count'],
              'host_solve_count_cumulative':diag['solve_count'],'cache_hit':bool(diag['cache_hit']),
              'coefficient_error':coeff,'strain_error':strain,'stress_error':stress,'work_error':work_error,
              'force_error':force,'moment_error':couple,'checks':checks,'memory':measurement.memory(),
              'coefficient_array_bytes':result.coefficients.nbytes})
        if not all(checks.values()):raise ValueError('coupled repeated-load acceptance failed; no retry')
        previous_solve=diag['solve_time'];del result
    emit({'type':'terminal','status':'passed_scoped_reuse_measurement','host_rhs':total,
          'reference_rhs':2,'production':'NO_GO','condensation':'disabled'})


if __name__=='__main__':main()
