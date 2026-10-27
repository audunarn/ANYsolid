# W1 source audit and environment

The read baseline is ANYsolver
1cff283d67ba31bf6d5dc816e2b55bd8359daa9b. DOFManager assigns six DOFs per
native node; the new SolidModel keeps that manager untouched and appends
explicit independent coefficient blocks. A separate wrapper avoids attaching
invisible solid state to ordinary FEModel-only analysis paths.

Production selectors are E4-PL Q4 and E4-PL S3 V2D. The initial trace accepts
exact Q4 only. The host's existing submodel interpolation confirms global
axial rotations and displacement transport theta cross(target-reference).
Physical director authority can differ from connectivity's numbered normal.
S3's reference-surface-offset convention requires separate treatment and was
not generalized from node count or enabled by this candidate.

Native affine constraints use u=T*q+u0. The existing linalg factorization
handle supports symmetric indefinite matrices and solve_many. The solid path
uses those public facilities with an explicit SuperLU choice. Full reaction
recovery includes C.T*lambda; native and solid vectors retain separate slices.

Dependency direction remains ANYsolver -> optional ANYsolid[skfem], never the
reverse. ANYsolid's numerical mesh snapshot consumes arrays, not geometry or
mesher-owned models. No ANYgeometry, ANYmesher, ANYfileIO, ANYmaterial or ANYfem
source changes are part of this workflow.

Tested runtime: CPython 3.11 on Windows x64, NumPy 2.4.6, SciPy 1.17.1,
scikit-fem 12.0.2, pytest 9.1.1. Initial new package license is MPL-2.0, aligned
with the ecosystem. Numerical dependency license texts remain in their
installed distributions; scikit-fem is an external dependency, not copied code.
No wheel-size, installed-footprint, import-only timing or RSS claim is made.
The configured Windows/Linux Python 3.11-3.14 CI matrix has not run remotely.

Existing dirty result work is protected and its content hashes were checked.
Source regression checks passed; a measured historical shell-only performance
baseline and release-level clean-checkout verification remain outstanding.
