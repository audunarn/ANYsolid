# Shear investigation — 27 October 2026

The retained coupled case remains failed. A new, independently reviewed
four-control design tested the same solid region with full analytical end
displacements, no shells/connector, and free lateral surfaces. It used the
unchanged reference, all original interior samples, and unchanged stress scales.

| Mesh | DOFs | Nodal-interpolant shear error | Solved-control shear error |
| --- | ---: | ---: | ---: |
| Original Nx4 Ny1 Nz8 | 1377 | 81.22% | 75.24% |
| Axial-only Nx8 Ny1 Nz8 | 2601 | 19.83% | 20.21% |
| Width-only Nx4 Ny2 Nz8 | 2295 | 81.22% | 77.82% |
| Thickness-only Nx4 Ny1 Nz16 | 2673 | 81.69% | 76.61% |

Four solves completed, zero execution failures, all residual gates passed;
process wall 2.922 s. No retry or additional mesh was run under this request.
Original-mesh quadrature coordinates exactly matched the retained coupled case.
Evidence: evidence/w1/shear-isolation-c9e5b50eda. The assigned four-solve authority
is consumed and its raw prefix/results remain immutable.

This demonstrates that a large recovered shear error occurs without a connector
and identifies strong axial resolution sensitivity in these controls. It does
not prove the absence or size of transition/native error: the boundary-value
problems differ, and the locations of maximum error can differ. The nodal
interpolant is not a best-approximation bound. Two axial resolutions do not
establish a convergence rate; width and thickness interactions remain possible.

An analytical calculation at the original controlling point also shows strong
gradient cancellation: the sum defining shear is about 732 times smaller than
the sum of the magnitudes of its two displacement-gradient terms. This explains
why accurate displacement/energy alone cannot certify accurate recovered shear;
it does not identify the measured error's sole cause. Inputs and derivation are
retained in evidence/w1/shear-cancellation-witness.json.

The next separately registered question was a paired control/coupled comparison
at Nx16 and Nx32, with native axial4, Ny1, Nz8 and all physical/operator/accuracy
definitions fixed. Each pair shares the exact prepared solid and compares
pointwise stresses, not merely maxima at different locations. Four new sparse
solves, at most 12000 primary DOFs and one 180-second process, are registered in
paired_axial_manifest.json. No product kernel, smoothing, reference or tolerance
change was part of the investigation.

## Paired result

The two pairs completed with four solves, zero execution failures and no retries
in 6.437 s. Each control and coupled solve shared the identical prepared solid,
quadrature coordinates and fixed mask. Independent non-author review reproduced
the pointwise comparisons from the retained tensors.

| Axial resolution | Primary DOFs, coupled | Control shear error | Coupled shear error | Pointwise paired shear difference |
| --- | ---: | ---: | ---: | ---: |
| Nx16 Ny1 Nz8 | 5169 | 4.39603% | 4.56495% | 0.93372% |
| Nx32 Ny1 Nz8 | 10065 | 1.36045% | 1.41254% | 0.17791% |

Both new cases meet the unchanged 5% stress, 1% coupled global-response and
1e-9 residual targets. Coupled tip displacement/energy errors are about 0.115%,
with native axial4 still fixed. No original failure was relabelled a pass.
Evidence: evidence/w1/paired-axial-03080fe925. Its four-solve authority is consumed.

The combined evidence supports coarse axial solid discretization as a major
contributor to the original error; a product-kernel repair is not established
by these data. Pointwise differences remain differences between boundary-value
problems, not a uniquely isolated connector error. No convergence rate,
arbitrary-mesh accuracy, uniform stability or general production support follows
from two finite cases. Production remains NO_GO until the other qualification
gates pass; these two benchmark cases may be recorded as targets met.
