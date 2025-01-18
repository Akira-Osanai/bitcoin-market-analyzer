import requests
import pandas as pd
from datetime import datetime
from .base_collector import BaseCollector

class OnchainDataCollector(BaseCollector):
    def get_large_holders_data(self):
        """bitcoin-dataからビットコインの大口保有者データを取得"""
        print("\n大口保有者データの取得を開始...")
        
        # 既存のデータを読み込む
        existing_df = self.load_existing_data('large_holders.csv')
        if existing_df is not None:
            print(f"既存データ: {len(existing_df)}行")
        
        url = 'https://bitcoin-data.com/v1/balance-addr-10K-BTC'
        headers = {'accept': 'application/hal+json'}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # データをDataFrameに変換
            dates = [datetime.strptime(item["d"], "%Y-%m-%d") for item in data]
            balances = [int(item["balAddr10Kbtc"]) for item in data]
            
            df = pd.DataFrame({
                'Total Holdings': balances
            }, index=dates)
            df.index.name = 'timestamp'
            
            # 1年分のデータにフィルタリング
            df = df[df.index >= self.start_date]
            df.sort_index(inplace=True)
            
            # 既存のデータとマージ
            if existing_df is not None:
                df = pd.concat([existing_df, df])
                df = df[~df.index.duplicated(keep='last')]
                df.sort_index(inplace=True)
            
            df.to_csv(f'{self.base_path}/large_holders.csv')
            print("✓ 大口保有者データを保存しました")
            return df
        except Exception as e:
            print(f"✗ 大口保有者データの取得に失敗: {str(e)}")
            return existing_df if existing_df is not None else None

    def get_active_addresses(self):
        """Blockchain.comからアクティブアドレス数を取得"""
        print("\nアクティブアドレス数の取得を開始...")
        url = "https://api.blockchain.info/charts/n-unique-addresses"
        params = {
            'timespan': '365days',
            'format': 'json'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()['values']
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['x'], unit='s')
            df['Active Addresses'] = df['y']
            df.set_index('timestamp', inplace=True)
            df = df[['Active Addresses']]
            
            # 1年分のデータにフィルタリング
            df = df[df.index >= self.start_date]
            df.sort_index(inplace=True)
            
            df.to_csv(f'{self.base_path}/active_addresses.csv')
            print("✓ アクティブアドレス数データを保存しました")
            return df
            
        except Exception as e:
            print(f"✗ アクティブアドレス数の取得に失敗: {str(e)}")
            return None

    def get_hash_rate(self):
        """Blockchain.comからハッシュレートを取得"""
        print("\nハッシュレートデータの取得を開始...")
        url = "https://api.blockchain.info/charts/hash-rate"
        params = {
            'timespan': '365days',
            'format': 'json'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()['values']
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['x'], unit='s')
            df['Hash Rate'] = df['y']
            df.set_index('timestamp', inplace=True)
            df = df[['Hash Rate']]
            
            # 1年分のデータにフィルタリング
            df = df[df.index >= self.start_date]
            df.sort_index(inplace=True)
            
            df.to_csv(f'{self.base_path}/hash_rate.csv')
            print("✓ ハッシュレートデータを保存しました")
            return df
            
        except Exception as e:
            print(f"✗ ハッシュレートの取得に失敗: {str(e)}")
            return None 