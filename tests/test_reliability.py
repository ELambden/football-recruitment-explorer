import pytest

from football_recruitment.reliability import shrink_rate


def test_shrink_rate_moves_low_sample_towards_prior() -> None:
    result = shrink_rate(count=2, nineties=1, prior_mean=0.5, prior_nineties=8)
    assert result == pytest.approx((2 + 0.5 * 8) / 9)


def test_shrink_rate_rejects_negative_exposure() -> None:
    with pytest.raises(ValueError):
        shrink_rate(count=1, nineties=-1, prior_mean=0.5)

