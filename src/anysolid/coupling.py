"""Research-only planar weak section-moment coupling, no production claim.

The multiplier partition is explicit and separate from integration partitions.
Five section traction modes are linear along that partition: xyz constants in
thickness and two thickness-linear SHELL-plane tangents. Degree-four upstream
triangle quadrature is used after clipping at every shell/multiplier breakpoint.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
import hashlib
from types import MappingProxyType
import numpy as np
from scipy import sparse


def _area(poly):
    p=np.asarray(poly)
    return .5*abs(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))) if len(p)>=3 else 0.


def _clip(poly,normal,limit):
    """Convex chart polygon clipped by normal.dot(x)<=limit."""
    if not len(poly):
        return []
    output=[]
    previous=np.asarray(poly[-1]); a=float(previous@normal-limit)
    for item in poly:
        point=np.asarray(item); b=float(point@normal-limit)
        if (a<=0)!=(b<=0):
            output.append(previous+(point-previous)*(a/(a-b)))
        if b<=0:
            output.append(point)
        previous,a=point,b
    return output


def _intersection(first,second):
    signed=np.sum(second[:,0]*np.roll(second[:,1],-1)-second[:,1]*np.roll(second[:,0],-1))
    polygon=list(first)
    for a,b in zip(second,np.roll(second,-1,axis=0)):
        edge=b-a
        normal=np.array([edge[1],-edge[0]])*np.sign(signed)
        polygon=_clip(polygon,normal,normal@a)
    return polygon


def _positive_area_triangle_intersection(first,second):
    """Exact positive-area SAT on the supplied binary64 chart triangles.

    A nondegenerate convex pair has positive intersection area iff no edge
    line of either triangle weakly separates their interiors. Exact rational
    orientation signs distinguish contact from clipping/shoelace roundoff.
    This is only a confirmation guard after the existing float area threshold;
    it changes neither integration polygons nor the dimensional tolerance.
    """
    triangles=[]
    for value in (first,second):
        array=np.asarray(value,float)
        if array.shape!=(3,2) or not np.isfinite(array).all():
            raise ValueError('overlap predicate requires finite (3,2) triangles')
        triangles.append(tuple(tuple(Fraction.from_float(float(v)) for v in p) for p in array))
    def orient(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    signs=[]
    for triangle in triangles:
        area=orient(*triangle)
        if area==0:
            return False
        signs.append(1 if area>0 else -1)
    for index,(triangle,sign) in enumerate(zip(triangles,signs)):
        other=triangles[1-index]
        for a,b in zip(triangle,triangle[1:]+triangle[:1]):
            if all(sign*orient(a,b,p)<=0 for p in other):
                return False
    return True


def _signature(matrix):
    digest=hashlib.sha256(str(matrix.shape).encode())
    for array in (matrix.indptr,matrix.indices,matrix.data):
        digest.update(array.tobytes())
    return digest.hexdigest()


@dataclass(frozen=True)
class CouplingOperator:
    C_shell: sparse.csr_matrix
    C_solid: sparse.csr_matrix
    affine: np.ndarray
    metadata: dict
    _trace: object
    _backend_signature: str
    _operator_signatures: tuple
    formulation: str='weak_section_moments_v1'

    def validate(self,native,prepared):
        self._trace.validate()
        if native is not self._trace.model or prepared.cache_signature()!=self._backend_signature:
            raise ValueError('stale or wrong-model coupling operator')
        if (_signature(self.C_shell),_signature(self.C_solid))!=self._operator_signatures:
            raise ValueError('mutated coupling operator; rebuild from the physical traces')
        if self.C_shell.shape[1]!=self._trace.ndof or self.C_solid.shape[1]!=prepared.ndof:
            raise ValueError('coupling coefficient layout mismatch')

    def interface_forces(self,multipliers):
        return self.C_shell.T@multipliers,-self.C_solid.T@multipliers


def build_weak_connector(trace,prepared,boundary_group,*,multiplier_breakpoints):
    """Build an explicitly unqualified candidate; caller must opt into research.

    The multiplier partition MUST be selected prospectively, sufficiently
    coarse for both traces. No automatic rule can establish inf-sup stability.
    """
    from skfem.quadrature import get_quadrature_tri
    trace.validate()
    knots=np.array(multiplier_breakpoints,float,copy=True)
    tolerance=trace.tolerance
    if knots.ndim!=1 or len(knots)<2 or not np.isfinite(knots).all() or np.any(np.diff(knots)<=tolerance) or abs(knots[0])>tolerance or abs(knots[-1]-trace.length)>tolerance:
        raise ValueError('multiplier partition must increase from 0 to interface length')
    mesh=prepared.mesh
    try:
        ids=mesh.boundary_groups[boundary_group]
    except KeyError as exc:
        raise ValueError('unknown solid interface boundary group') from exc
    facets=mesh.boundary_facets[np.isin(mesh.boundary_ids,ids)]
    if not len(facets) or len(facets)>4096:
        raise ValueError('research connector needs 1..4096 selected boundary facets')
    triangles=[]
    for facet in facets:
        points=mesh.coordinates[facet]
        chart=trace.chart(points)
        plane=(points-trace.reference_start)@trace.solid_outward
        normal=np.cross(points[1]-points[0],points[2]-points[0])
        normal/=np.linalg.norm(normal)
        if np.max(abs(plane))>tolerance or normal@trace.solid_outward<1-1e-10 or np.min(chart[:,0])<-tolerance or np.max(chart[:,0])>trace.length+tolerance or np.max(abs(chart[:,1]))>trace.thickness/2+tolerance:
            raise ValueError('solid interface geometry, normal or rectangular extent mismatch')
        triangles.append(chart)
    total=sum(_area(t) for t in triangles)
    expected=trace.length*trace.thickness
    if abs(total-expected)>max(tolerance*(trace.length+trace.thickness),1e-12*expected):
        raise ValueError('solid interface has missing/duplicated area')
    # AABB sweep checks positive-area overlap independently of total area.
    ordered=sorted(triangles,key=lambda t:float(t[:,0].min()))
    active=[]
    for triangle in ordered:
        lo,hi=triangle.min(axis=0),triangle.max(axis=0)
        active=[old for old in active if old[:,0].max()>lo[0]+tolerance]
        for old in active:
            if old[:,1].max()<=lo[1]+tolerance or old[:,1].min()>=hi[1]-tolerance:
                continue
            if (_area(_intersection(triangle,old))>tolerance*tolerance
                    and _positive_area_triangle_intersection(triangle,old)):
                raise ValueError('overlapping solid interface facets')
        active.append(triangle)
    rule,weights=get_quadrature_tri(4)
    cuts=np.unique(np.concatenate((trace.breakpoints,knots)))
    samples=[]; measures=[]
    for triangle in triangles:
        for left,right in zip(cuts[:-1],cuts[1:]):
            if right<triangle[:,0].min() or left>triangle[:,0].max():
                continue
            polygon=_clip(list(triangle),np.array([-1.,0.]),-left)
            polygon=_clip(polygon,np.array([1.,0.]),right)
            for i in range(1,len(polygon)-1):
                small=np.array([polygon[0],polygon[i],polygon[i+1]])
                jac=2*_area(small)
                if jac<=np.finfo(float).tiny:
                    continue
                samples.extend(small[0]+rule[0,:,None]*(small[1]-small[0])+rule[1,:,None]*(small[2]-small[0]))
                measures.extend(weights*jac)
    chart=np.array(samples); measures=np.array(measures)
    points=trace.points(chart)
    nrows=5*len(knots)
    rows=[]; cols=[]; data=[]
    for p,(s,z) in enumerate(chart):
        k=min(max(np.searchsorted(knots,s,side='right')-1,0),len(knots)-2)
        alpha=(s-knots[k])/(knots[k+1]-knots[k])
        modes=np.vstack((np.eye(3),2*z/trace.thickness*trace.tangent,2*z/trace.thickness*trace.conormal))
        for node,value in ((k,1-alpha),(k+1,alpha)):
            for mode,vector in enumerate(modes):
                for component in range(3):
                    rows.append(5*node+mode); cols.append(3*p+component)
                    data.append(value*vector[component]*measures[p])
    W=sparse.csr_matrix((data,(rows,cols)),shape=(nrows,3*len(points)))
    Csh=(W@trace.displacement_operator(points)).tocsr()
    Cv=(W@prepared.trace(points)).tocsr()
    # Necessary two-sided row-rank check, deliberately not a stability claim.
    ranks={}
    for name,matrix in (('shell',Csh),('solid',Cv)):
        if nrows>256:
            raise ValueError('research rank diagnostic limited to 256 multiplier rows')
        scales=np.sqrt(np.asarray(matrix.multiply(matrix).sum(axis=1)).ravel())
        if np.any(scales==0):
            raise ValueError(f'{name} multiplier pairing has zero rows')
        scaled=sparse.diags(1/scales)@matrix
        spectrum=np.linalg.eigvalsh((scaled@scaled.T).toarray())
        rank=int(np.count_nonzero(spectrum>np.finfo(float).eps*max(matrix.shape)*max(spectrum[-1],1)))
        ranks[name]=rank
        if rank<nrows:
            raise ValueError(f'one-sided {name} multiplier kernel: use a coarser explicit multiplier partition')
    affine=np.frombuffer(np.zeros(nrows).tobytes(),dtype=float)
    metadata={'status':'NO_GO_PRODUCTION_UNQUALIFIED','area':total,'quadrature_area':float(measures.sum()),
              'quadrature_points':len(points),'quadrature_degree':4,'multiplier_breakpoints':knots.tolist(),
              'trace_pairing_ranks':ranks,'section_modes':5,'stability':'not established'}
    return CouplingOperator(Csh,Cv,affine,MappingProxyType(metadata),trace,prepared.cache_signature(),
                            (_signature(Csh),_signature(Cv)))
