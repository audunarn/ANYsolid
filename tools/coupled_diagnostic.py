"""Retain rejection and dimensional evidence for the registered membrane case."""
import importlib.util
import json
from pathlib import Path
from anysolver.solids import SolidModelError

spec=importlib.util.spec_from_file_location('specimen',Path('C:/Github/ANYsolver/tests/test_solid_coupling.py'))
specimen=importlib.util.module_from_spec(spec)
spec.loader.exec_module(specimen)
native,backend,left,right,clamp,tip=specimen.specimen()
native.add_boundary_condition(specimen.BoundaryCondition(name='clamp',node_ids=clamp,
    dof_constraints={key:0. for key in ('ux','uy','uz','rx','ry','rz')}))
load=specimen.LoadCase('extension')
for node in tip:
    load.add_nodal_load(node,forces=[1/len(tip),0.,0.])
model=specimen.SolidModel(native,research_coupling=True)
model.add_region('solid',prepared=backend)
for trace,group in ((left,'left'),(right,'right')):
    model.add_interface('solid',specimen.build_weak_connector(trace,backend,group,multiplier_breakpoints=[0,1]))
try:
    model.solve_static(('extension',),native_load_cases={'extension':load})
except SolidModelError as error:
    print(json.dumps({'status':'NO_GO','error':str(error),'diagnostics':getattr(error,'diagnostics',{})}))
else:
    raise RuntimeError('registered failure unexpectedly disappeared; inspect acceptance gate')
