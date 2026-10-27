"""Bounded W1.5 all-solid integration measurement; no speed-up claim."""
import json
from time import perf_counter
import numpy as np
from scipy.sparse.linalg import spsolve
from anysolid import SolidMesh,prepare
from anysolver.solids import SolidModel

mesh=SolidMesh([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],[[0,1,2,3]],
               boundary_facets=[[0,2,1]],boundary_ids=[100],boundary_groups={'clamp':[100]})
start=perf_counter()
backend=prepare(mesh,{'elastic_modulus':1000.,'poisson_ratio':.3})
conversion_seconds=perf_counter()-start
start=perf_counter()
K=backend.assemble_linear()
assembly_seconds=perf_counter()-start
fixed=backend.boundary_dofs('clamp')
free=np.setdiff1d(np.arange(backend.ndof),fixed)
f=backend.body_load([1.,2.,3.])
reference=np.zeros(backend.ndof)
reference[free]=spsolve(K[free][:,free],f[free])
rows=[]
for count in (1,10,100,1000):
    model=SolidModel()
    region=model.add_region('tet',prepared=backend)
    region.prescribe('clamp',0.)
    names=tuple(str(i) for i in range(count))
    scales=1+np.arange(count)/1000.
    for name,scale in zip(names,scales):
        region.set_load(name,scale*f)
    start=perf_counter()
    result=model.solve_static(names)
    elapsed=perf_counter()-start
    error=float(np.max(abs(result.coefficients-reference[:,None]*scales)))
    if error>1e-10*float(np.max(abs(reference))):
        raise RuntimeError('multiple-RHS integration mismatch')
    if result.diagnostics['factorization_count']!=1 or result.diagnostics['solve_count']!=count:
        raise RuntimeError('factorization reuse not active')
    start=perf_counter()
    recovered=backend.recover(result.coefficients[:,0])
    recovery_seconds=perf_counter()-start
    rows.append({'rhs':count,'primary_dofs':int(backend.ndof),'free_dofs':len(free),
        'conversion_seconds_shared':conversion_seconds,'assembly_seconds_shared':assembly_seconds,
        'host_total_seconds':elapsed,'factorization_seconds':result.diagnostics['factorization_time'],
        'solve_seconds':result.diagnostics['solve_time'],'selected_recovery_seconds':recovery_seconds,
        'maximum_displacement_error':error,'coefficient_output_bytes':result.coefficients.nbytes,
        'factorization_count':result.diagnostics['factorization_count'],'solve_count':result.diagnostics['solve_count'],
        'status':'passed_current_gate'})
print(json.dumps({'case':'one controlled tet4 geometry / P2 space / constant three-component body force',
    'backend_signature':backend.cache_signature(),'limitations':'tiny integration measurement; not engineering scaling, RSS or speed-up evidence',
    'results':rows}))
