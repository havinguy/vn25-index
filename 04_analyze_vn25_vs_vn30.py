"""
04_analyze_vn25_vs_vn30.py (Full 3-Year Rebased Chart)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from vnstock import stock_historical_data

PROJECT_DIR = Path(__file__).resolve().parent
VN25_CSV = PROJECT_DIR / "data" / "vn25_historical_index.csv"
OUTPUT_CHART = PROJECT_DIR / "vn25_vs_vn30_chart.png"

def calculate_metrics(series, name):
    daily_returns = series.pct_change().dropna()
    total_return = (series.iloc[-1] / series.iloc[0]) - 1
    days = (series.index[-1] - series.index[0]).days
    annualized_return = ((1 + total_return) ** (365.25 / days)) - 1
    
    volatility = daily_returns.std() * np.sqrt(252)
    
    rolling_max = series.cummax()
    drawdown = (series / rolling_max) - 1
    max_drawdown = drawdown.min()
    
    return {
        "Index": name,
        "Total Return": f"{total_return * 100:.2f}%",
        "Annualized Return": f"{annualized_return * 100:.2f}%",
        "Annualized Volatility": f"{volatility * 100:.2f}%",
        "Max Drawdown": f"{max_drawdown * 100:.2f}%"
    }

def main():
    print("Loading VN25 Synthetic Index data...")
    vn25_df = pd.read_csv(VN25_CSV)
    vn25_df['Date'] = pd.to_datetime(vn25_df['Date'])
    vn25_df.set_index('Date', inplace=True)
    
    start_date = vn25_df.index.min().strftime('%Y-%m-%d')
    end_date = vn25_df.index.max().strftime('%Y-%m-%d')
    
    print(f"Fetching real VN30 data from {start_date} to {end_date}...")
    try:
        vn30_df = stock_historical_data(symbol='VN30', 
                                        start_date=start_date, 
                                        end_date=end_date, 
                                        resolution="1D", 
                                        type="index")
        
        vn30_df.rename(columns={'time': 'Date', 'tradingDate': 'Date'}, inplace=True)
        vn30_df['Date'] = pd.to_datetime(vn30_df['Date'])
        vn30_df.set_index('Date', inplace=True)
        vn30_df = vn30_df[['close']].rename(columns={'close': 'VN30_Real'})
        
    except Exception as e:
        print(f"Failed to fetch VN30: {e}")
        return

    print("Aligning datasets and rebasing both to 1,000 on Day 1...")
    comparison_df = vn25_df[['VN25_Value']].join(vn30_df, how='inner')
    
    # REBASE BOTH TO 1000 AT START DATE
    base_vn25 = comparison_df['VN25_Value'].iloc[0]
    base_vn30 = comparison_df['VN30_Real'].iloc[0]
    
    comparison_df['VN25_Rebased'] = (comparison_df['VN25_Value'] / base_vn25) * 1000.0
    comparison_df['VN30_Rebased'] = (comparison_df['VN30_Real'] / base_vn30) * 1000.0

    print("\n--- PERFORMANCE METRICS ---")
    vn25_metrics = calculate_metrics(comparison_df['VN25_Rebased'], "VN25 (Synthetic)")
    vn30_metrics = calculate_metrics(comparison_df['VN30_Rebased'], "VN30 (Actual)")
    
    metrics_df = pd.DataFrame([vn25_metrics, vn30_metrics]).set_index("Index")
    print(metrics_df.to_string())

    print("\nGenerating Chart...")
    plt.figure(figsize=(14, 7))
    
    plt.plot(comparison_df.index, comparison_df['VN25_Rebased'], label='VN25 (Ex-Vingroup/Vietjet)', color='#1f77b4', linewidth=2)
    plt.plot(comparison_df.index, comparison_df['VN30_Rebased'], label='VN30 (Actual)', color='#ff7f0e', linewidth=2, linestyle='--')
    
    plt.title('VN25 Synthetic Index vs Actual VN30 (Full 3-Year History, Rebased to 1,000)', fontsize=14, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Index Value (Base = 1,000)', fontsize=12)
    plt.legend(fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    plt.savefig(OUTPUT_CHART, dpi=300)
    print(f"\n[SUCCESS] Updated chart saved to: {OUTPUT_CHART}")

if __name__ == "__main__":
    main()