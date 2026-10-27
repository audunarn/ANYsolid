# Retained-only exact work adjudication: early checkpoint

The failed original double contraction remains FAILED in immutable evidence
`evidence/w1/revised-broader-physics-016d398003`. Only its two-region case is
eligible for this separate arithmetic correction. No physical model, saved
coefficient, load, matrix value, energy reference or1e-10 limit changes.

Actual saved inputs: canonical Kr810x810/32241 entries,828 physical
coefficients (108 native,405 solid1,315 solid2),18 fixed native DOFs, all
prescribed values0. Saved loads are nodal My on14/16/18, all solid loads0.
Frozen fixture allocates nodes in ascending IDs; frozen DOFManager.add_node
allocates contiguous [ux,uy,uz,rx,ry,rz]. Thus the saved native node map can
be independently reconstructed and checked without importing the FE library.
Kr free order is explicitly retained and must equal the exact complement of
the fixed DOFs. Regions append in saved declared order solid1,solid2.

Plan: stdlib-only validator rejects source/input/terminal/ordering/support or
load ambiguity; register all archive/harness/manifest/source hashes and explicit
node/region/free ordering. Execution computes exact Fraction q^T Kr q and
q^T F from binary float values and compares their exact normalized difference
with Fraction(1e-10). Default mode performs only schema/identity checks.
No FE import, assembly, factorization or solve is permitted. One30s process /
25s inner deadline,50000 entries/1000 physical coefficients, no retry.

Remaining: implement runner/manifest, perform only AST/schema validation and
freeze for independent preflight. Exact arithmetic has NOT been executed.

## Final frozen proposal

Runner and manifest are implemented and frozen for independent preflight.
33 input/source hashes pin the full raw JSONL, receipt, outer identity,
stderr, registered broader source/manifest, fixture and all retained outer
source modules. Embedded identity and exact source/input registrations are
cross-checked. The complete original scientific-failure terminal and all
three solve counts must remain intact. Both unaffected cases must retain
their original passes; only the original isolated double-work failure is
eligible. No retained exploratory arithmetic result is reused.

The node map is not guessed from coordinates: frozen FEModel.add_node
delegates to Mesh.add_node, which immediately allocates DOFManager's six
contiguous coordinates and stores them in the node map. The frozen fixture
calls add_node sequentially with ID=len(nodes)+1 in the explicit strip/y/x
loop. All18 saved node coordinates are reconstructed from this traversal
and checked against both saved mesh and physical result. The retained free
list must equal the exact ascending complement of supports0..5,12..17,24..29.
Region order and canonical Kr construction are source-pinned and checked.
All828 actual coefficients are read from the physical result, never replaced
by analytical values. Native loading uses only the saved loads on14/16/18
mapped through this proven DOF map; their component ownership and registered
actual values must match. Both actual saved solid load arrays must be zero.
All support coefficients, saved affine vector and support work must be zero.

Target records are raw lines20(metric),38(load/mesh),39(physical), individually
hashed as well as protected by the whole JSONL hash. CSR must be sorted,
duplicate-free, finite, zero-eliminated810x810 with32241 entries. The exact
route computes the full unsymmetrized canonical quadratic form and saved
external work in Fraction arithmetic; no averaging or cancellation shortcut.
It compares the exact normalized difference to Fraction(1e-10). Exact rational
numerator/denominator and rounded display are emitted separately. The result
can adjudicate only this saved discrete work quantity, not continuum/model
error or production qualification.

Verification actually performed: Python AST parsing and stdlib-only schema/
identity/ordering/shape validation. The initial unpersisted schema check found
a KeyError because the retained harness hash is nested in the embedded
manifest, rather than at header top level. This implementation lookup was
corrected; no contractions/FE work occurred in that failed check.

Persisted exact command:
`.venv/Scripts/python.exe tools/run_check.py --name exact-retained-work-schema --timeout 30 -- python tools/exact_retained_work.py`

Exit0,3 JSONL records(identity/schema/proposal), process wall
0.3129999999946449s, cleanup verified with0 active processes. Evidence:
`evidence/w1/exact-retained-work-schema-7ab0465525`.
Exact contractions executed0; FE imports/assemblies/factorizations/solves0.
The independent schema audit also asserted no NumPy/SciPy/skfem/ANYsolver
module import. No unit tests or exact-energy run was performed.

Runner SHA256:
`78ec76e1fec1fb24092cf6e8755f8fa1b9411b15dd4861c67a7adfd71bda09bd`.
Manifest SHA256:
`cd96885e0cbad207fdc8d1b96a3104d22887d8ea9f8f4964abdba667785a53f6`.

Pending independent preflight and explicit authorization, the ONLY proposed
execution is:
`.venv/Scripts/python.exe tools/run_check.py --name exact-retained-work --timeout 30 -- python tools/exact_retained_work.py --execute`.
One30s outer/25s inner audit, no automatic retry. Original DOUBLE evaluation
remains FAILED_UNCHANGED regardless of this separate result; production NO_GO.
