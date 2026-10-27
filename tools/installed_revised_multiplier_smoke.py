"""Installed policy plus actual coupling-construction smoke; no solve/certificate."""
import hashlib
import json
from pathlib import Path
import sys
import anysolid
from anysolid.multiplier import coarsened_p1_partition
import anysolid.multiplier

assert sys.flags.isolated and 'site-packages' in Path(anysolid.__file__).parts
assert 'numpy' not in sys.modules and 'skfem' not in sys.modules
assert hashlib.sha256(Path(anysolid.multiplier.__file__).read_bytes()).hexdigest()=='03706a167e6d7ddf77c2afd81e55142273a005abf42e376448af6951a4d515e8'
import numpy as np
from skfem import MeshTet
from anysolid import SolidMesh,prepare
from anysolid.coupling import build_weak_connector
from anysolver import FEModel
from anysolver.elements import create_shell_element
from anysolver.solid_trace import ShellEdgeTrace

corners=np.linspace(0.,1.,5)
knots=coarsened_p1_partition(corners,corners)
np.testing.assert_array_equal(knots,[0.,.5,1.])
assert not knots.flags.writeable
native=FEModel('installed-revised-policy')
native.add_material('m',1000.,0.)
for j,y in enumerate(corners):
    native.add_node(2*j+1,-1.,float(y),0.);native.add_node(2*j+2,0.,float(y),0.)
for j in range(4):
    native.add_element(j+1,create_shell_element(j+1,[2*j+1,2*j+2,2*j+4,2*j+3],
        'm',thickness=.2,reference_normal=(0.,0.,1.)))
raw=MeshTet.init_tensor([0.,1.],corners,[-.1,0.,.1]).oriented()
snapshot=SolidMesh(raw.p.T,raw.t.T)
ids=snapshot.boundary_ids[np.all(snapshot.coordinates[snapshot.boundary_facets,0]==0.,axis=1)]
prepared=prepare(SolidMesh(snapshot.coordinates,snapshot.cells,boundary_groups={'left':ids}),
                 {'elastic_modulus':1000.,'poisson_ratio':0.})
operator=build_weak_connector(ShellEdgeTrace(native,[(i,1) for i in range(1,5)]),prepared,'left',multiplier_breakpoints=knots)
assert operator.C_shell.shape==(15,60) and operator.C_solid.shape==(15,405)
assert operator.metadata['status']=='NO_GO_PRODUCTION_UNQUALIFIED'
print(json.dumps({'status':'passed_installed_construction_smoke','origin':anysolid.__file__,
                  'knots':knots.tolist(),'rows':15,'production':'still_unqualified'}))
