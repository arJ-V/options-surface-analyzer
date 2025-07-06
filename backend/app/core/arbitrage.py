import numpy as np
import pandas as pd
from backend.app.core.calibration import svi_raw

def svi_derivatives(k, params):
    """Calculates SVI total variance w, and its first (w') and second (w'') derivatives."""
    a, b, rho, m, sigma = params

    sqrt_term = np.sqrt((k - m)**2 + sigma**2)

    w = a + b * (rho * (k - m) + sqrt_term)

    w_prime = b * (rho + (k - m) / sqrt_term)

    w_double_prime = b * (sigma**2 / sqrt_term**3)

    return w, w_prime, w_double_prime

def check_butterfly_arbitrage(k, params):
    """Calculates the g(k) function to test for butterfly arbitrage."""
    w, w_prime, w_double_prime = svi_derivatives(k, params)

    w = np.maximum(w, 1e-10)

    term1 = (1 - k * w_prime / (2 * w))**2
    term2 = (w_prime**2 / 4) * (1 / w + 0.25)
    term3 = w_double_prime / 2

    g = term1 - term2 + term3
    return g

def find_arbitrage_signals(calibrated_params, master_df):
    butterfly_signals = []
    calendar_signals = []
    log_moneyness_range = np.linspace(-0.2, 0.2, 200)

    for expiry, params in calibrated_params.items():
        g_values = check_butterfly_arbitrage(log_moneyness_range, params)
        arbitrage_regions = log_moneyness_range[g_values < 0]
        if len(arbitrage_regions) > 0:
            k_min, k_max = arbitrage_regions.min(), arbitrage_regions.max()
            butterfly_signals.append({'expiry': expiry, 'k_min': k_min, 'k_max': k_max})

    sorted_expiries = sorted(calibrated_params.keys())
    for i in range(len(sorted_expiries) - 1):
        expiry1, expiry2 = sorted_expiries[i], sorted_expiries[i+1]
        params1, params2 = calibrated_params[expiry1], calibrated_params[expiry2]
        T1 = master_df[master_df['expiryDate'] == expiry1]['T'].iloc[0]
        T2 = master_df[master_df['expiryDate'] == expiry2]['T'].iloc[0]

        w1_curve = svi_raw(log_moneyness_range, params1)
        w2_curve = svi_raw(log_moneyness_range, params2)

        if np.any(w2_curve < w1_curve):
            arbitrage_indices = np.where(w2_curve < w1_curve)
            k_min, k_max = log_moneyness_range[arbitrage_indices].min(), log_moneyness_range[arbitrage_indices].max()
            calendar_signals.append({'expiry1': expiry1, 'expiry2': expiry2, 'k_min': k_min, 'k_max': k_max})

    return butterfly_signals, calendar_signals