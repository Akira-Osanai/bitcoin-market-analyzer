import requests
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from datetime import datetime

# Function to get balance data from API
def get_btc_balance_data():
    url = 'https://bitcoin-data.com/v1/balance-addr-10K-BTC'
    headers = {'accept': 'application/hal+json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching BTC data: {response.status_code}")
        return []

# Function to get BTCUSD data from Yahoo Finance
def get_btcusd_data(start_date, end_date):
    ticker = "BTC-USD"
    btc_data = yf.download(ticker, start=start_date, end=end_date)
    return btc_data

# Function to get DOGEUSD data from Yahoo Finance
def get_dogeusd_data(start_date, end_date):
    ticker = "DOGE-USD"
    doge_data = yf.download(ticker, start=start_date, end=end_date)
    return doge_data

# Function to get XMRUSD data from Yahoo Finance
def get_xmrusd_data(start_date, end_date):
    ticker = "XMR-USD"
    xmr_data = yf.download(ticker, start=start_date, end=end_date)
    return xmr_data

# Plot all charts in a single figure with subplots
def plot_combined_charts(btc_data, btcusd_data, doge_data, xmr_data):
    # Create a figure with 4 subplots
    fig, axs = plt.subplots(4, 1, figsize=(10, 18))

    # Plot BTC 10K+ Addresses
    dates = [datetime.strptime(item["d"], "%Y-%m-%d") for item in btc_data]
    balances = [int(item["balAddr10Kbtc"]) for item in btc_data]
    axs[0].plot(dates, balances, label="BTC 10K+ Addresses", color='blue')
    axs[0].set_title("Number of BTC Addresses Holding 10K+ BTC")
    axs[0].set_xlabel("Date")
    axs[0].set_ylabel("Number of Addresses")
    axs[0].grid(True)
    axs[0].legend()

    # Plot BTCUSD (Normalized to thousands)
    axs[1].plot(btcusd_data.index, btcusd_data['Close'] / 1000, label="BTCUSD (in thousands)", color='orange')
    axs[1].set_title("BTCUSD Price Over Time (Normalized)")
    axs[1].set_xlabel("Date")
    axs[1].set_ylabel("Price (in thousands USD)")
    axs[1].grid(True)
    axs[1].legend()

    # Plot DOGEUSD
    axs[2].plot(doge_data.index, doge_data['Close'], label="DOGEUSD", color='green')
    axs[2].set_title("DOGEUSD Price Over Time")
    axs[2].set_xlabel("Date")
    axs[2].set_ylabel("Price (USD)")
    axs[2].grid(True)
    axs[2].legend()

    # Plot XMRUSD
    axs[3].plot(xmr_data.index, xmr_data['Close'], label="XMRUSD", color='purple')
    axs[3].set_title("XMRUSD Price Over Time")
    axs[3].set_xlabel("Date")
    axs[3].set_ylabel("Price (USD)")
    axs[3].grid(True)
    axs[3].legend()

    # Adjust layout and save the plot
    plt.tight_layout()
    plt.savefig('crypto_analysis.png')
    print("グラフを'crypto_analysis.png'として保存しました。")

def main():
    print("暗号通貨データの取得を開始します...")
    btc_data = get_btc_balance_data()

    if btc_data:
        # Get the start and end dates from the BTC data
        start_date = min([item["d"] for item in btc_data])
        end_date = max([item["d"] for item in btc_data])

        print(f"データ期間: {start_date} から {end_date}")
        print("Yahoo Financeからデータを取得中...")

        # Get BTCUSD, DOGEUSD, and XMRUSD data from Yahoo Finance
        btcusd_data = get_btcusd_data(start_date, end_date)
        doge_data = get_dogeusd_data(start_date, end_date)
        xmr_data = get_xmrusd_data(start_date, end_date)

        # Plot combined charts
        if not btcusd_data.empty and not doge_data.empty and not xmr_data.empty:
            print("グラフを生成中...")
            plot_combined_charts(btc_data, btcusd_data, doge_data, xmr_data)
        else:
            print("エラー: 一つ以上のデータセットが空です。")
    else:
        print("BTCデータの取得に失敗しました。")

if __name__ == "__main__":
    main() 