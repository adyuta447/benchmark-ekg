import numpy as np

def summ(x, n_boot=2000, seed=0):
    """Median, IQR, dan interval kepercayaan 95% (bootstrap persentil) untuk median."""
    x = np.asarray(x, float); rng = np.random.default_rng(seed)
    meds = np.median(rng.choice(x, (n_boot, len(x))), axis=1)
    q1, q3 = np.percentile(x, [25, 75])
    return {"median": float(np.median(x)), "q1": float(q1), "q3": float(q3),
            "ci_lo": float(np.percentile(meds, 2.5)), "ci_hi": float(np.percentile(meds, 97.5)), "n": len(x)}
