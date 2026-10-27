"""Prospective membrane-only interface-distance study. Default: no FE imports."""
from __future__ import annotations
import argparse
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
MANIFEST=ROOT/'docs/transition_distance_manifest.json'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def emit(record):
    def convert(value):
        if hasattr(value,'tolist'): return value.tolist()
        if hasattr(value,'item'): return value.item()
        raise TypeError(type(value).__name__)
    print(json.dumps(record,default=convert,allow_nan=False,sort_keys=True),flush=True)


def check_time(deadline):
    if time.perf_counter()>=deadline: raise TimeoutError('registered transition-study deadline')


def ratio(value):
    if isinstance(value,bool) or not math.isfinite(float(value)): raise ValueError('finite binary numeric input required')
    n,d=float(value).as_integer_ratio()
    return n,d.bit_length()-1


def exact_quadratic(indptr,indices,data,q,deadline=math.inf):
    """Exact dyadic accumulation, no rounded products and no Fraction per term."""
    qr=[ratio(v) for v in q];bins={}
    if len(indptr)!=len(q)+1 or indptr[0]!=0 or indptr[-1]!=len(data) or len(indices)!=len(data): raise ValueError('CSR dimensions')
    for i in range(len(q)):
        check_time(deadline)
        a,b=int(indptr[i]),int(indptr[i+1])
        if not 0<=a<=b<=len(data): raise ValueError('CSR pointers')
        for k in range(a,b):
            j=int(indices[k])
            if not 0<=j<len(q): raise ValueError('CSR index')
            n,e=ratio(data[k]);ni,ei=qr[i];nj,ej=qr[j];power=e+ei+ej
            bins[power]=bins.get(power,0)+n*ni*nj
    power=max(bins,default=0)
    return Fraction(sum(n<<(power-e) for e,n in bins.items()),1<<power)


def exact_dot(a,b):
    if len(a)!=len(b): raise ValueError('dot dimensions')
    return sum((Fraction(float(x))*Fraction(float(y)) for x,y in zip(a,b)),Fraction(0))


def cases():
    result=[]
    for length,nx,ns in ((.5,4,5),(1.,8,4),(1.5,12,3)):
        primary=3*(2*nx+1)*5*5+36*(ns+1)
        result.append({'id':f'core_length_{length:g}','core_x':[.5-length/2,.5+length/2],
            'core_grid':[nx,2,2],'native_axial_each_side':ns,'native_width_intervals':2,
            'primary':primary,'reduced':primary-18,'multiplier_rows':20,'KKT':primary+2,
            'minimum_ROI_interface_distance':length/2-.0625})
    return result


def triangular_line_weights():
    ys=[0.,.5,1.];weights=[0.,0.,0.]
    for j in range(2):
        h=ys[j+1]-ys[j];ql=4*min(ys[j],1-ys[j]);qr=4*min(ys[j+1],1-ys[j+1])
        weights[j]+=h*(2*ql+qr)/6;weights[j+1]+=h*(ql+2*qr)/6
    return weights


def output_factor():
    return math.ceil(max(Fraction(.03)/Fraction(.015),Fraction(.03)/Fraction(.005)))


def validate(manifest):
    if sha(__file__)!=manifest['harness_sha256']: raise ValueError('prospective runner changed')
    for path,expected in manifest['source_sha256'].items():
        if sha(path)!=expected: raise ValueError(f'frozen input/source changed: {path}')
    if manifest['cases']!=cases(): raise ValueError('prospective geometry/count changed')
    if manifest['bounds']!={'coupled_primary':2100,'coupled_KKT':2100,'coupled_reduced':2100,'multiplier':20,'reference_primary':50000,'physical_solves':5,'inverse_assessments':3,'outer_seconds':180,'inner_seconds':175}:
        raise ValueError('prospective bounds changed')
    if manifest['references']!=[{'grid':[12,8,2],'primary':6375},{'grid':[24,16,4],'primary':43659}]: raise ValueError('reference inventory changed')
    if manifest['criteria']!={'reference_field_energy':.001,'reference_stress':.005,'physical_field_energy':.01,'physical_stress':.05,
        'measured_field_energy':.009,'measured_stress':.045,'registered_residual':1e-9,'work_symmetry':1e-10,'force_moment':1e-8,'physical_output_amplification':1e6,'modal_amplification':5e6}:
        raise ValueError('prospective scientific criteria changed')


def load_numerics(manifest):
    path=manifest['numerics_path'];payload=Path(path).read_bytes()
    if hashlib.sha256(payload).hexdigest()!=manifest['source_sha256'][path]: raise ValueError('numerical helper changed')
    module=types.ModuleType('_transition_frozen_certificate');module.__file__=path
    exec(compile(payload,path,'exec'),module.__dict__)
    return module


def solid(np,xs,grid,name):
    from skfem import MeshTet
    from anysolid import SolidMesh,prepare
    nx,ny,nz=grid
    raw=MeshTet.init_tensor(np.linspace(*xs,nx+1),np.linspace(0.,1.,ny+1),np.linspace(-.1,.1,nz+1)).oriented()
    initial=SolidMesh(raw.p.T,raw.t.T);xyz=initial.coordinates[initial.boundary_facets]
    left=np.all(xyz[:,:,0]==xs[0],axis=1);right=np.all(xyz[:,:,0]==xs[1],axis=1)
    low=np.all(xyz[:,:,1]<=.5,axis=1);high=np.all(xyz[:,:,1]>=.5,axis=1)
    groups={'left':initial.boundary_ids[left],'right':initial.boundary_ids[right],
            'right_low':initial.boundary_ids[right&low],'right_high':initial.boundary_ids[right&high]}
    return prepare(SolidMesh(initial.coordinates,initial.cells,boundary_groups=groups,provenance={'study':name}),{'elastic_modulus':1000.,'poisson_ratio':0.},order=2)


def point_stress(np,prepared,a,points):
    """Verification-only upstream gbasis gradients, pinned scikit-fem12.0.2.

    On an internal mesh face use the upstream element_finder's deterministic
    selected cell, with no smoothing/averaging/exclusion. No native FE kernel.
    """
    from skfem.element import DiscreteField
    from skfem.helpers import sym_grad
    from skfem.models.elasticity import linear_stress
    b=prepared._basis;x=np.asarray(points).T
    cells=b.mesh.element_finder(mapping=b.mapping)(*x);local=b.mapping.invF(x[:,:,None],tind=cells)
    grad=np.zeros((3,3,len(points)))
    for k in range(b.Nbfun):
        field=b.elem.gbasis(b.mapping,local,k,tind=cells)[0]
        grad+=field.grad[...,0]*a[b.element_dofs[k,cells]][None,None,:]
    field=DiscreteField(value=np.zeros((3,len(points))),grad=grad)
    stress=linear_stress(prepared._lam,prepared._mu)(sym_grad(field))
    return np.moveaxis(stress,(0,1),(-2,-1))


def resultant(np,p,f):
    vector=np.zeros((p.ndof,3));vector[np.arange(p.ndof),p.coefficient_components]=f
    return vector.sum(axis=0),np.cross(p.coefficient_coordinates,vector).sum(axis=0)


def exact_work(K,q,F,normalizer,deadline):
    energy=exact_quadratic(K.indptr,K.indices,K.data,q,deadline);work=exact_dot(q,F)
    return energy,work,abs(energy-work)/Fraction(normalizer)


def rational(x): return {'numerator':str(x.numerator),'denominator':str(x.denominator),'display':float(x)}


def reference(np,registration,deadline,counts):
    from scipy.sparse.linalg import splu,norm
    p=solid(np,[-1.,2.],registration['grid'],'independent_whole_body_reference')
    if p.ndof!=registration['primary'] or p.ndof>50000: raise ValueError('reference primary bound')
    K=p.assemble_linear();f=np.zeros(p.ndof)
    low=np.zeros((3,3));low[0,1]=20.;high=-low
    f+=p.traction('right_low',[0.,0.,0.],gradient=low)
    f+=p.traction('right_high',[20.,0.,0.],gradient=high)
    fixed=p.boundary_dofs('left');free=np.setdiff1d(np.arange(p.ndof),fixed)
    emit({'type':'reference_solve_start','registration':registration,'ndof':p.ndof,'matrix_shape':K.shape,'matrix_nnz':K.nnz,
          'matrix_data_sha256':hashlib.sha256(K.indptr.tobytes()+K.indices.tobytes()+K.data.tobytes()).hexdigest(),
          'fixed_dofs':fixed,'actual_affine_surface_load':f,'prepared_signature':p.cache_signature(),
          'route':'whole-body upstream P2, direct SciPy free-DOF LU; no native or coupling imports'})
    check_time(deadline);counts['reference_attempts']+=1
    a=np.zeros(p.ndof);a[free]=splu(K[free][:,free].tocsc()).solve(f[free]);counts['reference_solved']+=1
    reaction=K@a-f;support=np.zeros(p.ndof);support[fixed]=reaction[fixed]
    residual=float(abs(reaction[free]).max()/1.)
    energy,work,error=exact_work(K,a,f,.015,deadline)
    force,moment=resultant(np,p,f+support)
    symmetry=float(norm(K-K.T,np.inf)/norm(K,np.inf))
    recovered=p.recover(a);own=point_stress(np,p,a,recovered.coordinates.reshape(-1,3)).reshape(recovered.stress.shape)
    probe_error=float(abs(own-recovered.stress).max()/5.)
    checks={'residual':residual<=1e-9,'exact_work':error<=Fraction(1e-10),'force':float(abs(force).max())<=1e-8,
            'moment':float(abs(moment).max())<=1e-8,'symmetry':symmetry<=1e-10,'upstream_gradient_probe':probe_error<=1e-10}
    emit({'type':'reference_result','registration':registration,'checks':checks,'passed':all(checks.values()),'coefficients':a,
          'coefficient_coordinates':p.coefficient_coordinates,'coefficient_components':p.coefficient_components,
          'mesh_coordinates':p.mesh.coordinates,'mesh_cells':p.mesh.cells,'support_reactions':support[fixed],
          'all_quad_coordinates':recovered.coordinates,'all_quad_stress':recovered.stress,'energy':rational(energy),'external_work':rational(work),
          'exact_work_error':rational(error),'free_force_residual_scaled':residual,'force_balance':force,'moment_balance':moment,
          'probe_self_check_error':probe_error,'physical_symmetry':symmetry})
    return {'p':p,'a':a,'energy':float(energy),'passed':all(checks.values())}


def native_model(np,case):
    from anysolver import FEModel,BoundaryCondition,LoadCase
    from anysolver.elements import create_shell_element
    from anysolver.solid_trace import ShellEdgeTrace
    native=FEModel(case['id']);native.add_material('m',1000.,0.);load=LoadCase(case['id']);ends=[];clamp=[];tip=[]
    x0,x1=case['core_x'];ns=case['native_axial_each_side'];ys=[0.,.5,1.]
    for strip,xs in enumerate((np.linspace(-1.,x0,ns+1),np.linspace(x1,2.,ns+1))):
        nodes={};edges=[]
        for j,y in enumerate(ys):
            for i,x in enumerate(xs):
                nid=len(native.mesh.nodes)+1;native.add_node(nid,float(x),y,0.);nodes[i,j]=nid
        for j in range(2):
            for i in range(ns):
                eid=len(native.mesh.elements)+1
                native.add_element(eid,create_shell_element(eid,[nodes[i,j],nodes[i+1,j],nodes[i+1,j+1],nodes[i,j+1]],'m',thickness=.2,reference_normal=(0.,0.,1.)))
                if i==(ns-1 if strip==0 else 0): edges.append((eid,1 if strip==0 else 3))
        if strip==0: clamp=[nodes[0,j] for j in range(3)]
        else: edges.reverse();tip=[nodes[ns,j] for j in range(3)]
        ends.append(edges)
    for nid in clamp: native.add_boundary_condition(BoundaryCondition(name=f'clamp{nid}',node_ids=[nid],dof_constraints={n:0. for n in ('ux','uy','uz','rx','ry','rz')}))
    weights=triangular_line_weights()
    for nid,weight in zip(tip,weights): load.add_nodal_load(nid,forces=[weight,0.,0.])
    return native,load,[ShellEdgeTrace(native,edge,offset=0.) for edge in ends],clamp,weights


def coupled(np,case,p,fine,samples,numerics,deadline,counts):
    from scipy import sparse
    from anysolid.coupling import build_weak_connector
    from anysolid.multiplier import coarsened_p1_partition
    from anysolver.assembly import assemble_system,build_constraint_transformation
    from anysolver.solids import SolidModel,ResidualScales
    native,load,traces,clamp,weights=native_model(np,case)
    knots=coarsened_p1_partition([0.,.5,1.],[0.,.5,1.]);ops=[build_weak_connector(traces[0],p,'left',multiplier_breakpoints=knots),build_weak_connector(traces[1],p,'right',multiplier_breakpoints=[1.-v for v in reversed(knots)])]
    F=np.zeros(native.mesh.dof_manager.total_dofs)
    for nid,values in load.nodal_loads.items(): F[native.mesh.dof_manager.get_node_dofs(nid)]+=values
    native.apply_boundary_conditions();Ksh,_,_=assemble_system(native,load);_,_,Tsh,u0,_,_=build_constraint_transformation(Ksh,F,native)
    Kv=p.assemble_linear();K=sparse.block_diag((Ksh,Kv),format='csr');P=sparse.block_diag((Tsh,sparse.eye(p.ndof)),format='csr');P.sum_duplicates();P.eliminate_zeros();cols=P.tocsc()
    if np.any(np.diff(cols.indptr)!=1) or np.any(cols.data!=1.) or np.any(np.diff(P.indptr)>1) or np.any(u0): raise ValueError('selection supports/homogeneous family changed')
    free=cols.indices;C=sparse.vstack([sparse.hstack((o.C_shell,-o.C_solid)) for o in ops],format='csr');C.sum_duplicates();C.eliminate_zeros()
    Kr=K[free][:,free].tocsr();B=C[:,free].tocsr()
    for v in (Kr,B):v.sum_duplicates();v.eliminate_zeros()
    r,m=B.shape[1],B.shape[0]
    if (K.shape[0],r,m,r+m)!=(case['primary'],case['reduced'],20,case['KKT']) or max(K.shape[0],r+m)>2100: raise ValueError('new explicitly registered dimensions exceeded')
    U=.03;G=np.array([float(Fraction(U)*sum(abs(Fraction(float(v))) for v in C.data[C.indptr[i]:C.indptr[i+1]])) for i in range(m)])
    S=np.ones(r);T=np.full(r,U);Lambda=np.tile([5.,5.,5.,150.,150.],m//5)
    H=numerics.build_scaled_kkt(Kr,B,S,T,G,Lambda)
    payload=lambda v:{'shape':v.shape,'indptr':v.indptr,'indices':v.indices,'data':v.data}
    emit({'type':'metric_start','case':case,'canonical_Kr':payload(Kr),'canonical_B':payload(B),'formed_H':payload(H),
          'free':free,'scales':{'S':S,'T':T,'G':G,'Lambda':Lambda,'D':'all1 becauseL1','s':'all1 selectionP'},'output_factor':output_factor(),
          'operator_metadata':[dict(o.metadata) for o in ops],'row_units':'five physical section modes; no knot-dependent renormalization'})
    counts['metric_attempts']+=1
    cert=numerics.certify_inverse_action(H,r,physical_output_factor=output_factor(),block_columns=64,deadline=deadline,progress=lambda rec:emit({'type':'inverse_progress','case':case['id'],**rec}))
    positive=numerics.finite_positive_energy_check(Kr,B,maximum_reduced=2100,deadline=deadline);counts['metric_results']+=1
    emit({'type':'metric_result','case':case['id'],'certificate':cert,'finite_positive_energy':positive})
    model=SolidModel(native,research_coupling=True,residual_scales={case['id']:ResidualScales(1.,1.,U,(U,U))});model.add_region('core',prepared=p)
    for op in ops:model.add_interface('core',op)
    emit({'type':'coupled_solve_start','case':case,'native_loads':load.nodal_loads,'native_line_weights':weights,'solid_mesh_coordinates':p.mesh.coordinates,
          'solid_mesh_cells':p.mesh.cells,'native_nodes':{n.id:n.coords() for n in native.mesh.nodes.values()},'prepared_signature':p.cache_signature()})
    check_time(deadline);counts['coupled_attempts']+=1
    result=model.solve_static((case['id'],),native_load_cases={case['id']:load});counts['coupled_solved']+=1
    q=result.native_displacements[:,0];a=result.region_coefficients('core')[:,0];allq=np.r_[q,a];allF=np.r_[F,np.zeros(p.ndof)]
    energy,work,werror=exact_work(K,allq,allF,.015,deadline)
    points=np.array([n.coords() for n in native.mesh.nodes.values()]);expected=(fine['p'].trace(points)@fine['a']).reshape(-1,3)
    actual=np.array([q[native.mesh.dof_manager.get_node_dofs(n.id)[:3]] for n in native.mesh.nodes.values()])
    native_error=float(abs(actual-expected).max()/.015)
    values=(fine['p'].trace(p.coefficient_coordinates)@fine['a']).reshape(-1,3);exact_a=values[np.arange(p.ndof),p.coefficient_components]
    core_error=float(abs(a-exact_a).max()/.015);energy_error=abs(float(energy)-fine['energy'])/fine['energy']
    recovered=p.recover(a);mask=(recovered.coordinates[...,0]>=.4375)&(recovered.coordinates[...,0]<=.5625)
    actual_stress=recovered.stress[mask];reference_stress=point_stress(np,fine['p'],fine['a'],recovered.coordinates[mask]);stress=float(abs(actual_stress-reference_stress).max()/5.)
    fixed=[d for nid in clamp for d in native.mesh.dof_manager.get_node_dofs(nid)];support=np.zeros_like(q);support[fixed]=result.reactions[fixed,0]
    force=np.zeros(3);moment=np.zeros(3)
    for n in native.mesh.nodes.values():
        dofs=native.mesh.dof_manager.get_node_dofs(n.id);v=F[dofs]+support[dofs];force+=v[:3];moment+=np.cross(n.coords(),v[:3])+v[3:]
    virtual=[]
    for i,op in enumerate(ops):
        rng=np.random.default_rng(7100+i);vq=rng.normal(size=q.shape)*U;va=rng.normal(size=a.shape)*U;vl=rng.normal(size=op.C_shell.shape[0])*5.
        fs,fv=op.interface_forces(vl);virtual.append(float(abs(vq@fs+va@fv-vl@(op.C_shell@vq-op.C_solid@va))/U))
    rotations=np.array([q[native.mesh.dof_manager.get_node_dofs(n.id)[3:]] for n in native.mesh.nodes.values()]);tilt=float(abs(rotations[:,:2]).max()/.005)
    symmetry=float(sparse.linalg.norm(K-K.T,np.inf)/sparse.linalg.norm(K,np.inf));residual=result.diagnostics['registered_residual_report']
    flags={'inverse_verified':cert['verified'],'physical_output_allocation':cert.get('physical_output_amplification_upper',math.inf)<=1e6,
        'modal_allocation':cert.get('modal_traction_couple_amplification_upper',math.inf)<=5e6,'finite_positive_energy':positive.get('positive_energy',False),
        'global_displacement':max(native_error,core_error)<=.009,'material_director_tilts':tilt<=.009,'energy':energy_error<=.009,'stress':stress<=.045,
        'residual':residual['passed'],'exact_work':werror<=Fraction(1e-10),'virtual_work':max(virtual)<=1e-10,'force':float(abs(force).max())<=1e-8,
        'moment':float(abs(moment).max())<=1e-8,'symmetry':symmetry<=1e-10}
    emit({'type':'coupled_result','case':case,'checks':flags,'passed':all(flags.values()),'native_field_error':native_error,'whole_core_field_error':core_error,
          'original_1percent_5percent_flags':{'field_energy':max(native_error,core_error,tilt,energy_error)<=.01,'stress':stress<=.05},
          'energy_error':energy_error,'stress_error':stress,'native_coefficients':q,'native_reference_translations':expected,'solid_coefficients':a,
          'solid_reference_coefficients':exact_a,'solid_coefficient_coordinates':p.coefficient_coordinates,'solid_coefficient_components':p.coefficient_components,
          'all_quad_coordinates':recovered.coordinates,'all_quad_stress':recovered.stress,'fixed_ROI_mask':mask,'ROI_reference_stress':reference_stress,
          'energy':rational(energy),'external_work':rational(work),'exact_work_error':rational(werror),'support_dofs':fixed,'support_reactions':support[fixed],
          'force_balance':force,'moment_balance':moment,'virtual_work_errors':virtual,'director_tilt_error':tilt,'drilling_rotations_diagnostic_only':rotations[:,2],
          'multipliers':result.multipliers,'registered_residual_report':residual})
    return {'case':case['id'],'passed':all(flags.values()),'checks':flags,'field_error':max(native_error,core_error),'energy_error':energy_error,'stress_error':stress}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    manifest=json.loads(MANIFEST.read_text());validate(manifest)
    emit({'type':'transition_identity','manifest':manifest,'manifest_sha256':sha(MANIFEST),'execute':args.execute})
    if not args.execute:emit({'type':'proposal_only','FE_solves':0,'inverse_assessments':0});return 0
    import numpy as np
    import scipy
    import scipy.linalg
    import skfem
    from threadpoolctl import threadpool_info
    runtime={'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'skfem':skfem.__version__,
             'thread_environment':{k:os.environ.get(k) for k in ('MKL_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')},'actual_threadpools':threadpool_info()}
    canonical=lambda p:sorted(p,key=lambda v:v['filepath'].casefold())
    if any(runtime[k]!=manifest['runtime'][k] for k in ('python','numpy','scipy','skfem','thread_environment')) or canonical(runtime['actual_threadpools'])!=canonical(manifest['runtime']['actual_threadpools']) or os.environ.get('PYTHONPATH')!=manifest['runtime']['pythonpath']:
        raise ValueError('registered numerical runtime differs')
    emit({'type':'runtime',**runtime});deadline=time.perf_counter()+175.;counts=dict.fromkeys(('reference_attempts','reference_solved','metric_attempts','metric_results','coupled_attempts','coupled_solved'),0)
    results=[];failed=False;execution_failures=0;ref_pass=False
    try:
        # Prepare sample coordinates before importing ANYsolver/coupling. No
        # stiffness or solve is needed to construct fixed quadrature locations.
        cores=[solid(np,c['core_x'],c['core_grid'],c['id']) for c in manifest['cases']]
        samples=[]
        for p in cores:
            rec=p.recover(np.zeros(p.ndof));mask=(rec.coordinates[...,0]>=.4375)&(rec.coordinates[...,0]<=.5625);samples.append(rec.coordinates[mask])
        sample=np.concatenate(samples);emit({'type':'registered_common_samples','coordinates':sample,'rule':'ALL core quadrature samples in fixed ROI; repeated samples retained'})
        coarse=reference(np,manifest['references'][0],deadline,counts);fine=reference(np,manifest['references'][1],deadline,counts)
        values=(fine['p'].trace(coarse['p'].coefficient_coordinates)@fine['a']).reshape(-1,3)
        component=coarse['p'].coefficient_components
        actual=values[np.arange(len(component)),component]
        field_difference=float(abs(actual-coarse['a']).max()/.015)
        energy_difference=abs(fine['energy']-coarse['energy'])/fine['energy']
        coarse_stress=point_stress(np,coarse['p'],coarse['a'],sample);fine_stress=point_stress(np,fine['p'],fine['a'],sample)
        stress_difference=float(abs(coarse_stress-fine_stress).max()/5.)
        ref_pass=(coarse['passed'] and fine['passed'] and field_difference<=.001 and energy_difference<=.001 and stress_difference<=.005
                  and float(abs(fine['a']).max())>=.015 and float(abs(fine_stress).max())>=5.)
        emit({'type':'reference_convergence','passed':ref_pass,'field_difference':field_difference,'energy_difference':energy_difference,'stress_difference':stress_difference,
              'coordinates':sample,'coarse_stress':coarse_stress,'fine_stress':fine_stress,'interpretation':'two-level numerical corroboration; no rate or rigorous continuum error bound'})
        if ref_pass:
            numerics=load_numerics(manifest)
            for case,p,points in zip(manifest['cases'],cores,samples):
                emit({'type':'coupled_case_start','case':case});check_time(deadline);results.append(coupled(np,case,p,fine,points,numerics,deadline,counts))
        else:failed=True
    except Exception as exc:
        failed=True;execution_failures+=1;emit({'type':'execution_failure','error_type':type(exc).__name__,'error':str(exc),'counts':counts});traceback.print_exc(file=sys.stderr)
    passed=not failed and len(results)==3 and all(r['passed'] for r in results)
    emit({'type':'transition_terminal','counts':counts,'passed':passed,'reference_convergence_passed':ref_pass,'execution_failures':execution_failures,'results':results,'scope':'first nonuniform membrane transition-distance slice only; shear/bending full-body reference gaps remain',
          'production_status':'NO_GO_PRODUCTION_UNQUALIFIED','no_retry':True})
    return int(not passed)


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        emit({'type':'startup_failure','error_type':type(exc).__name__,'error':str(exc)});traceback.print_exc(file=sys.stderr);raise SystemExit(1)
