# Facet overlap diagnosis and bounded guard repair

Frozen scientific study attempt `workflow1-extended-patches-030e6dbb32` remains
retained: the first three cases passed, then ratio1:8 was rejected before its
solve. No study source/manifest was changed or scientific case retried here.

## Exact geometry witness

Bounded geometry-only diagnostic evidence:
`evidence/w1/facet-overlap-geometry-40cd3e8814`, process1.7179999999934807 s
under30 s; zero stiffness assemblies/solves. Source coupling fingerprint was
`99abc4c4191e9f4ce402e8c49a57884138ca12a234bf1369e8f40341cc71e86c`.
Both 32-triangle end faces were inspected with the original AABB candidate
selection. Left face has two false rejection pairs(11,10),(27,26); right
face has none. Exact-rational clipping on each rejected pair gives area0.

Minimal left-face witness, facets[23,24,5] and[5,24,6]:

| Triangle | Chart(s,z) vertices |
| --- | --- |
| first | (.625,0),(.75,0),(.625,-.1) |
| second | (.625,-.1),(.75,0),(.75,-.1) |

They share actual vertex rows5 and24: world coordinates(0,.625,-.1) and
(0,.75,0). Their nonshared vertices are(0,.625,0) and(0,.75,-.1), lying on
strict opposite sides of the common edge. Thus the exact intersection is
ONLY that segment, with zero area. This statement holds for the actual
binary64 coordinates: rational endpoints are(5/8,-3602879701896397/36028797018963968)
and(3/4,0). Exact orientation signs for the other vertices are opposite.

Floating clipping produces an extra point(.7499999999999999,0) next to
(.75,0). The resulting spurious sliver has computed shoelace area
6.938893903907228e-18, exceeding the unchanged tol²=1.0000000000000001e-20.
Translating the area calculation still gives5.204170427930421e-18; translation
alone does not eliminate the already perturbed clipping vertices. The
diagnostic retained an informational NumPy 2D-cross deprecation warning.

## Adopted isolated repair

Parent authorized a secondary exact positive-area triangle-intersection
confirmation before rejecting a floating computed area above tol². The
implementation uses exact Fraction orientations of the supplied binary64
chart triangles and the convex separating-axis theorem. For each edge of
either nondegenerate triangle, if every vertex of the other lies outside or
on that edge's interior half-plane boundary, the interiors are separated and
their intersection has zero area. If no such weak separating edge exists,
their intersection has positive area. Both windings are handled explicitly.
Degenerate triangles have zero-area intersection by definition.

Fractions are used only after the original floating computed-area threshold
is exceeded, so ordinary valid candidate pairs do not require the exact path.
No error-bound heuristic, fitted tolerance or unconditional shared-edge skip
is used. Shared-edge triangles on the SAME side still overlap and must fail.
All existing tol² thresholds, floating area/intersection functions, quadrature,
integration cuts, multipliers, load/reference data and study sources remain
unchanged. This guard confirms only the existing rejection path; it does not
broaden the existing detector for below-threshold overlaps or certify arbitrary
global meshes.

Focused verification is pending. Pure ANYsolid tests use only adapter/chart
math, without ANYsolver import. Actual production1:8 construction and genuine
overlap rejection are separate ANYsolver tests. No scientific solve/campaign
is authorized by this repair; parent independent review precedes continuation.
