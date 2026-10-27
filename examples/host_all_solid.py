"""Opt-in ANYsolver host statics; run with both packages installed."""
from anysolid import SolidMesh
from anysolver import SolidModel

mesh=SolidMesh([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],[[0,1,2,3]],
               boundary_facets=[[0,2,1]],boundary_ids=[100],boundary_groups={'clamp':[100]})
model=SolidModel()
region=model.add_region('block',mesh,{'elastic_modulus':1000.,'poisson_ratio':.3})
region.prescribe('clamp',0.)
region.set_load('body',region.prepared.body_load([1.,2.,3.]))
result=model.solve_static(('body',))
print('coefficient count:',result.layout.primary_dofs)
print('equilibrium:',result.diagnostics['normalized_equilibrium'])
print('sampling:',region.prepared.recover(result.region_coefficients('block')[:,0]).sampling)
