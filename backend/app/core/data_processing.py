import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

def fetch_option_chain(ticker_obj, expiry_date):
    """Fetches the call and put option chain for a given expiry and combines them."""
    opt_chain = ticker_obj.option_chain(expiry_date)

    calls = opt_chain.calls
    calls['type'] = 'call'
    puts = opt_chain.puts
    puts['type'] = 'put'

    chain = pd.concat([calls, puts], ignore_index=True)

    chain['expiryDate'] = pd.to_datetime(expiry_date)
    chain['fetchDate'] = pd.to_datetime(datetime.now().date())

    return chain

def filter_options_data(df, underlying_price):
    """Applies liquidity and moneyness filters to the options DataFrame."""

    for col in ['bid', 'ask', 'strike', 'volume', 'openInterest']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df.dropna(subset=['bid', 'ask', 'strike', 'volume', 'openInterest'], inplace=True)

    df['mid_price'] = (df['bid'] + df['ask']) / 2
    df['spread_abs'] = df['ask'] - df['bid']
    df['spread_rel'] = df['spread_abs'] / df['mid_price']

    df = df[df['bid'] > 0]

    oi_threshold = 50
    volume_threshold = 10
    df = df[(df['openInterest'] >= oi_threshold) & (df['volume'] >= volume_threshold)]

    spread_threshold = 0.4
    df = df[df['spread_rel'] < spread_threshold]

    moneyness_lower_bound = 0.85
    moneyness_upper_bound = 1.15
    df = df[(df['strike'] > underlying_price * moneyness_lower_bound) & (df['strike'] < underlying_price * moneyness_upper_bound)]

    return df

def get_processed_options_data(ticker: str, risk_free_rate: float, num_expiries_to_fetch: int = 8):
    stock = yf.Ticker(ticker)
    underlying_price = stock.history(period='1d')['Close'].iloc[0]
    expirations = stock.options

    all_options_data = []

    for expiry in expirations[:num_expiries_to_fetch]:
        try:
            raw_chain = fetch_option_chain(stock, expiry)
            filtered_chain = filter_options_data(raw_chain.copy(), underlying_price)
            all_options_data.append(filtered_chain)
        except Exception as e:
            print(f"Could not process expiry {expiry}: {e}")

    if not all_options_data:
        raise Exception("No valid options data could be fetched. Please check market hours or ticker.")

    master_df = pd.concat(all_options_data, ignore_index=True)
    master_df['log_moneyness'] = np.log(master_df['strike'] / underlying_price)

    return master_df, underlying_price, risk_free_rate