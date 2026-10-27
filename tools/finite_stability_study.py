"""Prospective finite KKT/width-refinement study; no default FE execution.

Certificate helpers support separately authorized synthetic matrices. FE
imports occur only in the explicitly authorized --execute path.
"""
from __future__ import annotations
import argparse
from collections.abc import Mapping
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'docs/finite_stability_manifest.json'
UNIT_ROUNDOFF=Fraction(1,2**53)
MIN_SUBNORMAL=Fraction(1,2**1074)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def emit(record):
    def convert(value):
        if isinstance(value,Mapping): return dict(value)
        if hasattr(value,'tolist'): return value.tolist()
        if hasattr(value,'item'): return value.item()
        raise TypeError(type(value).__name__)
    print(json.dumps(record,default=convert,allow_nan=False,sort_keys=True),flush=True)


def _scalar_upper(value):
    import numpy as np
    result=float(value)
    if not math.isfinite(result): raise ValueError('nonfinite certificate scalar')
    if Fraction.from_float(result)<value: result=float(np.nextafter(result,np.inf))
    return result


def _gamma(n):
    n=int(n)
    if n<1 or n*UNIT_ROUNDOFF>=1: raise ValueError('invalid gamma operation count')
    return _scalar_upper(n*UNIT_ROUNDOFF/(1-n*UNIT_ROUNDOFF))


def _underflow(n):
    # At most 2n+1 elementary underflow errors, each bounded by one full
    # minimum subnormal, propagated by <=1/(1-nu). Deliberately conservative.
    return _scalar_upper((2*n+1)*MIN_SUBNORMAL/(1-n*UNIT_ROUNDOFF))


def _up_add(a,b):
    import numpy as np
    return np.nextafter(np.add(a,b),np.inf)


def _up_mul(a,b):
    import numpy as np
    return np.nextafter(np.multiply(a,b),np.inf)


def _up_div(a,b):
    import numpy as np
    return np.nextafter(np.divide(a,b),np.inf)


def _one_minus_lower(value):
    import numpy as np
    return np.nextafter(np.subtract(1.,value),-np.inf)


def _sum_upper(values):
    """Nonnegative row sums with conservative summation and underflow bounds."""
    import numpy as np
    n=values.shape[1]
    if n==0: return np.zeros(values.shape[0])
    gamma=_gamma(n)
    return _up_div(_up_add(np.sum(values,axis=1),_underflow(n)),_one_minus_lower(gamma))


def _arithmetic_environment():
    import numpy as np
    if np.finfo(np.float64).nmant!=52 or np.finfo(np.float64).maxexp!=1024:
        raise ValueError('certificate requires IEEE binary64')
    one=np.float64(1.); half_ulp=np.float64(2.**-53)
    if np.add(one,half_ulp)!=one or np.subtract(one,np.float64(2.**-54))!=one:
        raise ValueError('certificate requires round-to-nearest/ties-to-even')
    tiny=np.array([1],dtype=np.uint64).view(np.float64)
    if np.multiply(tiny,np.float64(1.)).view(np.uint64)[0]!=1:
        raise ValueError('certificate requires gradual underflow, not FTZ/DAZ')


def formation_relative_bound():
    gamma=4*UNIT_ROUNDOFF/(1-4*UNIT_ROUNDOFF)
    return _scalar_upper(gamma/(1-gamma))


def _normal_finite(values,label):
    import numpy as np
    values=np.asarray(values)
    if not np.isfinite(values).all() or np.any((values!=0)&(abs(values)<np.finfo(float).tiny)):
        raise ValueError(f'{label} requires normal finite nonzero entries')


def scaled_block(matrix,row_denominators,column_scales):
    """Form entries using exactly one reciprocal and two multiplications.

    The ideal block is defined by exact arithmetic on the recorded stored
    physical entries/scales. For normal finite operations relative error is
    <=gamma3, hence the registered gamma4/(1-gamma4) bound is conservative.
    """
    import numpy as np
    from scipy import sparse
    raw=sparse.csr_matrix(matrix)
    if raw.dtype.kind not in 'biuf': raise ValueError('real physical matrix required')
    if not raw.has_canonical_format: raise ValueError('canonical stored physical entries required before scaling')
    result=sparse.csr_matrix(raw,dtype=float,copy=True)
    result.sum_duplicates();result.eliminate_zeros()
    rows=np.repeat(np.arange(result.shape[0]),np.diff(result.indptr))
    row_denominators=np.asarray(row_denominators,dtype=float)
    column_scales=np.asarray(column_scales,dtype=float)
    if row_denominators.shape!=(result.shape[0],) or column_scales.shape!=(result.shape[1],):
        raise ValueError('scaled block dimensional mismatch')
    if np.any(row_denominators<=0) or np.any(column_scales<=0):
        raise ValueError('positive scaling entries required')
    _normal_finite(result.data,'physical matrix');_normal_finite(row_denominators,'row scales');_normal_finite(column_scales,'column scales')
    with np.errstate(over='ignore',under='ignore',invalid='ignore',divide='ignore'):
        inverse=1./row_denominators
        _normal_finite(inverse,'row reciprocal')
        if np.any(inverse==0): raise ValueError('row reciprocal underflow')
        product=result.data*column_scales[result.indices]
        _normal_finite(product,'first scaling product')
        if np.any((result.data!=0)&(product==0)): raise ValueError('first scaling product underflow')
        data=product*inverse[rows]
        _normal_finite(data,'second scaling product')
        if np.any((product!=0)&(data==0)): raise ValueError('second scaling product underflow')
    result.data=data
    return result


def certify_inverse_action(H,primal_rows,*,block_columns=64,physical_output_factor=4.,
                           inverse_action=None,formation_error=None,deadline=None,progress=None):
    """Verified row-block upper bounds using RIGHT defect I-H_star R.

    H_star is the ideal scaling of the stored physical blocks, with entrywise
    formation uncertainty <=formation_error*abs(H). R is only a computed
    inverse action. Every dot, subtraction and row accumulation is enclosed
    outward. No LU error estimate or inverse-norm estimator is assumed.
    """
    import numpy as np
    from scipy import sparse
    from scipy.sparse.linalg import splu
    _arithmetic_environment()
    raw=sparse.csr_matrix(H)
    if raw.dtype.kind not in 'biuf': raise ValueError('real certificate matrix required')
    H=sparse.csr_matrix(raw,dtype=float,copy=True);H.sum_duplicates();H.eliminate_zeros()
    n=H.shape[0]
    if (H.shape!=(n,n) or n==0 or n>2100 or not isinstance(primal_rows,(int,np.integer))
            or isinstance(primal_rows,(bool,np.bool_)) or not 0<=primal_rows<=n):
        raise ValueError('certificate requires square dimension1..2100 and valid row split')
    if not isinstance(block_columns,int) or isinstance(block_columns,bool) or not 1<=block_columns<=64:
        raise ValueError('inverse column block must be1..64')
    if not math.isfinite(physical_output_factor) or physical_output_factor<=0 or not np.isfinite(H.data).all():
        raise ValueError('nonfinite matrix/output scale')
    formation=formation_relative_bound() if formation_error is None else float(formation_error)
    if not math.isfinite(formation) or formation<0: raise ValueError('invalid formation bound')
    try:
        action=splu(H.tocsc()).solve if inverse_action is None else inverse_action
    except (RuntimeError,ValueError) as exc:
        return {'verified':False,'reason':'factorization_failed','detail':str(exc)}
    row_R=np.zeros(n);row_arithmetic=np.zeros(n);row_formation=np.zeros(n)
    gamma=_gamma(n);under=_underflow(n);absolute_H=abs(H)
    try:
        with np.errstate(over='ignore',under='ignore',invalid='ignore',divide='ignore'):
            for start in range(0,n,block_columns):
                if deadline is not None and time.perf_counter()>=deadline: raise TimeoutError('registered study deadline')
                stop=min(start+block_columns,n);width=stop-start
                I=np.zeros((n,width));I[np.arange(start,stop),np.arange(width)]=1.
                R=np.asarray(action(I),dtype=float)
                if R.shape!=I.shape or not np.isfinite(R).all():
                    return {'verified':False,'reason':'nonfinite_or_wrong_inverse_action'}
                product=np.asarray(H@R)
                abs_product=np.asarray(absolute_H@abs(R))
                # Correct the nonnegative computed dot to an exact upper bound
                # before using it in either arithmetic or formation estimates.
                abs_product_up=_up_div(_up_add(abs_product,under),_one_minus_lower(gamma))
                residual=I-product
                dot_error=_up_add(_up_mul(gamma,abs_product_up),under)
                subtraction_error=_up_add(_up_mul(float(UNIT_ROUNDOFF),_up_add(abs(I),abs(product))),float(MIN_SUBNORMAL))
                arithmetic=_up_add(abs(residual),_up_add(dot_error,subtraction_error))
                formation_block=_up_mul(formation,abs_product_up)
                row_R=_up_add(row_R,_sum_upper(abs(R)))
                row_arithmetic=_up_add(row_arithmetic,_sum_upper(arithmetic))
                row_formation=_up_add(row_formation,_sum_upper(formation_block))
                if not all(np.isfinite(v).all() for v in (product,abs_product_up,row_R,row_arithmetic,row_formation)):
                    return {'verified':False,'reason':'nonfinite_certificate_arithmetic'}
                if progress is not None:
                    progress({'columns_checked':stop,'dimension':n,'partial_only':True})
    except TimeoutError:
        raise
    eta_rows=_up_add(row_arithmetic,row_formation)
    if not np.isfinite(eta_rows).all():
        return {'verified':False,'reason':'nonfinite_total_defect_bound'}
    eta=float(eta_rows.max())
    base={'verified':False,'dimension':n,'block_columns':block_columns,'eta_upper':eta,
          'eta_arithmetic_upper':float(row_arithmetic.max()),'eta_formation_upper':float(row_formation.max()),
          'formation_relative_bound':formation,'physical_output_factor':float(physical_output_factor),
          'R_primal_row_norm_upper':float(row_R[:primal_rows].max(initial=0.)),
          'R_dual_row_norm_upper':float(row_R[primal_rows:].max(initial=0.)),
          'streamed_columns':n,'full_inverse_stored':False}
    if eta>=1:
        return {**base,'reason':'right_defect_not_below_one'}
    denominator=_one_minus_lower(eta)
    primal=float(_up_div(base['R_primal_row_norm_upper'],denominator))
    dual=float(_up_div(base['R_dual_row_norm_upper'],denominator))
    output=float(_up_mul(physical_output_factor,primal))
    if not np.isfinite([primal,dual,output]).all():
        return {**base,'reason':'nonfinite_inverse_upper_bound'}
    return {**base,'verified':True,'reason':'right_defect_neumann_bound',
            'primal_inverse_upper':primal,'physical_output_amplification_upper':output,
            'modal_traction_couple_amplification_upper':dual}


def build_scaled_kkt(Kr,B,S,T,G,Lambda):
    from scipy import sparse
    upper_left=scaled_block(Kr,S,T)
    upper_right=scaled_block(B.T,S,Lambda)
    lower_left=scaled_block(B,G,T)
    return sparse.bmat([[upper_left,upper_right],[lower_left,None]],format='csr')


def finite_positive_energy_check(Kr,B,*,maximum_reduced=2000,deadline=None):
    """Numerical QR/Cholesky assessment, NOT exact coercivity certification."""
    import numpy as np
    from scipy import linalg,sparse
    Kr=sparse.csr_matrix(Kr,dtype=float);B=sparse.csr_matrix(B,dtype=float)
    r,m=Kr.shape[0],B.shape[0]
    if r>maximum_reduced: return {'assessed':False,'reason':'registered_dense_dimension_bound'}
    if m>=r: return {'assessed':True,'positive_energy':False,'reason':'no_registered_positive_kernel_dimension'}
    if deadline is not None and time.perf_counter()>=deadline: raise TimeoutError('registered study deadline')
    norms=np.asarray(abs(B).sum(axis=1)).ravel()
    if np.any(norms==0): return {'assessed':True,'positive_energy':False,'reason':'zero_constraint_row'}
    normalized=sparse.diags(1./norms)@B
    Q,R=linalg.qr(normalized.T.toarray(),mode='full',pivoting=False,check_finite=True)
    Z=Q[:,m:]
    if np.any(np.diag(R[:m])==0):
        return {'assessed':True,'positive_energy':False,'reason':'zero_QR_pivot_no_rank_truncation'}
    raw=np.asarray(normalized@Z)
    magnitude=np.asarray(abs(normalized)@abs(Z))
    magnitude_up=_up_div(_up_add(magnitude,_underflow(r)),_one_minus_lower(_gamma(r)))
    null_upper=_up_add(abs(raw),_up_add(_up_mul(_gamma(r),magnitude_up),_underflow(r)))
    null_defect=float(_sum_upper(null_upper).max(initial=0.))
    if deadline is not None and time.perf_counter()>=deadline: raise TimeoutError('registered study deadline')
    KZ=Kr@Z;projected=np.asarray(Z.T@KZ)
    scale=np.linalg.norm(projected,np.inf)
    asym=float(np.linalg.norm(projected-projected.T,np.inf)/scale) if scale else 0.
    positive=False;failure=None;diagonal=None
    try:
        L=linalg.cholesky(projected,lower=True,check_finite=True)
        positive=True;diagonal=float(np.diag(L).min())
    except (linalg.LinAlgError,ValueError) as exc: failure=str(exc)
    return {'assessed':True,'positive_energy':bool(positive and null_defect<=1e-10 and asym<=1e-10),
            'kind':'finite_positive_energy_check_not_exact_coercivity_certificate',
            'nullspace_defect_upper':null_defect,'projected_relative_asymmetry':asym,
            'raw_constraint_rows':m,'kernel_basis_columns':Z.shape[1],'rank_truncation':False,
            'regularization':False,'Cholesky_min_diagonal_diagnostic':diagonal,'failure':failure,
            'named_dense_array_bytes':{'Q':Q.nbytes,'R':R.nbytes,'KZ':KZ.nbytes,'projected':projected.nbytes,
                                       'Cholesky':projected.nbytes if positive else 0},
            'storage_scope':'named arrays only, not RSS or all library workspace'}


def _load_fixture(manifest):
    path=Path(manifest['fixture_path'])
    if sha(path)!=manifest['fixture_sha256']: raise ValueError('frozen geometry/load helper changed')
    spec=importlib.util.spec_from_file_location('_finite_width_fixture',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def full_solid_reference(np,registration,manifest,deadline,coarse_state=None):
    """Independent full-body P2 corroboration: no shell/trace/host coupling.

    Only physical affine side tractions and analytical essential end values
    enter the direct SciPy solve. The analytical reference is never fitted.
    """
    if 'anysolver' in sys.modules or 'anysolid.coupling' in sys.modules:
        raise ValueError('independent references must precede all native/coupling imports')
    from skfem import MeshTet
    from scipy.sparse.linalg import splu
    from anysolid import SolidMesh,prepare
    n=registration['subdivisions'];t=registration['thickness'];a=.001;E=1000.
    raw=MeshTet.init_tensor(np.linspace(-1.,2.,n+1),np.linspace(0.,1.,n+1),np.linspace(-t/2,t/2,n+1)).oriented()
    mesh0=SolidMesh(raw.p.T,raw.t.T)
    x=mesh0.coordinates[mesh0.boundary_facets]
    groups={'left':mesh0.boundary_ids[np.all(x[:,:,0]==-1.,axis=1)],
            'y0':mesh0.boundary_ids[np.all(x[:,:,1]==0.,axis=1)],
            'y1':mesh0.boundary_ids[np.all(x[:,:,1]==1.,axis=1)],
            'all':mesh0.boundary_ids}
    prepared=prepare(SolidMesh(mesh0.coordinates,mesh0.cells,boundary_groups=groups,
        provenance={'independent_full_solid_reference':registration['id']}),{'elastic_modulus':E,'poisson_ratio':0.},order=2)
    if prepared.ndof!=registration['planned_dofs'] or prepared.ndof>manifest['bounds']['maximum_reference_primary']:
        raise ValueError('independent reference DOF bound/count mismatch')
    locations=prepared.coefficient_coordinates;components=prepared.coefficient_components
    values=np.column_stack((np.zeros(prepared.ndof),a*(locations[:,1]-.5)*locations[:,2],-a*(locations[:,1]-.5)**2/2))
    exact=values[np.arange(prepared.ndof),components]
    f=np.zeros(prepared.ndof)
    for side,sign in (('y0',-1.),('y1',1.)):
        gradient=np.zeros((3,3));gradient[1,2]=sign*E*a
        f+=prepared.traction(side,[0.,0.,0.],gradient=gradient)
    fixed=prepared.boundary_dofs('left');boundary=prepared.boundary_dofs('all')
    free=np.setdiff1d(np.arange(prepared.ndof),fixed);K=prepared.assemble_linear()
    rhs=f[free]-K[free][:,fixed]@exact[fixed]
    emit({'type':'full_solid_reference_solve_start','reference':registration,'ndof':int(prepared.ndof),
          'fixed_dofs':fixed,'applied_affine_surface_load':f,'exact_fixed_values':exact[fixed],
          'matrix_shape':K.shape,'matrix_nnz':K.nnz,'route':'ANYsolid public backend plus direct SciPy LU; no shell/coupling',
          'prepared_signature':prepared.cache_signature()})
    if time.perf_counter()>=deadline: raise TimeoutError('deadline before independent reference solve')
    coefficients=exact.copy()
    coefficients[free]=splu(K[free][:,free].tocsc()).solve(rhs)
    reaction=K@coefficients-f
    support=np.zeros(prepared.ndof);support[fixed]=reaction[fixed]
    recovered=prepared.recover(coefficients);expected=np.zeros_like(recovered.stress)
    expected[...,1,1]=E*a*recovered.coordinates[...,2]
    energy=float(coefficients@K@coefficients);reference_energy=registration['twice_energy']
    field_error=float(abs(coefficients-exact).max()/.000125)
    boundary_error=float(abs(coefficients[boundary]-exact[boundary]).max()/.000125)
    stress_error=float(abs(recovered.stress-expected).max()/(E*a*t/2))
    energy_error=abs(energy-reference_energy)/reference_energy
    work=float(coefficients@f+coefficients[fixed]@support[fixed])
    work_error=abs(energy-work)/reference_energy
    residual=float(abs(reaction[free]).max(initial=0.)/registration['force_reference'])
    physical=np.zeros((prepared.ndof,3));physical[np.arange(prepared.ndof),components]=f+support
    force_error=float(np.linalg.norm(physical.sum(axis=0),np.inf)/registration['force_reference'])
    moment_error=float(np.linalg.norm(np.cross(locations,physical).sum(axis=0),np.inf)/registration['force_reference'])
    refinement=None
    if coarse_state is not None:
        # Actual common-point difference, not difference of independently
        # attained extrema. P2 trace is upstream; no recovery smoothing/fitting.
        all_values=(prepared.trace(coarse_state['locations'])@coefficients).reshape(-1,3)
        sampled=all_values[np.arange(len(coarse_state['coefficients'])),coarse_state['components']]
        difference=sampled-coarse_state['coefficients']
        refinement={'coarse_fine_common_coefficient_displacement_difference_scaled':float(abs(difference).max()/.000125),
                    'coarse_fine_energy_difference_relative':abs(energy-coarse_state['energy'])/reference_energy,
                    'common_coordinates':coarse_state['locations'],'common_components':coarse_state['components'],
                    'common_point_coefficient_differences':difference,
                    'stress_comparison':'Both levels independently compare every quadrature stress component to exact analytic field; no difference-of-maxima stress claim'}
    checks={'all_primary_coefficients':field_error<=1e-4,'all_boundary_coefficients':boundary_error<=1e-4,
            'energy':energy_error<=1e-4,'all_quadrature_stress':stress_error<=5e-4,'residual':residual<=1e-9,
            'work':work_error<=1e-10,'force':force_error<=1e-8,'moment':moment_error<=1e-8}
    if refinement is not None:
        checks['refinement_common_field']=refinement['coarse_fine_common_coefficient_displacement_difference_scaled']<=1e-4
        checks['refinement_energy']=refinement['coarse_fine_energy_difference_relative']<=1e-4
    record={'type':'full_solid_reference_result','reference':registration,'passed':bool(all(checks.values())),
            'checks':checks,'all_primary_error':field_error,'all_boundary_error':boundary_error,
            'energy_error':energy_error,'stress_error':stress_error,'residual':residual,'work_error':work_error,
            'force_error':force_error,'moment_error':moment_error,'energy_twice':energy,'external_plus_support_work':work,
            'coefficient_coordinates':locations,'components':components,'actual_coefficients':coefficients,'exact_coefficients':exact,
            'all_stress_coordinates':recovered.coordinates,'actual_stress':recovered.stress,'exact_stress':expected,
            'boundary_dofs':boundary,'refinement_difference':refinement,
            'claim':'Independent numerical corroboration only of the exact width-bending continuum reference'}
    state={'locations':locations,'components':components,'coefficients':coefficients,'energy':energy}
    return record,state


def _physical_output_factor(np,P,D,T,rotation_indices,manifest):
    # Exact rational check of the actual sparse map DP T / individual refs.
    # No floating norm estimator is promoted to an output upper bound.
    rotations=set(map(int,rotation_indices));factor=Fraction(0)
    for row in range(P.shape[0]):
        start,stop=P.indptr[row:row+2]
        if stop-start>1: raise ValueError('physical output requires disjoint selection P')
        check=manifest['physical_references']['rotation_check']*manifest['physical_references']['length'] if row in rotations else manifest['physical_references']['displacement_check']
        value=sum(abs(Fraction.from_float(float(D[row]))*Fraction.from_float(float(P.data[k]))*Fraction.from_float(float(T[P.indices[k]]))/Fraction.from_float(float(check))) for k in range(start,stop))
        factor=max(factor,value)
    if factor>Fraction(4): raise ValueError('actual normalized physical output exceeds registered factor4')
    return {'registered_conservative_factor':4.,'exact_actual_max_row_sum':str(factor)}


def run_registered_case(np,fixture,case,manifest,deadline):
    from scipy import sparse
    from anysolver.assembly import assemble_system,build_constraint_transformation
    from anysolver.solids import SolidModel,ResidualScales
    configuration=case['derived_configuration'];registration=case['physical_case']
    native,regions,operators,clamp,tip=fixture.build_specimen(np,registration,configuration)
    load,F_native,solid_loads,_=fixture.make_loads(np,native,regions,tip,registration,configuration)
    prepared=regions['solid1'];native.apply_boundary_conditions()
    Ksh,_,_=assemble_system(native,load)
    _,_,Tsh,u0,_,_=build_constraint_transformation(Ksh,F_native,native)
    K=sparse.block_diag((Ksh,prepared.assemble_linear()),format='csr')
    P=sparse.block_diag((Tsh,sparse.eye(prepared.ndof)),format='csr');P.sum_duplicates();P.eliminate_zeros()
    columns=P.tocsc()
    if np.any(np.diff(columns.indptr)!=1) or not np.all(columns.data==1.) or np.any(np.diff(P.indptr)>1):
        raise ValueError('registered family permits selection-only supports, no MPC')
    free=columns.indices
    C=sparse.vstack([sparse.hstack((op.C_shell,-op.C_solid)) for _,op in operators],format='csr')
    C.sum_duplicates();C.eliminate_zeros()
    Kr=K[free][:,free].tocsr();B=C[:,free].tocsr()
    Kr.sum_duplicates();Kr.eliminate_zeros();B.sum_duplicates();B.eliminate_zeros()
    r,m=Kr.shape[0],B.shape[0]
    bounds=manifest['bounds']
    if K.shape[0]>bounds['maximum_primary'] or r+m>bounds['maximum_kkt'] or m>bounds['maximum_multiplier']:
        raise ValueError('actual case dimensions exceed prospective bounds')
    symmetry=float(sparse.linalg.norm(K-K.T,np.inf)/sparse.linalg.norm(K,np.inf))
    if symmetry>1e-10: raise ValueError('physical stiffness symmetry gate')
    rotations=np.array([d for node in native.mesh.nodes.values() for d in native.mesh.dof_manager.get_node_dofs(node.id)[3:]],dtype=int)
    D=np.ones(K.shape[0]);D[rotations]=manifest['physical_references']['length']
    if not np.all(D==1.): raise ValueError('registered L1 selection family changed')
    U=manifest['physical_references']['U'];force=case['force_reference'];thickness=case['thickness']
    s=np.ones(r);T=np.full(r,U);S=np.full(r,force)
    G=np.array([float(Fraction.from_float(U)*sum(abs(Fraction.from_float(float(v))) for v in C.data[C.indptr[i]:C.indptr[i+1]])) for i in range(m)])
    if np.any(G<=0): raise ValueError('zero constraint normalization')
    modal=np.array([float(Fraction.from_float(force)/(Fraction(1)*Fraction.from_float(thickness)))]*3+
                   [float(6*Fraction.from_float(force)/Fraction.from_float(thickness)**2)]*2)
    Lambda=np.tile(modal,m//5)
    H=build_scaled_kkt(Kr,B,S,T,G,Lambda)
    output=_physical_output_factor(np,P,D,T,rotations,manifest)
    def csr_payload(matrix):
        matrix=sparse.csr_matrix(matrix)
        return {'shape':matrix.shape,'indptr':matrix.indptr,'indices':matrix.indices,'data':matrix.data}
    emit({'type':'metric_start','case':case['id'],'dimensions':{'primary':K.shape[0],'reduced':r,'multipliers':m,'KKT':r+m},
          'scales':{'D':D,'s':s,'T':T,'S':S,'G':G,'Lambda':Lambda},'physical_output':output,
          'canonical_stored_Kr':csr_payload(Kr),'canonical_stored_B':csr_payload(B),
          'formed_H':csr_payload(H),'selection_free_rows':free,
          'certificate_scope':'ideal exact scaling of canonical stored physical blocks and stored normalization values; not assembly/continuum/model error',
          'physical_symmetry':symmetry,'H_shape':H.shape,'H_nnz':H.nnz,
          'csr_H_array_bytes':H.data.nbytes+H.indices.nbytes+H.indptr.nbytes})
    started=time.perf_counter()
    cert=certify_inverse_action(H,r,physical_output_factor=4.,block_columns=64,deadline=deadline,
        progress=lambda record:emit({'type':'inverse_progress','case':case['id'],**record}))
    inverse_wall=time.perf_counter()-started
    emit({'type':'inverse_certificate','case':case['id'],'certificate':cert,'phase_wall_seconds':inverse_wall})
    emit({'type':'positive_energy_start','case':case['id'],'reduced_dimension':r})
    started=time.perf_counter();coercivity=finite_positive_energy_check(Kr,B,maximum_reduced=2000,deadline=deadline)
    coercivity_wall=time.perf_counter()-started
    emit({'type':'positive_energy_result','case':case['id'],**coercivity,'phase_wall_seconds':coercivity_wall})
    flags={'verified_inverse':cert['verified'],
        'physical_output_allocation':cert.get('physical_output_amplification_upper',math.inf)<=1e6,
        'modal_traction_couple_allocation':cert.get('modal_traction_couple_amplification_upper',math.inf)<=5e6,
        'finite_positive_energy_check':coercivity.get('positive_energy',False)}
    physical=None
    if case['physical_solve']:
        if time.perf_counter()>=deadline: raise TimeoutError('registered study deadline before physical solve')
        refs=registration['references']
        model=SolidModel(native,research_coupling=True,residual_scales={case['id']:ResidualScales(1.,force,U,(U,U))})
        model.add_region('solid1',prepared=prepared).set_load(case['id'],solid_loads['solid1'])
        for name,op in operators: model.add_interface(name,op)
        emit({'type':'physical_solve_start','case':case['id'],'registration':registration,'coarse_diagnostic':case['nshell']!=16})
        result=model.solve_static((case['id'],),native_load_cases={case['id']:load})
        q=result.native_displacements[:,0];a=result.region_coefficients('solid1')[:,0]
        exact=np.zeros_like(q);trans=[];rot=[]
        for node in native.mesh.nodes.values():
            dofs=native.mesh.dof_manager.get_node_dofs(node.id)
            u,theta=fixture.reference_fields(np,node.coords(),registration);exact[dofs]=np.r_[u,theta]
            trans.extend(dofs[:3]);rot.extend(dofs[3:])
        native_displacement=float(abs(q[trans]-exact[trans]).max()/manifest['physical_references']['displacement_check'])
        exact_solid_values=fixture.reference_fields(np,prepared.coefficient_coordinates,registration)[0]
        exact_solid=exact_solid_values[np.arange(prepared.ndof),prepared.coefficient_components]
        solid_displacement=float(abs(a-exact_solid).max()/manifest['physical_references']['displacement_check'])
        displacement=max(native_displacement,solid_displacement)
        rotation=float(abs(q[rot]-exact[rot]).max()/manifest['physical_references']['rotation_check'])
        energy=float(q@Ksh@q+a@prepared.assemble_linear()@a)
        energy_error=abs(energy-refs['twice_energy'])/refs['twice_energy']
        recovery=prepared.recover(a);expected=np.zeros_like(recovery.stress)
        expected[...,1,1]=1000.*.001*recovery.coordinates[...,2]
        mask=(recovery.coordinates[...,0]>=.25)&(recovery.coordinates[...,0]<=.75)
        stress=float(abs(recovery.stress[mask]-expected[mask]).max()/refs['stress_scale'])
        fixed=np.array([d for nid in clamp for d in native.mesh.dof_manager.get_node_dofs(nid)],dtype=int)
        support=np.zeros_like(q);support[fixed]=result.reactions[fixed,0]
        ef,em=fixture.physical_resultant(np,native,F_native,solid_loads,regions)
        sf,sm=fixture.physical_resultant(np,native,support,{},regions)
        force_error=float(np.linalg.norm(ef+sf,np.inf)/force);moment_error=float(np.linalg.norm(em+sm,np.inf)/force)
        external=float(q@F_native+a@solid_loads['solid1']+q[fixed]@support[fixed])
        work_error=abs(energy-external)/refs['twice_energy']
        residual=result.diagnostics['registered_residual_report']
        physical_flags={'displacement':displacement<=.009,'rotation':rotation<=.009,'energy':energy_error<=.009,
                        'stress':stress<=.045,'residuals':residual['passed'],'work':work_error<=1e-10,
                        'force':force_error<=1e-8,'moment':moment_error<=1e-8}
        physical={'displacement_error':displacement,'rotation_error':rotation,'energy_error':energy_error,'stress_error':stress,
                  'native_displacement_error':native_displacement,'whole_core_coefficient_displacement_error':solid_displacement,
                  'force_error':force_error,'moment_error':moment_error,'work_error':work_error,
                  'flags_at_finest_limits':physical_flags,'coarse_diagnostic_only':case['nshell']!=16,
                  'finest_measured_targets_met':bool(all(physical_flags.values())) if case['nshell']==16 else None,
                  'native_coefficients':q,'solid_coefficients':a,'stress_coordinates':recovery.coordinates,
                  'solid_coefficient_coordinates':prepared.coefficient_coordinates,'solid_coefficient_components':prepared.coefficient_components,
                  'exact_solid_coefficients':exact_solid,
                  'actual_stress':recovery.stress,'exact_continuum_stress':expected,'fixed_roi_mask':mask,
                  'registered_residual_report':residual,
                  'interpretation':'finite measurements, not a combined certified energy/stress error budget'}
        emit({'type':'physical_result','case':case['id'],**physical})
    return {'type':'case_result','case':case['id'],'metric_flags':flags,'metric_passed':bool(all(flags.values())),
            'certificate':cert,'finite_positive_energy':coercivity,
            'physical_summary':None if physical is None else {k:v for k,v in physical.items() if k not in ('native_coefficients','solid_coefficients','stress_coordinates','actual_stress','exact_continuum_stress','fixed_roi_mask','registered_residual_report','solid_coefficient_coordinates','solid_coefficient_components','exact_solid_coefficients')},
            'production_status':'NO_GO_PRODUCTION_UNQUALIFIED'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    if sha(__file__)!=manifest['harness_sha256']: raise ValueError('finite study source identity changed')
    for path,expected in manifest['source_hashes'].items():
        if sha(path)!=expected: raise ValueError(f'frozen source changed: {path}')
    if (len(manifest['cases'])!=18 or sum(c['physical_solve'] for c in manifest['cases'])!=12
            or len(manifest['full_solid_references'])!=6):
        raise ValueError('registered18metric/12physical inventory mismatch')
    refs=manifest['physical_references']
    if (refs['length'],refs['U'],refs['displacement_check'],refs['rotation_check'],refs['interface_U'])!=(1.,.0005,.000125,.0005,[.0005,.0005]):
        raise ValueError('registered component/output reference family changed')
    emit({'type':'study_identity','manifest':manifest,'manifest_sha256':sha(MANIFEST),'harness_sha256':sha(__file__),'execute':args.execute})
    if not args.execute:
        emit({'type':'proposal_only','candidate_metrics':0,'physical_solves':0});return 0
    import numpy as np
    import scipy
    import scipy.linalg
    import scipy.sparse.linalg
    import skfem
    from threadpoolctl import threadpool_info
    if skfem.__version__!='12.0.2': raise ValueError('registered upstream version changed')
    pools=threadpool_info()
    controlled=[p for p in pools if p.get('user_api') in ('blas','openmp')]
    if not controlled or any(p.get('num_threads')!=1 for p in controlled):
        raise ValueError('candidate requires verifiable actual single-thread BLAS/OpenMP pools')
    emit({'type':'runtime','python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'skfem':skfem.__version__,
          'actual_threadpools':pools,'thread_environment':{key:os.environ.get(key) for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')}})
    deadline=time.perf_counter()+175.
    reference_summaries=[];coarse_states={}
    for registration in manifest['full_solid_references']:
        emit({'type':'full_solid_reference_start','reference':registration})
        started=time.perf_counter()
        try:
            if time.perf_counter()>=deadline: raise TimeoutError('registered deadline before independent reference')
            key=str(registration['thickness'])
            record,state=full_solid_reference(np,registration,manifest,deadline,coarse_states.get(key))
            record['phase_wall_seconds']=time.perf_counter()-started;emit(record)
            if registration['subdivisions']==2: coarse_states[key]=state
            else: coarse_states.pop(key,None)
            reference_summaries.append({key:record[key] for key in ('reference','passed','checks','all_primary_error',
                'all_boundary_error','energy_error','stress_error','residual','work_error')})
        except Exception as exc:
            emit({'type':'full_solid_reference_failure','reference':registration,'error_type':type(exc).__name__,'error':str(exc)})
            traceback.print_exc(file=sys.stderr);sys.stderr.flush()
            emit({'type':'study_summary','references_completed':len(reference_summaries),'metrics_completed':0,
                  'physical_results':0,'execution_failures':1,'bounded_registered_cases_met':False,
                  'reference_results':reference_summaries,'production_status':'NO_GO_PRODUCTION_UNQUALIFIED'})
            return 1
    if not all(record['passed'] for record in reference_summaries):
        emit({'type':'study_summary','references_completed':len(reference_summaries),'metrics_completed':0,
              'physical_results':0,'execution_failures':0,'bounded_registered_cases_met':False,
              'reason':'independent_reference_accuracy_prerequisite_not_met','reference_results':reference_summaries,
              'production_status':'NO_GO_PRODUCTION_UNQUALIFIED'})
        return 1
    fixture=_load_fixture(manifest)
    records=[];failures=0
    for case in manifest['cases']:
        emit({'type':'case_start','case':case['id'],'registration':case})
        case_started=time.perf_counter()
        try:
            if time.perf_counter()>=deadline: raise TimeoutError('registered study deadline')
            record=run_registered_case(np,fixture,case,manifest,deadline)
            record['case_wall_seconds']=time.perf_counter()-case_started
            emit(record);records.append(record)
        except Exception as exc:
            failures+=1;emit({'type':'case_failure','case':case['id'],'error_type':type(exc).__name__,'error':str(exc),
                'diagnostics':getattr(exc,'diagnostics',None)})
            traceback.print_exc(file=sys.stderr);sys.stderr.flush();break
    finest=[r for r in records if r['physical_summary'] is not None and not r['physical_summary']['coarse_diagnostic_only']]
    accepted=(failures==0 and len(records)==18 and len(finest)==3 and all(r['passed'] for r in reference_summaries)
              and all(r['metric_passed'] for r in records)
              and all(r['physical_summary']['finest_measured_targets_met'] for r in finest)
              and all(all(r['physical_summary']['flags_at_finest_limits'][key] for key in ('residuals','work','force','moment'))
                      for r in records if r['physical_summary'] is not None))
    emit({'type':'study_summary','metrics_completed':len(records),'physical_results':sum(r['physical_summary'] is not None for r in records),
          'references_completed':len(reference_summaries),'reference_results':reference_summaries,
          'execution_failures':failures,'bounded_registered_cases_met':bool(accepted),
          'records':records,'claim':'bounded discrete case evidence only; no universal stability or recovered-stress certificate',
          'production_status':'NO_GO_PRODUCTION_UNQUALIFIED'})
    return int(not accepted)


if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc:
        emit({'type':'startup_failure','error_type':type(exc).__name__,'error':str(exc)});traceback.print_exc(file=sys.stderr);raise SystemExit(1)
