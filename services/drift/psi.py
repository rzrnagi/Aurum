import numpy as np


def compute_psi(reference: np.ndarray, current: np.ndarray, n_bins: int = 10) -> float:
    """
    Population Stability Index (PSI) between reference and current distributions.

    PSI < 0.1  : no significant change
    PSI < 0.2  : moderate change (warning)
    PSI >= 0.2 : significant change (alert)
    """
    # Bin edges derived from reference distribution (percentile-based)
    edges = np.percentile(reference, np.linspace(0, 100, n_bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf

    ref_counts, _ = np.histogram(reference, bins=edges)
    cur_counts, _ = np.histogram(current, bins=edges)

    # Avoid division by zero or log(0)
    ref_pct = (ref_counts / len(reference)) + 1e-8
    cur_pct = (cur_counts / len(current)) + 1e-8

    psi = float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))
    return psi
