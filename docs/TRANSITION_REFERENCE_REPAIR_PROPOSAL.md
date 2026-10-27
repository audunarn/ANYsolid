# Proposed reference repair after the failed convergence gate

The registered 3D reference pair failed its unchanged 0.1% displacement
convergence criterion. It remains failed and consumed. Both individual solves,
energy convergence and common-point stress convergence passed. No third mesh or
coupled case was executed. See `transition-distance-6b4550d018`.

The controlling retained coefficient is lateral displacement at the loaded end:
`(x,y,z)=(2,.6875,.1)`. Coarse/fine values are
`.0007670615335005832` and `.0008114102368193117` metres. Their difference divided
by the registered `.015m` scale is `.0029565802212485667`, exceeding `.001`.
Changing the ROI or checking only its much smaller error would not satisfy the
global criterion. All three reference directions changed, so the evidence does
not isolate the most efficient next mesh direction.

## An exact dimension reduction for this particular BVP

An alternative prospective route is a full-body 2D reference extruded through
the thickness. This requires explicit adoption and independent mathematical
review; it is not a replacement of the failed result.

For the registered material only, Poisson ratio is exactly zero, so the 3D
Lamé parameter lambda is zero. Geometry, end traction and clamp values are
independent of z. Take `u=(ux(x,y),uy(x,y),0)`. Then all strains involving z
vanish, as do sigma_zz, sigma_xz and sigma_yz. The free top and bottom face
conditions hold exactly. The x/y equilibrium equations reduce to 2D elasticity,
and the full left-face clamp and right-face traction remain identical. Uniqueness
of the clamped positive-energy 3D problem identifies this extruded solution with
the 3D continuum solution. This argument does not apply to general nonzero
Poisson ratio, z-dependent loads, eccentric loads or different constraints.

The weak argument does not assume that arbitrary 3D test fields are independent
of z. Average their x/y components through the thickness. Their averages are
admissible 2D test fields and the 3D internal and external work reduce to the
same thickness-integrated 2D identity. The z test component contributes zero.
Uniqueness follows because a homogeneous difference has zero strain energy,
hence is a rigid motion, and the full clamped face eliminates that motion.

Integrate the 2D elastic operator multiplied by the physical thickness `.2m`.
Apply the physical line load qx(y)=4y for y<=.5 and 4(1-y) above .5, in N/m.
It integrates to 1N and equals thickness times the original 3D traction.
Recover 3D stress with the original E=1000Pa constitutive law, rather than the
thickness-scaled resultant tensor. Energy is the thickness-integrated 3D energy.
Embed reference stress into a full 3-by-3 tensor with all z components zero.

## Bounded prospective verification, not current execution authority

Proposed whole-body P2 triangle grids: 48x32 and 96x64, with 12,610 and 49,794
coefficients respectively. Retain the original physical geometry, load, clamp,
all global displacement samples, every fixed 3D ROI stress sample and all
normalizations. Keep reference differences <=.001 field/energy and <=.005 stress;
keep measured physical comparisons <=.009 field/energy and <=.045 stress, with
the original 1%/5% reporting as before. Retain all residual, exact work, force,
moment, symmetry, certificate and output-allocation limits.

Before acceptance, verify the dimension-reduction derivation, thickness/load
conversion, affine/rigid/engineering-shear recovery, common-point interpolation,
global support reactions and exact work. Both references must converge before
any of the three unchanged coupled cases runs. Proposed bounds remain two
reference solves, three coupled solves, three KKT certificates, coupled KKT<=2100,
reference coefficients<=50000, and one 180-second supervised process. No extra
reference or automatic retry is proposed. Independent review precedes execution.

This is a reviewable proposal only. The failed registration authorizes no new
execution; a fresh bounded qualification registration and authority are needed.
It would cover the nonuniform membrane slice, not the outstanding transverse
shear/bending transition-distance reference problem or platform gates.

Independent non-author mathematical review found this equivalence and the
thickness/load/stress/energy conversions sound for the stated BVP. The reviewer
used the same model family. This is a reviewed proposal, not implemented or
executed qualification and not a guarantee that the proposed meshes converge.
