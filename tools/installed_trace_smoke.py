"""Installed-only small-linear production S3 trace and host API smoke."""
import inspect
import json
from pathlib import Path
import sys
import numpy as np
import anysolver
from anysolver.elements import create_shell_element
from anysolver.solid_trace import ShellEdgeTrace
from anysolver.solids import SolidModel

assert sys.flags.isolated
assert "site-packages" in Path(anysolver.__file__).parts
assert "diagnostic_strong_tying" in inspect.signature(SolidModel.add_interface).parameters
model = anysolver.FEModel("installed-S3-linear-trace")
model.add_material("m",1000.,0.)
for node,xyz in enumerate(((0.,0.,0.),(1.,0.,0.),(0.,1.,0.)),1):
    model.add_node(node,*xyz)
model.add_element(1,create_shell_element(1,[1,2,3],"m",thickness=.2,reference_normal=(0.,0.,1.)))
trace = ShellEdgeTrace(model,[(1,0)])
q = np.zeros(trace.ndof)
q[model.mesh.dof_manager.get_node_dofs(1)[4]] = 1.
value = trace.displacement_operator([[.5,0.,0.]]) @ q
np.testing.assert_allclose(value,[0.,0.,-.125],atol=1e-14)
print(json.dumps({"status":"passed", "scope":"installed small-linear S3 trace smoke only",
                  "origin":anysolver.__file__,"trace":value.tolist()}))
