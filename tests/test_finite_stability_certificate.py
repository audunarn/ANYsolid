"""Fixed <=8x8 synthetic certificates only: no FE fixture, assembly or study."""
from fractions import Fraction
import importlib.util
from pathlib import Path
import numpy as np
import pytest

PATH=Path(__file__).resolve().parents[1]/'tools/finite_stability_study.py'
SPEC=importlib.util.spec_from_file_location('_synthetic_finite_certificate',PATH)
HELPER=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


def at_least(value,exact):
    assert Fraction.from_float(value)>=exact


def test_exact_identity_row_blocks_and_output_factor_four():
    certificate=HELPER.certify_inverse_action(np.eye(3),2,block_columns=2)
    assert certificate['verified']
    at_least(certificate['primal_inverse_upper'],Fraction(1))
    at_least(certificate['modal_traction_couple_amplification_upper'],Fraction(1))
    at_least(certificate['physical_output_amplification_upper'],Fraction(4))
    assert certificate['physical_output_amplification_upper']<4.00000000001
    assert certificate['eta_formation_upper']>0
    assert not certificate['full_inverse_stored']


def test_nonsymmetric_exact_inverse_and_distinct_blocks():
    # inverse([[2,3],[4,0]])=[[0,1/4],[1/3,-1/6]].
    certificate=HELPER.certify_inverse_action([[2.,3.],[4.,0.]],1)
    assert certificate['verified']
    at_least(certificate['primal_inverse_upper'],Fraction(1,4))
    at_least(certificate['modal_traction_couple_amplification_upper'],Fraction(1,2))
    assert certificate['physical_output_amplification_upper']==pytest.approx(1.,rel=1e-12)


def test_actual_three_operation_scaled_kkt_formation_is_covered():
    H=HELPER.build_scaled_kkt([[2.]],np.array([[3.]]),np.array([5.]),np.array([7.]),np.array([11.]),np.array([13.]))
    # Ideal exact H=[[14/5,39/5],[21/11,0]], with actual float formation
    # errors covered in the certificate, not assumed to be exact.
    a,b,c=Fraction(14,5),Fraction(39,5),Fraction(21,11)
    primal=1/c
    dual=1/b+a/(b*c)
    certificate=HELPER.certify_inverse_action(H,1)
    assert certificate['verified']
    at_least(certificate['primal_inverse_upper'],primal)
    at_least(certificate['modal_traction_couple_amplification_upper'],dual)
    at_least(certificate['physical_output_amplification_upper'],4*primal)


def test_right_defect_is_used_not_left_defect():
    H=np.diag([2.,1.]);R=np.array([[.5,.25],[0.,1.]])
    # I-HR has infinity norm1/2, I-RH has norm1/4.
    result=HELPER.certify_inverse_action(H,1,inverse_action=lambda rhs:R@rhs,formation_error=0.)
    assert result['verified']
    assert .5<=result['eta_upper']<.50000000001
    at_least(result['primal_inverse_upper'],Fraction(3,2))


@pytest.mark.parametrize('block',[1,2,3,8])
def test_stream_block_size_preserves_bounds_on_known_eight_by_eight_inverse(block):
    H=2*np.eye(8)+np.diag(np.ones(7),1)
    # Triangular geometric-series inverse R_ij=(-1)^(j-i)/2^(j-i+1).
    primal=max(sum(Fraction(1,2**(j-i+1)) for j in range(i,8)) for i in range(5))
    dual=max(sum(Fraction(1,2**(j-i+1)) for j in range(i,8)) for i in range(5,8))
    result=HELPER.certify_inverse_action(H,5,block_columns=block)
    assert result['verified']
    at_least(result['primal_inverse_upper'],primal)
    at_least(result['modal_traction_couple_amplification_upper'],dual)
    assert result['primal_inverse_upper']==pytest.approx(float(primal),rel=1e-11)
    assert result['modal_traction_couple_amplification_upper']==pytest.approx(float(dual),rel=1e-11)


def test_large_condition_amplification_does_not_pass_physical_allocation():
    result=HELPER.certify_inverse_action(np.diag([2.**-30,1.]),1)
    assert result['verified']
    at_least(result['physical_output_amplification_upper'],Fraction(4*2**30))
    assert result['physical_output_amplification_upper']>1e6


def test_modal_block_condition_amplification_is_separate():
    result=HELPER.certify_inverse_action(np.diag([1.,2.**-30]),1)
    assert result['verified']
    assert result['physical_output_amplification_upper']<1e6
    at_least(result['modal_traction_couple_amplification_upper'],Fraction(2**30))
    assert result['modal_traction_couple_amplification_upper']>5e6


def test_defect_not_below_one_and_singular_are_not_certified():
    bad=HELPER.certify_inverse_action(np.eye(2),1,inverse_action=lambda rhs:np.zeros_like(rhs))
    assert not bad['verified']
    assert bad['eta_upper']>=1
    assert bad['reason']=='right_defect_not_below_one'
    singular=HELPER.certify_inverse_action([[1.,1.],[1.,1.]],1)
    assert not singular['verified']
    assert singular['reason']=='factorization_failed'


@pytest.mark.parametrize('value',[np.inf,np.nan])
def test_nonfinite_computed_inverse_refused(value):
    result=HELPER.certify_inverse_action(np.eye(2),1,inverse_action=lambda rhs:np.full_like(rhs,value))
    assert not result['verified']
    assert result['reason']=='nonfinite_or_wrong_inverse_action'


@pytest.mark.parametrize('kwargs',[{'block_columns':0},{'block_columns':65},{'primal_rows':True},
    {'primal_rows':3},{'physical_output_factor':np.inf},{'formation_error':np.nan}])
def test_invalid_certificate_controls(kwargs):
    args={'primal_rows':1,**kwargs}
    with pytest.raises(ValueError): HELPER.certify_inverse_action(np.eye(2),**args)


@pytest.mark.parametrize('H',[[[np.inf,0.],[0.,1.]],[[1.+1j,0.],[0.,1.]]])
def test_nonfinite_or_complex_matrix_refused(H):
    with pytest.raises(ValueError): HELPER.certify_inverse_action(H,1)


def test_scaling_underflow_subnormal_and_nonpositive_refs_refused():
    for value in (1e-320,1e-300):
        with pytest.raises(ValueError):
            HELPER.scaled_block([[value]],np.array([1.]),np.array([1e-100]))
    with pytest.raises(ValueError): HELPER.scaled_block([[1.]],np.array([0.]),np.array([1.]))


def test_noncanonical_physical_entries_are_refused_before_formation():
    from scipy import sparse
    duplicate=sparse.csr_matrix(([.5,.5],[0,0],[0,2]),shape=(1,1))
    assert not duplicate.has_canonical_format
    with pytest.raises(ValueError,match='canonical'):
        HELPER.scaled_block(duplicate,np.array([1.]),np.array([1.]))


def test_finite_energy_check_is_labelled_numerical_and_unregularized():
    Kr=np.diag([1.,2.,3.]);B=np.array([[1.,0.,0.]])
    result=HELPER.finite_positive_energy_check(Kr,B)
    assert result['assessed'] and result['positive_energy']
    assert result['kind']=='finite_positive_energy_check_not_exact_coercivity_certificate'
    assert result['nullspace_defect_upper']<=1e-10
    assert not result['rank_truncation'] and not result['regularization']
