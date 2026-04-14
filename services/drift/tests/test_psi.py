import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from psi import compute_psi


def make_normal(mean=0.0, std=1.0, n=500, seed=42):
    rng = np.random.default_rng(seed)
    return rng.normal(mean, std, n)


def test_identical_distributions_near_zero():
    """PSI of a distribution against itself should be ~0."""
    data = make_normal()
    psi = compute_psi(data, data)
    assert psi < 0.01


def test_stable_similar_distributions():
    """Two samples from the same distribution should give PSI < 0.1."""
    ref = make_normal(seed=1)
    cur = make_normal(seed=2)
    psi = compute_psi(ref, cur)
    assert psi < 0.1


def test_shifted_distribution_triggers_alert():
    """A distribution shifted by 3 std devs should give PSI >= 0.2."""
    ref = make_normal(mean=0.0, std=1.0, seed=1)
    cur = make_normal(mean=3.0, std=1.0, seed=2)
    psi = compute_psi(ref, cur)
    assert psi >= 0.2


def test_psi_is_non_negative():
    """PSI is always >= 0."""
    ref = make_normal(seed=10)
    cur = make_normal(mean=1.0, seed=11)
    psi = compute_psi(ref, cur)
    assert psi >= 0.0


def test_psi_symmetric_approx():
    """PSI(ref, cur) and PSI(cur, ref) should be close (not identical due to binning)."""
    ref = make_normal(mean=0.0, seed=1)
    cur = make_normal(mean=0.5, seed=2)
    psi_forward = compute_psi(ref, cur)
    psi_reverse = compute_psi(cur, ref)
    assert abs(psi_forward - psi_reverse) < 0.5


def test_custom_bin_count():
    """compute_psi works with non-default n_bins."""
    ref = make_normal(seed=1)
    cur = make_normal(seed=2)
    psi = compute_psi(ref, cur, n_bins=20)
    assert psi >= 0.0


def test_small_current_window():
    """Should not crash with a small current window (10 samples)."""
    ref = make_normal(n=500, seed=1)
    cur = make_normal(n=10, seed=2)
    psi = compute_psi(ref, cur)
    assert psi >= 0.0


def test_returns_float():
    ref = make_normal(seed=1)
    cur = make_normal(seed=2)
    psi = compute_psi(ref, cur)
    assert isinstance(psi, float)
