import requests
import pandas as pd
import time
from datetime import timedelta
from .base_collector import BaseCollector

class DerivativeDataCollector(BaseCollector):
    def get_funding_rates(self):
        """Binanceの先物ファンディングレートを取得"""
        url = "https://fapi.binance.com/fapi/v1/fundingRate"
        
        print("\nファンディングレートデータの取得を開始...")
        try:
            all_data = []
            start_time = int(self.start_date.timestamp() * 1000)
            end_time = int(self.end_date.timestamp() * 1000)
            request_count = 0
            
            while start_time < end_time:
                request_count += 1
                print(f"\r取得リクエスト数: {request_count}", end='', flush=True)
                
                params = {
                    'symbol': 'BTCUSDT',
                    'limit': 1000,
                    'startTime': start_time,
                    'endTime': end_time
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    break
                
                all_data.extend(data)
                start_time = int(data[-1]['fundingTime']) + 1
                time.sleep(1)
            
            print("\n✓ データ取得完了")
            
            if not all_data:
                print("✗ ファンディングレートデータが空です")
                return None
            
            df = pd.DataFrame(all_data)
            df['timestamp'] = pd.to_datetime(df['fundingTime'], unit='ms')
            df['Funding Rate'] = pd.to_numeric(df['fundingRate'], errors='coerce') * 100
            df.set_index('timestamp', inplace=True)
            df = df[['Funding Rate']]
            df.sort_index(inplace=True)
            
            df.to_csv(f'{self.base_path}/funding_rates.csv')
            print("✓ ファンディングレートデータを保存しました")
            return df
        except Exception as e:
            print(f"\n✗ ファンディングレートの取得に失敗: {str(e)}")
            return None

    def get_open_interest(self):
        """Binanceからオープンインタレストデータを取得"""
        print("\nオープンインタレストデータの取得を開始...")
        
        # 既存のデータを読み込む
        existing_df = self.load_existing_data('open_interest.csv')
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
            request_count = 0
            
            for start_date, end_date in missing_ranges:
                current_date = start_date
                while current_date <= end_date:
                    request_count += 1
                    print(f"\r取得リクエスト数: {request_count}", end='', flush=True)
                    
                    # 休場日をスキップ
                    if not self.is_market_open(current_date):
                        print(f"\n✓ {current_date.date()} は休場日のためスキップします")
                        current_date += timedelta(days=1)
                        continue
                    
                    params = {
                        'symbol': 'BTCUSDT'
                    }
                    
                    try:
                        response = requests.get("https://fapi.binance.com/fapi/v1/openInterest", params=params)
                        response.raise_for_status()
                        data = response.json()
                        
                        if data:
                            # 日付を00:00:00に設定
                            timestamp = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
                            new_data.append({
                                'timestamp': timestamp,
                                'Open Interest': float(data['openInterest'])
                            })
                        
                        time.sleep(1)  # API制限を考慮
                    
                    except Exception as e:
                        print(f"\n✗ {current_date.date()}のデータ取得中にエラー: {str(e)}")
                    
                    current_date += timedelta(days=1)
            
            print("\n✓ データ取得完了")
            
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
                df.to_csv(f'{self.base_path}/open_interest.csv')
                print("✓ オープンインタレストデータを保存しました")
                return df
            elif existing_df is not None:
                print("✓ 新規データなし - 既存データを使用")
                return existing_df
            else:
                print("✗ データが取得できませんでした")
                return None
            
        except Exception as e:
            print(f"\n✗ オープンインタレストデータの取得に失敗: {str(e)}")
            return existing_df if existing_df is not None else None 