"""Explicit research multiplier partition policy; no qualification inference.

The connector still requires the caller to supply the returned knots. These
are geometric CORNER stations, never inferred from displacement coefficients.
"""
from fractions import Fraction


def coarsened_p1_partition(shell_corners,solid_corners):
    """Choose fewer corner intervals (shell on ties), keep0,2,4,... and end.

    Both inputs must be finite real 1D partitions from0 to the same positive
    endpoint, strictly increasing, with INPUT spacing ratio<=2. The output is
    an owned immutable float64 subset, with at least two nodes. For an odd
    number of input intervals the final interval is retained; output spacing
    ratio can reach4 and is intentionally not repaired. No normalization,
    snapping, coordinate inference or adaptive qualification occurs here.
    """
    import numpy as np
    partitions=[]
    for value,name in ((shell_corners,'shell_corners'),(solid_corners,'solid_corners')):
        raw=np.asarray(value)
        if raw.ndim!=1 or len(raw)<2 or raw.dtype.kind not in 'iuf':
            raise ValueError(f'{name} must be a real 1D geometric corner partition with at least2 nodes')
        values=np.array(raw,dtype=np.float64,copy=True)
        if not np.isfinite(values).all() or values[0]!=0. or values[-1]<=0:
            raise ValueError(f'{name} must be finite, start0 and end at a positive coordinate')
        exact=[Fraction.from_float(float(v)) for v in values]
        intervals=[b-a for a,b in zip(exact,exact[1:])]
        if any(d<=0 for d in intervals):
            raise ValueError(f'{name} must be strictly increasing')
        if max(intervals)>2*min(intervals):
            raise ValueError(f'{name} input spacing ratio exceeds2')
        partitions.append(values)
    shell,solid=partitions
    if shell[-1]!=solid[-1]:
        raise ValueError('corner partitions must share the exact same positive endpoint')
    chosen=shell if len(shell)<=len(solid) else solid
    indices=list(range(0,len(chosen),2))
    if indices[-1]!=len(chosen)-1: indices.append(len(chosen)-1)
    selected=np.ascontiguousarray(chosen[indices],dtype=np.float64)
    return np.frombuffer(selected.tobytes(),dtype=np.float64)
