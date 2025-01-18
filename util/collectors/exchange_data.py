import requests
import pandas as pd
import yfinance as yf
import time
from datetime import timedelta
from .base_collector import BaseCollector

class ExchangeDataCollector(BaseCollector):
    def get_trading_volume(self):
        """Yahoo FinanceからBTCUSD取引量を取得"""
        print("\n取引量データの取得を開始...")
        try:
            df = yf.download("BTC-USD", start=self.start_date, end=self.end_date)
            if df.empty:
                return None
                
            volume_df = df[['Volume']].copy()
            volume_df.columns = ['Trading Volume']
            volume_df.to_csv(f'{self.base_path}/trading_volume.csv')
            print("✓ 取引量データを保存しました")
            return volume_df
            
        except Exception as e:
            print(f"✗ 取引量データの取得に失敗: {str(e)}")
            return None

    def get_coinbase_premium(self):
        """コインベースプレミアムデータを取得します。
        コインベースとBinanceの価格差からプレミアムを計算します。
        """
        print("\nコインベースプレミアムデータの取得を開始...")
        
        # 既存のデータを読み込む
        existing_df = self.load_existing_data('coinbase_premium.csv')
        if existing_df is not None:
            print(f"既存データ: {len(existing_df)}行")
            missing_ranges = self.get_missing_date_ranges(existing_df)
        else:
            missing_ranges = [(self.start_date, self.end_date)]
        
        if not missing_ranges:
            print("✓ 新規データなし - 既存データを使用")
            return existing_df

        try:
            new_data = []
            for start_date, end_date in missing_ranges:
                current_date = start_date
                while current_date <= end_date:
                    # 休場日をスキップ
                    if not self.is_market_open(current_date):
                        print(f"✓ {current_date.date()} は休場日のためスキップします")
                        current_date += timedelta(days=1)
                        continue

                    try:
                        # Coinbaseのデータ取得
                        cb_url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
                        response = requests.get(cb_url)
                        if response.status_code == 200:
                            cb_data = response.json()
                            cb_price = float(cb_data['data']['amount'])
                        else:
                            print(f"✗ {current_date.date()}のCoinbaseデータの取得に失敗: {response.status_code}")
                            current_date += timedelta(days=1)
                            continue

                        # Binanceのデータ取得
                        binance_url = "https://api.binance.com/api/v3/ticker/price"
                        params = {'symbol': 'BTCUSDT'}
                        response = requests.get(binance_url, params=params)
                        if response.status_code == 200:
                            binance_data = response.json()
                            binance_price = float(binance_data['price'])
                        else:
                            print(f"✗ {current_date.date()}のBinanceデータの取得に失敗: {response.status_code}")
                            current_date += timedelta(days=1)
                            continue

                        # プレミアムの計算（パーセンテージ）
                        premium = ((cb_price - binance_price) / binance_price) * 100

                        # 日付を00:00:00に設定
                        timestamp = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        new_data.append({
                            'timestamp': timestamp,
                            'Coinbase Premium': premium
                        })

                        print(f"✓ {current_date.date()}のコインベースプレミアム: {premium:.2f}%")
                        time.sleep(1)  # API制限を考慮

                    except Exception as e:
                        print(f"✗ {current_date.date()}のデータ取得中にエラーが発生: {e}")

                    current_date += timedelta(days=1)

            if new_data:
                new_df = pd.DataFrame(new_data)
                new_df.set_index('timestamp', inplace=True)
                
                # 既存のデータとマージ
                if existing_df is not None:
                    df = pd.concat([existing_df, new_df])
                    df = df[~df.index.duplicated(keep='last')]
                else:
                    df = new_df
                
                df.sort_index(inplace=True)
                
                # CSVに保存
                df.to_csv(f'{self.base_path}/coinbase_premium.csv')
                print("✓ コインベースプレミアムデータを保存しました")
                return df
            elif existing_df is not None:
                print("✓ 新規データなし - 既存データを使用")
                return existing_df
            else:
                print("✗ データが取得できませんでした")
                return None
            
        except Exception as e:
            print(f"✗ コインベースプレミアムデータの取得に失敗: {str(e)}")
            return existing_df if existing_df is not None else None 