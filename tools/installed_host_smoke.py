"""Installed wheel smoke; execute with python -I, outside all source roots."""
import importlib.metadata
import json
from pathlib import Path
import sys
import numpy as np
import anysolver

assert 'site-packages' in Path(anysolver.__file__).parts
assert 'anysolid' not in sys.modules and 'skfem' not in sys.modules
native=anysolver.FEModel('installed-shell-only-import')
assert 'anysolid' not in sys.modules and 'skfem' not in sys.modules
from anysolver import SolidModel,ResidualScales
assert 'anysolid' not in sys.modules and 'skfem' not in sys.modules
from anysolid import SolidMesh

mesh=SolidMesh([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],[[0,1,2,3]],
               boundary_facets=[[0,2,1]],boundary_ids=[100],boundary_groups={'clamp':[100]})
model=SolidModel(residual_scales={'body':ResidualScales(1.,1.,.003)})
region=model.add_region('tet',mesh,{'elastic_modulus':1000.,'poisson_ratio':.3})
region.prescribe('clamp',0.)
region.set_load('body',region.prepared.body_load([1.,2.,3.]))
values,info=anysolver.solve_linear_many(model,['body','body'])
assert values.shape==(30,2)
np.testing.assert_array_equal(values[:,0],values[:,1])
assert info['registered_residual_report']['passed']
assert info['factorization_count']==1 and info['solve_count']==2
print(json.dumps({'status':'passed','host_module':anysolver.__file__,
    'host_version':anysolver.__version__,'isolated':bool(sys.flags.isolated),
    'residual_policy':info['residual_policy'],'normalized_equilibrium':info['normalized_equilibrium'],
    'distributions':{name:importlib.metadata.version(name) for name in
        ('ANYsolver','ANYsolver-results','ANYsolid','ANYmaterial','ANYmesher','ANYgeometry','ANYfileio','scikit-fem')}}))
