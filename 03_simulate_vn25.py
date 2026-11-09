"""
03_simulate_vn25.py (FIXED)
"""
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

PROJECT_DIR = Path(__file__).resolve().parent
PRICES_DIR = PROJECT_DIR / "data" / "prices"
BASKET_CSV = PROJECT_DIR / "data" / "vn30_freefloat_history.csv"
OUTPUT_INDEX_CSV = PROJECT_DIR / "data" / "vn25_historical_index.csv"
OUTPUT_WEIGHTS_CSV = PROJECT_DIR / "data" / "vn25_daily_weights.csv"

EXCLUDED_TICKERS = ['VIC', 'VHM', 'VRE', 'VPL', 'VJC'] # Remove 'VJC' here to simulate VN26
BASE_VALUE = 1000.0
CAP_LIMIT = 0.10

def cap_weights(weights_series, cap=0.10):
    w = weights_series.copy()
    capped = pd.Series(False, index=w.index)
    
    while True:
        violators = w > cap
        new_violators = violators & ~capped
        
        if not new_violators.any():
            break
            
        capped = capped | violators
        w[capped] = cap
        
        uncapped_sum = w[~capped].sum()
        if uncapped_sum == 0:
            break
            
        remaining_weight = 1.0 - w[capped].sum()
        w[~capped] = (w[~capped] / uncapped_sum) * remaining_weight
        
    return w

def main():
    print("=== SCRIPT 3: Data Alignment ===")
    print("Loading VN30 quarterly history...")
    basket_df = pd.read_csv(BASKET_CSV)
    basket_df['rebalance_date'] = pd.to_datetime(basket_df['rebalance_date'])
    basket_df = basket_df.sort_values('rebalance_date')
    
    print("Loading daily OHLCV prices...")
    price_dfs = []
    for csv_file in PRICES_DIR.glob("*.csv"):
        df = pd.read_csv(csv_file)
        df['ticker'] = csv_file.stem
        price_dfs.append(df)
    
    prices_df = pd.concat(price_dfs, ignore_index=True)
    prices_df['Date'] = pd.to_datetime(prices_df['Date'])
    prices_df = prices_df.sort_values(['Date', 'ticker'])
    
    print("Aligning quarterly baskets to daily trading timeline...")
    trading_dates = pd.DataFrame({'Date': sorted(prices_df['Date'].unique())})
    
    rebalance_dates = sorted(basket_df['rebalance_date'].unique())
    rebalance_lookup = pd.DataFrame({
        'rebalance_date': rebalance_dates,
        'matched_rebalance': rebalance_dates
    })
    
    daily_timeline = pd.merge_asof(
        trading_dates,
        rebalance_lookup,
        left_on='Date',
        right_on='rebalance_date',
        direction='backward'
    )
    
    daily_timeline = daily_timeline.dropna(subset=['matched_rebalance'])
    
    daily_basket = pd.merge(
        daily_timeline[['Date', 'matched_rebalance']],
        basket_df,
        left_on='matched_rebalance',
        right_on='rebalance_date',
        how='inner'
    )
    daily_basket = daily_basket.drop(columns=['matched_rebalance', 'rebalance_date'])
    
    daily_master = pd.merge(daily_basket, prices_df, on=['Date', 'ticker'], how='inner')
    print(f"Total structured daily records generated: {len(daily_master)}")
    
    print("\n=== SCRIPT 4: The VN25 Purge ===")
    initial_count = len(daily_master)
    daily_master = daily_master[~daily_master['ticker'].isin(EXCLUDED_TICKERS)]
    purged_count = initial_count - len(daily_master)
    print(f"Purged {purged_count} daily records belonging to {EXCLUDED_TICKERS}")
    
    print("\n=== SCRIPT 5: The 10% Iterative Cap ===")
    daily_master['ff_mcap'] = daily_master['Close'] * daily_master['shares_for_index'] * (daily_master['free_float_pct'] / 100.0)
    
    print("Calculating daily weights and applying iterative capping algorithm...")
    daily_totals = daily_master.groupby('Date')['ff_mcap'].transform('sum')
    daily_master['raw_weight'] = daily_master['ff_mcap'] / daily_totals
    
    capped_weights = daily_master.groupby('Date')['raw_weight'].apply(cap_weights)
    daily_master['capped_weight'] = capped_weights.reset_index(level=0, drop=True)
    
    print("\n=== SCRIPT 6: Index Calculation ===")
    daily_master = daily_master.sort_values(['ticker', 'Date'])
    daily_master['stock_return'] = daily_master.groupby('ticker')['Close'].pct_change()
    daily_master['lagged_weight'] = daily_master.groupby('ticker')['capped_weight'].shift(1)
    
    calc_df = daily_master.dropna(subset=['stock_return', 'lagged_weight'])
    
    daily_index_returns = calc_df.groupby('Date').apply(
        lambda row: np.sum(row['lagged_weight'] * row['stock_return'])
    ).rename('index_return').reset_index()
    
    daily_index_returns['cumulative_return'] = (1 + daily_index_returns['index_return']).cumprod()
    daily_index_returns['VN25_Value'] = BASE_VALUE * daily_index_returns['cumulative_return']
    
    first_date = daily_master['Date'].min()
    base_row = pd.DataFrame({'Date': [first_date], 'index_return': [0.0], 'cumulative_return': [1.0], 'VN25_Value': [BASE_VALUE]})
    final_index = pd.concat([base_row, daily_index_returns], ignore_index=True).sort_values('Date')
    
    final_index.to_csv(OUTPUT_INDEX_CSV, index=False)
    weights_export = daily_master[['Date', 'ticker', 'raw_weight', 'capped_weight']].sort_values(['Date', 'capped_weight'], ascending=[True, False])
    weights_export.to_csv(OUTPUT_WEIGHTS_CSV, index=False)
    
    print("\n=== SUCCESS ===")
    print(f"Timeline starts at: {first_date.strftime('%Y-%m-%d')}")
    print(f"Timeline ends at: {final_index['Date'].iloc[-1].strftime('%Y-%m-%d')}")
    print(f"Base Index Value: {BASE_VALUE:.2f}")
    print(f"Final Index Value: {final_index['VN25_Value'].iloc[-1]:.2f}")

if __name__ == "__main__":
    main()