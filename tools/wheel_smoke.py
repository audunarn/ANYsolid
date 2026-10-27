"""Run with python -I after installing the candidate wheel, outside src."""
import json
from pathlib import Path
import sys
import anysolid

assert 'site-packages' in Path(anysolid.__file__).parts
assert 'skfem' not in sys.modules
from anysolid import SolidMesh,prepare
assert 'skfem' not in sys.modules
from anysolid.coupling import CouplingOperator
assert '_operator_signatures' in CouplingOperator.__annotations__
prepared=prepare(SolidMesh([[0,0,0],[1,0,0],[0,1,0],[0,0,1]],[[0,1,2,3]]),
                 {'elastic_modulus':1000.,'poisson_ratio':.3})
assert prepared.ndof==30
assert prepared.assemble_linear().shape==(30,30)
print(json.dumps({'status':'passed','module':anysolid.__file__,'version':anysolid.__version__,
                  'ndof':int(prepared.ndof),'isolated_python':bool(sys.flags.isolated)}))
