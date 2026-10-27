"""Exact chart-triangle overlap checks; no ANYsolver dependency or FE solves."""
import numpy as np
import pytest
from anysolid.coupling import _area, _intersection, _positive_area_triangle_intersection


A=np.array([[0.,0.],[2.,0.],[0.,2.]])


@pytest.mark.parametrize('other,expected',[
    ([[0.,0.],[2.,0.],[2.,-2.]],False), # shared edge, opposite sides
    ([[2.,0.],[3.,0.],[2.,1.]],False), # shared vertex only
    ([[3.,3.],[4.,3.],[3.,4.]],False), # disjoint
    ([[.2,.2],[.4,.2],[.2,.4]],True), # contained
    ([[0.,0.],[2.,0.],[2.,2.]],True), # shared edge but same side: real overlap
    ([[.5,0.],[2.5,0.],[.5,2.]],True),
    ([[0.,0.],[1.,0.],[2.,0.]],False), # degenerate intersection has no area
])
@pytest.mark.parametrize('reverse_first,reverse_second',[(False,False),(True,False),(False,True),(True,True)])
def test_exact_sat_contacts_and_positive_overlaps(other,expected,reverse_first,reverse_second):
    first=A[::-1] if reverse_first else A
    second=np.array(other)[::-1] if reverse_second else np.array(other)
    assert _positive_area_triangle_intersection(first,second) is expected
    assert _positive_area_triangle_intersection(second,first) is expected


@pytest.mark.parametrize('scale',[1e-4,1.,1e4])
@pytest.mark.parametrize('angle',[0.,.731])
def test_rotation_translation_and_rescaling_preserve_represented_contacts(scale,angle):
    R=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    shift=np.array([1024.,-2048.])
    transform=lambda x: scale*np.asarray(x)@R.T+shift
    first=transform(A)
    contact=transform([[0.,0.],[2.,0.],[2.,-2.]])
    interior=transform([[.25,.25],[.5,.25],[.25,.5]])
    assert not _positive_area_triangle_intersection(first,contact)
    assert _positive_area_triangle_intersection(first,interior)


def test_near_collinear_true_positive_is_not_discarded_as_contact():
    h=2.**-40
    first=np.array([[0.,0.],[1.,0.],[0.,h]])
    second=np.array([[0.,0.],[1.,0.],[1.,h]])
    assert _area(_intersection(first,second))>1e-20
    assert _positive_area_triangle_intersection(first,second)


def test_actual_ratio_1_8_false_positive_witness_is_exact_edge_contact():
    first=np.array([[.625,0.],[.75,0.],[.625,-.1]])
    second=np.array([[.625,-.1],[.75,0.],[.75,-.1]])
    # Preserve the failed computed area and original dimensional threshold.
    assert _area(_intersection(first,second))==6.938893903907228e-18
    assert _area(_intersection(first,second))>1e-10**2
    assert not _positive_area_triangle_intersection(first,second)


@pytest.mark.parametrize('bad',[
    np.zeros((4,2)), [[0.,0.],[1.,0.],[np.nan,1.]],
])
def test_invalid_triangles_are_refused(bad):
    with pytest.raises(ValueError): _positive_area_triangle_intersection(A,bad)
