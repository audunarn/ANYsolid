"""Installed-only 1:8 coverage and robust shared-edge guard smoke; no solve."""
from pathlib import Path
import json
import sys
import numpy as np
from skfem import MeshTet
import anysolid
import anysolver
from anysolid import SolidMesh,prepare
from anysolid.coupling import build_weak_connector
from anysolver.elements import create_shell_element
from anysolver.solid_trace import ShellEdgeTrace

assert sys.flags.isolated
assert all('site-packages' in Path(module.__file__).parts for module in (anysolid,anysolver))
native=anysolver.FEModel('installed-1-to-8-geometry')
native.add_material('m',1000.,0.)
for i,xyz in enumerate(((-1.,0.,0.),(0.,0.,0.),(0.,1.,0.),(-1.,1.,0.)),1):
    native.add_node(i,*xyz)
native.add_element(1,create_shell_element(1,[1,2,3,4],'m',thickness=.2,reference_normal=(0.,0.,1.)))
raw=MeshTet.init_tensor([0.,1.],np.linspace(0.,1.,9),[-.1,0.,.1]).oriented()
snapshot=SolidMesh(raw.p.T,raw.t.T)
ids=snapshot.boundary_ids[np.all(snapshot.coordinates[snapshot.boundary_facets,0]==0.,axis=1)]
prepared=prepare(SolidMesh(snapshot.coordinates,snapshot.cells,boundary_groups={'left':ids}),
                 {'elastic_modulus':1000.,'poisson_ratio':0.})
operator=build_weak_connector(ShellEdgeTrace(native,[(1,1)]),prepared,'left',multiplier_breakpoints=[0.,1.])
assert operator.C_shell.shape==(10,24) and operator.C_solid.shape==(10,765)
assert operator.metadata['status']=='NO_GO_PRODUCTION_UNQUALIFIED'
print(json.dumps({'status':'passed_geometry_smoke','shell_origin':anysolver.__file__,
                  'solid_origin':anysolid.__file__,'rows':10,'production':'NO_GO'}))
