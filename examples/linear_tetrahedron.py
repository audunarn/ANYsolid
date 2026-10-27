"""Small SI displacement solve. Run with the package installed or PYTHONPATH=src."""
import numpy as np
from scipy.sparse.linalg import spsolve
from anysolid import SolidMesh, prepare


def main():
    mesh = SolidMesh(
        coordinates=[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]],
        cells=[[0, 1, 2, 3]],
        boundary_facets=[[0, 2, 1]],
        boundary_ids=[100],
        boundary_groups={'clamp': [100]},
        provenance={'example': 'unit tet4 under constant body force'})
    prepared = prepare(mesh, {'elastic_modulus': 200e9, 'poisson_ratio': .3}, order=2)
    k = prepared.assemble_linear()
    f = prepared.body_load([0., 0., -7800. * 9.81])
    fixed = prepared.boundary_dofs('clamp')
    free = np.setdiff1d(np.arange(prepared.ndof), fixed)
    a = np.zeros(prepared.ndof)
    a[free] = spsolve(k[free][:, free], f[free])
    print('tip displacement (m):', prepared.trace([[0., 0., 1.]]) @ a)
    print('force equilibrium norm (N):', np.linalg.norm((k @ a - f)[free]))
    print('sampling:', prepared.recover(a).sampling)
    return a


if __name__ == '__main__':
    main()
