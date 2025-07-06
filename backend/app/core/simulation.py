import pandas as pd

def simulate_butterfly_trades(signals, df):
    profitable_trades = []

    for signal in signals:
        expiry = signal['expiry']
        k_min, k_max = signal['k_min'], signal['k_max']

        slice_df = df[(df['expiryDate'] == expiry) & (df['type'] == 'call')].sort_values('strike').reset_index(drop=True)

        for i in range(len(slice_df) - 2):
            opt1, opt2, opt3 = slice_df.iloc[i], slice_df.iloc[i+1], slice_df.iloc[i+2]

            if k_min <= opt2['log_moneyness'] <= k_max:
                c1_ask = opt1['ask']
                c2_bid = opt2['bid']
                c3_ask = opt3['ask']

                initial_profit = (2 * c2_bid) - c1_ask - c3_ask

                if initial_profit > 0:
                    trade_details = {
                        'type': 'Butterfly Spread',
                        'expiry': expiry.date(),
                        'strikes': f"{opt1['strike']}/{opt2['strike']}/{opt3['strike']}",
                        'actions': f"BUY C@{opt1['strike']} @{c1_ask}, SELL 2x C@{opt2['strike']} @{c2_bid}, BUY C@{opt3['strike']} @{c3_ask}",
                        'initial_profit_per_spread': f"${initial_profit:.4f}"
                    }
                    profitable_trades.append(trade_details)

    return pd.DataFrame(profitable_trades) if profitable_trades else pd.DataFrame()

def simulate_calendar_trades(signals, df):
    profitable_trades = []

    for signal in signals:
        exp1, exp2 = signal['expiry1'], signal['expiry2']
        k_min, k_max = signal['k_min'], signal['k_max']

        slice1 = df[(df['expiryDate'] == exp1) & (df['type'] == 'call')]
        slice2 = df[(df['expiryDate'] == exp2) & (df['type'] == 'call')]

        common_strikes = pd.merge(slice1, slice2, on='strike', suffixes=('_T1', '_T2'))

        for _, row in common_strikes.iterrows():
            if k_min <= row['log_moneyness_T1'] <= k_max:
                c1_bid = row['bid_T1']
                c2_ask = row['ask_T2']
                strike = row['strike']

                initial_profit = c1_bid - c2_ask

                if initial_profit > 0:
                    trade_details = {
                        'type': 'Calendar Spread',
                        'expiries': f"{exp1.date()} / {exp2.date()}",
                        'strike': strike,
                        'actions': f"SELL C@{strike} (exp {exp1.date()}) @{c1_bid}, BUY C@{strike} (exp {exp2.date()}) @{c2_ask}",
                        'initial_credit_per_spread': f"${initial_profit:.4f}"
                    }
                    profitable_trades.append(trade_details)

    return pd.DataFrame(profitable_trades) if profitable_trades else pd.DataFrame()