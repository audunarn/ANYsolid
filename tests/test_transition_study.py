"""Synthetic arithmetic only: no FE imports, assembly or candidate solves."""
import importlib.util
from fractions import Fraction
from pathlib import Path
import math
import pytest

path=Path(__file__).resolve().parents[1]/'tools/transition_distance_study.py'
spec=importlib.util.spec_from_file_location('_transition_synthetic',path)
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)


def test_exact_quadratic_retains_binary_cancellation():
    # Independently: (1e16+1)+(-1e16+2)=3 for q=(1,1).
    assert study.exact_quadratic([0,2,4],[0,1,0,1],[1e16,1.,-1e16,2.],[1.,1.])==3


def test_exact_quadratic_matches_independent_fraction_sum():
    q=[.1,-.2,.3];data=[3.,.1,-.7,2.,.25];indices=[0,2,0,1,2];pointers=[0,2,4,5]
    expected=sum((Fraction(q[i])*Fraction(data[k])*Fraction(q[indices[k]]) for i in range(3) for k in range(pointers[i],pointers[i+1])),Fraction(0))
    assert study.exact_quadratic(pointers,indices,data,q)==expected


def test_exact_dot_and_empty_form():
    assert study.exact_dot([.1,.2],[.3,-.4])==Fraction(.1)*Fraction(.3)-Fraction(.2)*Fraction(.4)
    assert study.exact_quadratic([0],[],[],[])==0
    assert study.exact_quadratic([0,1],[0],[-0.],[-0.])==0


@pytest.mark.parametrize('data,q', [([math.inf],[1.]),([1.],[math.nan]),([True],[1.])])
def test_nonfinite_or_bool_refused(data,q):
    with pytest.raises(ValueError):study.exact_quadratic([0,1],[0],data,q)


def test_invalid_indices_and_deadline_refused():
    with pytest.raises(ValueError):study.exact_quadratic([0,1],[1],[1.],[1.])
    with pytest.raises(ValueError):study.exact_quadratic([0,2],[0],[1.],[1.])
    with pytest.raises(TimeoutError):study.exact_quadratic([0,1],[0],[1.],[1.],deadline=0.)


def test_registered_count_and_distance_derivation():
    c=study.cases()
    assert [x['primary'] for x in c]==[891,1455,2019]
    assert [x['KKT'] for x in c]==[893,1457,2021]
    assert [x['minimum_ROI_interface_distance'] for x in c]==[.1875,.4375,.6875]
    assert all(x['KKT']<=2100 and x['multiplier_rows']==20 for x in c)
    assert study.output_factor()==6


def test_real_triangular_load_consistent_integrals():
    # Exact integration of linear N times piecewise-linear q. Total area1,
    # first moment1/2; consistent endpoint/interior weights1/6,2/3,1/6.
    weights=study.triangular_line_weights()
    assert weights==[float(Fraction(1,6)),float(Fraction(2,3)),float(Fraction(1,6))]
    assert abs(sum(weights)-1.)<2e-16
    assert abs(sum(w*y for w,y in zip(weights,[0.,.5,1.]))-.5)<1e-16
