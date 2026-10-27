"""Public P2 wheel smoke in an isolated interpreter, without checkout imports."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

CODE = r'''
import json, pathlib, sys
import anysolid
assert not {'skfem','anysolver'} & sys.modules.keys()
assert not pathlib.Path(anysolid.__file__).resolve().is_relative_to(pathlib.Path(sys.argv[1]).resolve())
import numpy as np
mesh = anysolid.SolidMesh(coordinates=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]),
    cells=np.array([[0,1,2,3]]), node_ids=[1,2,3,4], cell_ids=[1])
prepared = anysolid.prepare(mesh, {'elastic_modulus':1000., 'poisson_ratio':.3}, order=2)
K = prepared.assemble_linear()
assert K.shape == (30,30)
assert np.max(np.abs((K-K.T).data), initial=0.) < 1e-10
assert prepared.rigid_modes().shape == (30,6)
print(json.dumps({'origin':anysolid.__file__, 'ndof':int(prepared.ndof), 'status':'passed'}))
'''


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="anysolid-wheel-") as folder:
        subprocess.run([sys.executable, "-I", "-c", CODE,
                        str(Path(__file__).resolve().parents[1] / "src")],
                       cwd=folder, check=True, timeout=30)
