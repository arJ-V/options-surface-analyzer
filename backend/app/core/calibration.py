import pandas as pd
import numpy as np
from scipy.optimize import minimize
from py_vollib_vectorized import vectorized_implied_volatility

def calculate_implied_volatility(df, underlying_price, risk_free_rate):
    """Calculates implied volatility for each option contract in the DataFrame."""

    df['T'] = (df['expiryDate'] - df['fetchDate']).dt.days / 365.0

    flags = df['type'].apply(lambda x: 'c' if x == 'call' else 'p').to_numpy()
    S = underlying_price
    K = df['strike'].to_numpy()
    t = df['T'].to_numpy()
    r = risk_free_rate
    prices = df['mid_price'].to_numpy()

    df['implied_volatility'] = vectorized_implied_volatility(
        prices, S, K, t, r, flags, return_as='numpy'
    )

    initial_count = len(df)
    df.dropna(subset=['implied_volatility'], inplace=True)
    df = df[(df['implied_volatility'] > 0.01) & (df['implied_volatility'] < 2.00)]

    return df

def svi_raw(k, params):
    """The raw SVI volatility formula."""
    a, b, rho, m, sigma = params
    if sigma < 0 or b < 0:
        return np.inf
    total_variance = a + b * (rho * (k - m) + np.sqrt((k - m)**2 + sigma**2))
    return total_variance

def svi_objective_function(params, market_data):
    """Calculates the squared error between SVI model variance and market variance."""
    k = market_data['log_moneyness'].values
    market_total_variance = (market_data['implied_volatility']**2 * market_data['T']).values

    model_total_variance = svi_raw(k, params)

    if np.any(model_total_variance < 0):
        return 1e9

    error = np.mean((model_total_variance - market_total_variance)**2)
    return error

def calibrate_svi_slice(market_data_slice):
    """Finds the best-fit SVI parameters for a single expiration date."""
    initial_guess = [0.1, 0.1, -0.5, 0.0, 0.2]
    bounds = ((-1, 1), (1e-3, 1), (-0.999, 0.999), (-1, 1), (1e-3, 1))

    result = minimize(
        svi_objective_function,
        initial_guess,
        args=(market_data_slice,),
        method='L-BFGS-B',
        bounds=bounds
    )

    if result.success:
        return result.x
    else:
        print(f"Warning: Optimization failed for expiry {market_data_slice['expiryDate'].iloc[0].date()}: {result.message}")
        return None

def calibrate_svi_parameters(master_df):
    calibrated_params = {}
    unique_expiries = master_df['expiryDate'].unique()

    for expiry in unique_expiries:
        market_slice = master_df[master_df['expiryDate'] == expiry]

        if len(market_slice) < 5:
            continue

        optimal_params = calibrate_svi_slice(market_slice)
        if optimal_params is not None:
            calibrated_params[expiry] = optimal_params

    return calibrated_params