from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import pandas as pd
import numpy as np

from app.core.data_processing import get_processed_options_data
from app.core.calibration import calculate_implied_volatility, calibrate_svi_parameters, svi_raw
from app.core.arbitrage import find_arbitrage_signals
from app.core.simulation import simulate_butterfly_trades, simulate_calendar_trades

router = APIRouter()

@router.get("/surface/{ticker}")
async def get_volatility_surface(ticker: str, risk_free_rate: float = 0.05, num_expiries: int = 8):
    try:
        # 1. Fetch and Process Data
        master_df, underlying_price, risk_free_rate = get_processed_options_data(ticker.upper(), risk_free_rate, num_expiries)
        
        # 2. Calculate Implied Volatility
        iv_df = calculate_implied_volatility(master_df.copy(), underlying_price, risk_free_rate)
        
        if iv_df.empty:
            raise HTTPException(status_code=404, detail="No valid options data after IV calculation.")

        # 3. Calibrate SVI Parameters
        calibrated_params = calibrate_svi_parameters(iv_df)

        if not calibrated_params:
            raise HTTPException(status_code=404, detail="Could not calibrate SVI parameters for any expiry.")

        # 4. Detect Arbitrage
        butterfly_signals, calendar_signals = find_arbitrage_signals(calibrated_params, iv_df)

        # 5. Simulate Trades
        butterfly_trades = simulate_butterfly_trades(butterfly_signals, iv_df)
        calendar_trades = simulate_calendar_trades(calendar_signals, iv_df)

        # Prepare data for 3D surface plot
        log_moneyness_grid = np.linspace(iv_df['log_moneyness'].min(), iv_df['log_moneyness'].max(), 50)
        expiries_sorted = sorted(calibrated_params.keys())
        maturities_grid = np.array([(pd.to_datetime(d) - pd.to_datetime(master_df['fetchDate'].iloc[0])).days / 365.0 for d in expiries_sorted])

        X, Y = np.meshgrid(log_moneyness_grid, maturities_grid)
        Z = np.zeros_like(X)

        for i, expiry in enumerate(expiries_sorted):
            T = maturities_grid[i]
            params = calibrated_params[expiry]
            total_variance = svi_raw(X[i, :], params)
            Z[i, :] = np.sqrt(total_variance / T)
        
        # Convert numpy arrays to lists for JSON serialization
        surface_data = {
            "x": X.tolist(),
            "y": Y.tolist(),
            "z": Z.tolist()
        }

        return {
            "ticker": ticker.upper(),
            "underlying_price": underlying_price,
            "risk_free_rate": risk_free_rate,
            "surface_data": surface_data,
            "market_data_points": iv_df[['log_moneyness', 'T', 'implied_volatility']].to_dict(orient='records'),
            "butterfly_arbitrage_signals": butterfly_signals,
            "calendar_arbitrage_signals": calendar_signals,
            "profitable_butterfly_trades": butterfly_trades.to_dict(orient='records'),
            "profitable_calendar_trades": calendar_trades.to_dict(orient='records'),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))