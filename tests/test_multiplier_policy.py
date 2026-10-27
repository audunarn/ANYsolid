"""Pure geometric policy tests; independent of ANYsolver and FE fixtures."""
import numpy as np
import pytest
from anysolid.multiplier import coarsened_p1_partition


def test_choose_fewer_geometric_intervals_on_either_side():
    coarse=np.array([0.,.25,.5,.75,1.])
    fine=np.linspace(0.,1.,9)
    np.testing.assert_array_equal(coarsened_p1_partition(coarse,fine),[0.,.5,1.])
    np.testing.assert_array_equal(coarsened_p1_partition(fine,coarse),[0.,.5,1.])


def test_shell_tie_is_explicit_not_coordinate_union():
    shell=[0.,.25,.5,.75,1.]
    solid=[0.,.2,.4,.7,1.]
    np.testing.assert_array_equal(coarsened_p1_partition(shell,solid),[0.,.5,1.])
    np.testing.assert_array_equal(coarsened_p1_partition(solid,shell),[0.,.4,1.])


@pytest.mark.parametrize('corners,expected',[
    ([0.,1.],[0.,1.]),([0.,.5,1.],[0.,1.]),
    ([0.,.3,.6,1.],[0.,.6,1.]),
    ([0.,.2,.4,.6,.8,1.],[0.,.4,.8,1.]),
])
def test_minimal_and_odd_final_endpoint(corners,expected):
    np.testing.assert_array_equal(coarsened_p1_partition(corners,np.linspace(0.,1.,17)),expected)


def test_input_ratio_two_does_not_force_output_ratio_two():
    result=coarsened_p1_partition([0.,2.,4.,5.],np.linspace(0.,5.,11))
    np.testing.assert_array_equal(result,[0.,4.,5.])
    assert np.diff(result).max()/np.diff(result).min()==4.


def test_owned_bytes_immutable_and_no_input_mutation():
    shell=np.linspace(0.,1.,5);solid=np.linspace(0.,1.,9)
    before=shell.copy(),solid.copy()
    result=coarsened_p1_partition(shell,solid)
    assert not np.shares_memory(result,shell) and not np.shares_memory(result,solid)
    np.testing.assert_array_equal(shell,before[0]);np.testing.assert_array_equal(solid,before[1])
    shell[:]=2.;solid[:]=3.
    np.testing.assert_array_equal(result,[0.,.5,1.])
    with pytest.raises(ValueError): result[1]=.4
    with pytest.raises(ValueError): result.setflags(write=True)


@pytest.mark.parametrize('n',[1,2,4,8,16])
def test_registered_refinement_sequence_is_fixed_subset(n):
    shell=np.linspace(0.,1.,n+1);solid=np.linspace(0.,1.,2*n+1)
    result=coarsened_p1_partition(shell,solid)
    expected=shell[::2]
    if expected[-1]!=shell[-1]: expected=np.r_[expected,shell[-1]]
    np.testing.assert_array_equal(result,expected)
    assert len(result)==max(2,(n+1)//2+1)


@pytest.mark.parametrize('bad',[
    [],[0.],[[0.,1.]],[0.,np.nan,1.],[0.,np.inf],[-1.,0.,1.],
    [.1,1.],[0.,0.],[0.,1.,.5],[0.,.5,.5,1.],[0.,.1,1.],
    [False,True],['0','1'],[0.+0j,1.+0j],
])
def test_invalid_input_refused_even_when_other_partition_is_coarser(bad):
    with pytest.raises(ValueError): coarsened_p1_partition([0.,1.],bad)
    with pytest.raises(ValueError): coarsened_p1_partition(bad,[0.,1.])


def test_common_endpoint_is_exact_no_renormalization_or_tolerance():
    with pytest.raises(ValueError,match='exact same'):
        coarsened_p1_partition([0.,1.],[0.,np.nextafter(1.,2.)])


def test_shifted_registered_input_is_not_snapped():
    shell=[0.,.25,.5,.75,1.]
    solid=[0.,.25,.45,.65,.85,1.]
    np.testing.assert_array_equal(coarsened_p1_partition(shell,solid),[0.,.5,1.])
