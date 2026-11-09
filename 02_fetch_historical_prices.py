"""
02_fetch_historical_prices.py (Deep History Version)
"""
import os
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

try:
    from vnstock import stock_historical_data
except ImportError:
    raise SystemExit(
        "Missing dependency. Run:\n"
        "  pip install vnstock pandas --break-system-packages"
    )

PROJECT_DIR = Path(__file__).resolve().parent
IN_CSV = PROJECT_DIR / "data" / "vn30_freefloat_history.csv"
OUT_DIR = PROJECT_DIR / "data" / "prices"

# 3-Year Lookback Window
START_DATE = "2023-01-01"
END_DATE = datetime.today().strftime('%Y-%m-%d')

def get_unique_tickers() -> list:
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Cannot find {IN_CSV}. Run Script 1 first.")
    
    df = pd.read_csv(IN_CSV)
    unique_tickers = sorted(df['ticker'].dropna().unique().tolist())
    print(f"Found {len(unique_tickers)} unique tickers across the 3-year history.")
    return unique_tickers

def fetch_all_tickers():
    tickers = get_unique_tickers()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] Fetching {ticker}...")
        try:
            # Using the older, unrestricted API function
            df = stock_historical_data(symbol=ticker, 
                                       start_date=START_DATE, 
                                       end_date=END_DATE, 
                                       resolution="1D", 
                                       type="stock")
            
            col_mapping = {
                'time': 'Date', 'tradingDate': 'Date', 'date': 'Date',
                'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close',
                'volume': 'Volume'
            }
            df.rename(columns=col_mapping, inplace=True)
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
                cols_to_keep = [c for c in ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'] if c in df.columns]
                df = df[cols_to_keep]
                
            out_file = OUT_DIR / f"{ticker}.csv"
            df.to_csv(out_file, index=False)
            
        except Exception as e:
            print(f"  [!] Failed to fetch {ticker}: {e}")
            failed.append(ticker)
            
    print(f"\nDone. Saved {len(tickers) - len(failed)} files to {OUT_DIR}")
    if failed:
        print(f"Failed tickers: {failed}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Fetch data for all tickers.")
    args = parser.parse_args()
    
    if args.full:
        fetch_all_tickers()
    else:
        print("Please specify an action: run 'python3.14 02_fetch_historical_prices.py --full'")