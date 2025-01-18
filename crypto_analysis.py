import requests
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import os
import seaborn as sns
import matplotlib.gridspec as gridspec
import pandas_market_calendars as mcal
from pytrends.request import TrendReq

class DataCollector:
    def __init__(self):
        self.base_path = 'market_data'
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        # 1年間のデータ取得用の日付設定
        self.end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.start_date = (self.end_date - relativedelta(years=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        # NYSE（ニューヨーク証券取引所）のカレンダーを取得
        self.nyse = mcal.get_calendar('NYSE')
        # PyTrendsの初期化
        self.pytrends = TrendReq(hl='en-US', tz=360)
        print(f"データ収集期間: {self.start_date} から {self.end_date}")

    def load_existing_data(self, filename):
        """既存のCSVファイルからデータを読み込む"""
        filepath = os.path.join(self.base_path, filename)
        if os.path.exists(filepath):
            try:
                df = pd.read_csv(filepath, index_col='timestamp', parse_dates=True)
                df.sort_index(inplace=True)
                return df
            except Exception as e:
                print(f"既存データの読み込みに失敗: {str(e)}")
        return None

    def get_missing_date_ranges(self, existing_df):
        """不足している日付範囲を取得"""
        if existing_df is None or existing_df.empty:
            return [(self.start_date, self.end_date)]

        date_ranges = []
        current_date = self.start_date

        # 開始日から最初のデータまでの期間
        if existing_df.index[0] > self.start_date:
            date_ranges.append((self.start_date, existing_df.index[0]))

        # データの間の欠損期間
        for i in range(len(existing_df.index) - 1):
            current = existing_df.index[i]
            next_date = existing_df.index[i + 1]
            if (next_date - current).days > 1:
                date_ranges.append((current + timedelta(days=1), next_date - timedelta(days=1)))

        # 最後のデータから終了日までの期間
        if existing_df.index[-1] < self.end_date:
            date_ranges.append((existing_df.index[-1] + timedelta(days=1), self.end_date))

        return date_ranges

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

    def get_btcusd_data(self):
        """Yahoo FinanceからBTCUSDデータを取得"""
        print("\nBTCUSDデータの取得を開始...")
        
        # 既存のデータを読み込む
        existing_df = self.load_existing_data('btcusd.csv')
        if existing_df is not None:
            print(f"既存データ: {len(existing_df)}行")
            missing_ranges = self.get_missing_date_ranges(existing_df)
        else:
            missing_ranges = [(self.start_date, self.end_date)]
        
        try:
            new_data = []
            for start, end in missing_ranges:
                print(f"データ取得期間: {start} から {end}")
                ticker = "BTC-USD"
                # end_dateに1日を加算して終了日を含める
                df = yf.download(ticker, start=start, end=end + relativedelta(days=1))
                if not df.empty:
                    new_data.append(df[['Close']].copy())
            
            if new_data:
                new_df = pd.concat(new_data)
                new_df.columns = ['BTCUSD Price']
                new_df.index.name = 'timestamp'
                
                # 既存のデータとマージ
                if existing_df is not None:
                    df = pd.concat([existing_df, new_df])
                    df = df[~df.index.duplicated(keep='last')]
                else:
                    df = new_df
                
                df.sort_index(inplace=True)
                df.to_csv(f'{self.base_path}/btcusd.csv')
                print("✓ BTCUSDデータを保存しました")
                return df
            elif existing_df is not None:
                print("✓ 新規データなし - 既存データを使用")
                return existing_df
            else:
                print("✗ データが取得できませんでした")
                return None
        except Exception as e:
            print(f"✗ BTCUSDデータの取得に失敗: {str(e)}")
            return existing_df if existing_df is not None else None

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

    def get_fear_greed_index(self):
        """Fear & Greed Indexを取得"""
        url = "https://api.alternative.me/fng/"
        params = {
            'limit': 365,
            'format': 'json'
        }
        
        print("\nFear & Greed Indexの取得を開始...")
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()['data']
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='s')
            df['Fear & Greed Value'] = pd.to_numeric(df['value'], errors='coerce')
            df.set_index('timestamp', inplace=True)
            df = df[['Fear & Greed Value']]
            df.sort_index(inplace=True)
            
            # 1年分のデータに制限
            df = df[df.index >= self.start_date]
            
            df.to_csv(f'{self.base_path}/fear_greed.csv')
            print("✓ Fear & Greed Indexデータを保存しました")
            return df
        except Exception as e:
            print(f"✗ Fear & Greed Indexの取得に失敗: {str(e)}")
            return None

    def get_open_interest(self):
        """Binanceからオープンインタレストデータを取得"""
        print("\nオープンインタレストデータの取得を開始...")
        url = "https://fapi.binance.com/fapi/v1/openInterest"
        
        # 既存のデータを読み込む
        existing_df = self.load_existing_data('open_interest.csv')
        if existing_df is not None:
            print(f"既存データ: {len(existing_df)}行")
            missing_ranges = self.get_missing_date_ranges(existing_df)
        else:
            missing_ranges = [(self.start_date, self.end_date)]
            
        try:
            all_data = []
            request_count = 0
            
            for start_date, end_date in missing_ranges:
                current_date = start_date
                while current_date <= end_date:
                    request_count += 1
                    print(f"\r取得リクエスト数: {request_count}", end='', flush=True)
                    
                    params = {
                        'symbol': 'BTCUSDT'
                    }
                    
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data:
                        # 日付を00:00:00に設定
                        timestamp = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        all_data.append({
                            'timestamp': timestamp,
                            'Open Interest': float(data['openInterest'])
                        })
                    
                    current_date = current_date + timedelta(days=1)
                    time.sleep(1)  # API制限を考慮
            
            print("\n✓ データ取得完了")
            
            if not all_data:
                if existing_df is not None:
                    print("✓ 新規データなし - 既存データを使用")
                    return existing_df
                print("✗ オープンインタレストデータが空です")
                return None
                
            df = pd.DataFrame(all_data)
            df.set_index('timestamp', inplace=True)
            df = df[['Open Interest']]
            
            # 既存のデータとマージ
            if existing_df is not None:
                df = pd.concat([existing_df, df])
                df = df[~df.index.duplicated(keep='last')]
            
            df.sort_index(inplace=True)
            df.to_csv(f'{self.base_path}/open_interest.csv')
            print("✓ オープンインタレストデータを保存しました")
            return df
            
        except Exception as e:
            print(f"✗ オープンインタレストデータの取得に失敗: {str(e)}")
            return existing_df if existing_df is not None else None

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

    def get_dxy_data(self):
        """Yahoo FinanceからDXY（米ドル指数）データを取得"""
        print("\nDXYデータの取得を開始...")
        
        # 既存のデータを読み込む
        existing_df = self.load_existing_data('dxy.csv')
        if existing_df is not None:
            print(f"既存データ: {len(existing_df)}行")
            missing_ranges = self.get_missing_date_ranges(existing_df)
        else:
            missing_ranges = [(self.start_date, self.end_date)]
        
        try:
            new_data = []
            for start, end in missing_ranges:
                # 土日または祝日をスキップ
                if start.weekday() >= 5 or end.weekday() >= 5 or not self.is_market_open(start) or not self.is_market_open(end):
                    print(f"✓ {start} から {end} は休場日のためスキップします")
                    continue
                    
                print(f"データ取得期間: {start} から {end}")
                ticker = "DX-Y.NYB"
                try:
                    df = yf.download(ticker, start=start, end=end + relativedelta(days=1))
                    if not df.empty:
                        df_close = df[['Close']].copy()
                        df_close.columns = ['DXY Price']
                        new_data.append(df_close)
                    else:
                        print(f"✓ {start} から {end} の期間にデータがないためスキップします")
                except Exception as e:
                    if "No price data found" in str(e):
                        print(f"✓ {start} から {end} の期間は取引なしのためスキップします")
                    else:
                        print(f"✓ {start} から {end} の期間のデータ取得をスキップ: {str(e)}")
            
            if new_data:
                new_df = pd.concat(new_data)
                new_df.index.name = 'timestamp'
                
                # 既存のデータとマージ
                if existing_df is not None:
                    df = pd.concat([existing_df, new_df])
                    df = df[~df.index.duplicated(keep='last')]
                else:
                    df = new_df
                
                df.sort_index(inplace=True)
                df.to_csv(f'{self.base_path}/dxy.csv')
                print("✓ DXYデータを保存しました")
                return df
            elif existing_df is not None:
                print("✓ 新規データなし - 既存データを使用")
                return existing_df
            else:
                print("✗ データが取得できませんでした")
                return None
        except Exception as e:
            print(f"✗ DXYデータの取得に失敗: {str(e)}")
            return existing_df if existing_df is not None else None

    def get_sp500_data(self):
        """Yahoo FinanceからS&P500データを取得"""
        print("\nS&P500データの取得を開始...")
        
        # 既存のデータを読み込む
        existing_df = self.load_existing_data('sp500.csv')
        if existing_df is not None:
            print(f"既存データ: {len(existing_df)}行")
            missing_ranges = self.get_missing_date_ranges(existing_df)
        else:
            missing_ranges = [(self.start_date, self.end_date)]
        
        try:
            new_data = []
            for start, end in missing_ranges:
                # 土日または祝日をスキップ
                if start.weekday() >= 5 or end.weekday() >= 5 or not self.is_market_open(start) or not self.is_market_open(end):
                    print(f"✓ {start} から {end} は休場日のためスキップします")
                    continue
                    
                print(f"データ取得期間: {start} から {end}")
                ticker = "^GSPC"
                try:
                    df = yf.download(ticker, start=start, end=end + relativedelta(days=1))
                    if not df.empty:
                        df_close = df[['Close']].copy()
                        df_close.columns = ['SP500 Price']
                        new_data.append(df_close)
                    else:
                        print(f"✓ {start} から {end} の期間にデータがないためスキップします")
                except Exception as e:
                    if "No price data found" in str(e):
                        print(f"✓ {start} から {end} の期間は取引なしのためスキップします")
                    else:
                        print(f"✓ {start} から {end} の期間のデータ取得をスキップ: {str(e)}")
            
            if new_data:
                new_df = pd.concat(new_data)
                new_df.index.name = 'timestamp'
                
                # 既存のデータとマージ
                if existing_df is not None:
                    df = pd.concat([existing_df, new_df])
                    df = df[~df.index.duplicated(keep='last')]
                else:
                    df = new_df
                
                df.sort_index(inplace=True)
                df.to_csv(f'{self.base_path}/sp500.csv')
                print("✓ S&P500データを保存しました")
                return df
            elif existing_df is not None:
                print("✓ 新規データなし - 既存データを使用")
                return existing_df
            else:
                print("✗ データが取得できませんでした")
                return None
        except Exception as e:
            print(f"✗ S&P500データの取得に失敗: {str(e)}")
            return existing_df if existing_df is not None else None

    def get_gold_data(self):
        """Yahoo Financeから金価格データを取得"""
        print("\n金価格データの取得を開始...")
        
        # 既存のデータを読み込む
        existing_df = self.load_existing_data('gold.csv')
        if existing_df is not None:
            print(f"既存データ: {len(existing_df)}行")
            missing_ranges = self.get_missing_date_ranges(existing_df)
        else:
            missing_ranges = [(self.start_date, self.end_date)]
        
        try:
            new_data = []
            for start, end in missing_ranges:
                # 日付範囲を1日単位で処理
                current_date = start
                while current_date <= end:
                    # 土日または祝日をスキップ
                    if current_date.weekday() >= 5 or not self.is_market_open(current_date):
                        print(f"✓ {current_date.strftime('%Y-%m-%d')} は休場日のためスキップします")
                        current_date += timedelta(days=1)
                        continue
                    
                    next_date = current_date + timedelta(days=1)
                    print(f"データ取得期間: {current_date.strftime('%Y-%m-%d')}")
                    
                    try:
                        df = yf.download("GLD", start=current_date, end=next_date)
                        if not df.empty:
                            df_close = df[['Close']].copy()
                            df_close.columns = ['Gold Price']
                            new_data.append(df_close)
                        else:
                            print(f"✓ {current_date.strftime('%Y-%m-%d')} の期間にデータがないためスキップします")
                    except Exception as e:
                        if "No price data found" in str(e):
                            print(f"✓ {current_date.strftime('%Y-%m-%d')} の期間は取引なしのためスキップします")
                        else:
                            print(f"✓ {current_date.strftime('%Y-%m-%d')} の期間のデータ取得をスキップ: {str(e)}")
                    
                    current_date = next_date
            
            if new_data:
                new_df = pd.concat(new_data)
                new_df.index.name = 'timestamp'
                
                # 既存のデータとマージ
                if existing_df is not None:
                    df = pd.concat([existing_df, new_df])
                    df = df[~df.index.duplicated(keep='last')]
                else:
                    df = new_df
                
                df.sort_index(inplace=True)
                df.to_csv(f'{self.base_path}/gold.csv')
                print("✓ 金価格データを保存しました")
                return df
            elif existing_df is not None:
                print("✓ 新規データなし - 既存データを使用")
                return existing_df
            else:
                print("✗ データが取得できませんでした")
                return None
        except Exception as e:
            print(f"✗ 金価格データの取得に失敗: {str(e)}")
            return existing_df if existing_df is not None else None

    def get_google_trends_data(self):
        """Googleトレンドからビットコイン関連の検索トレンドを取得"""
        print("\nGoogleトレンドデータの取得を開始...")
        
        # 既存のデータを読み込む
        try:
            filepath = os.path.join(self.base_path, 'google_trends.csv')
            if os.path.exists(filepath):
                existing_df = pd.read_csv(filepath)
                existing_df['timestamp'] = pd.to_datetime(existing_df['date'])
                existing_df.set_index('timestamp', inplace=True)
                existing_df.drop('date', axis=1, errors='ignore', inplace=True)
                print(f"既存データ: {len(existing_df)}行")
                if existing_df.index[-1].date() >= self.end_date.date():
                    print("✓ 新規データなし - 既存データを使用")
                    return existing_df
            else:
                existing_df = None
        except Exception as e:
            print(f"既存データの読み込みをスキップ: {str(e)}")
            existing_df = None
        
        try:
            # 検索キーワードの設定
            keywords = ['bitcoin', 'BTC', 'crypto']
            self.pytrends.build_payload(
                kw_list=keywords,
                timeframe=f'{self.start_date.strftime("%Y-%m-%d")} {self.end_date.strftime("%Y-%m-%d")}'
            )
            
            # データの取得
            df = self.pytrends.interest_over_time()
            if df.empty:
                print("✗ トレンドデータが取得できませんでした")
                return existing_df if existing_df is not None else None
            
            # 不要な列を削除
            df = df.drop('isPartial', axis=1)
            
            # カラム名を変更
            df.columns = [f'{col} Trend' for col in df.columns]
            
            # インデックス名を変更
            df.index.name = 'timestamp'
            
            # 既存のデータとマージ
            if existing_df is not None:
                df = pd.concat([existing_df, df])
                df = df[~df.index.duplicated(keep='last')]
            
            df.sort_index(inplace=True)
            
            # CSVに保存（dateカラムを追加）
            df_to_save = df.copy()
            df_to_save['date'] = df_to_save.index
            df_to_save.to_csv(f'{self.base_path}/google_trends.csv', index=True)
            print("✓ Googleトレンドデータを保存しました")
            return df
            
        except Exception as e:
            print(f"✗ Googleトレンドデータの取得に失敗: {str(e)}")
            return existing_df if existing_df is not None else None

    def get_etf_data(self):
        """Yahoo FinanceからBitcoin ETFのデータを取得"""
        print("\nBitcoin ETFデータの取得を開始...")
        
        # 既存のデータを読み込む
        existing_df = self.load_existing_data('etf.csv')
        if existing_df is not None:
            print(f"既存データ: {len(existing_df)}行")
            missing_ranges = self.get_missing_date_ranges(existing_df)
        else:
            missing_ranges = [(self.start_date, self.end_date)]
        
        try:
            new_data = []
            for start, end in missing_ranges:
                # 日付範囲を1日単位で処理
                current_date = start
                while current_date <= end:
                    # 土日または祝日をスキップ
                    if current_date.weekday() >= 5 or not self.is_market_open(current_date):
                        print(f"✓ {current_date.strftime('%Y-%m-%d')} は休場日のためスキップします")
                        current_date += timedelta(days=1)
                        continue
                    
                    next_date = current_date + timedelta(days=1)
                    print(f"データ取得期間: {current_date.strftime('%Y-%m-%d')}")
                    
                    # 複数のBitcoin ETFのデータを取得
                    etf_symbols = ['GBTC', 'BITO']
                    daily_data = {}
                    
                    for symbol in etf_symbols:
                        try:
                            df = yf.download(symbol, start=current_date, end=next_date, progress=False)
                            if not df.empty:
                                # .item()を使用して明示的に数値を取得
                                price = df['Close'].iloc[0].item()
                                volume = df['Volume'].iloc[0].item()
                                flow = price * volume
                                
                                # 大きな数値を適切に処理
                                daily_data[f'{symbol} Price'] = price
                                daily_data[f'{symbol} Volume'] = volume
                                daily_data[f'{symbol} Flow'] = flow
                                
                                print(f"✓ {symbol}: Price=${price:,.2f}, Volume={volume:,.0f}, Flow=${flow:,.2f}")
                            else:
                                print(f"✓ {symbol}: {current_date.strftime('%Y-%m-%d')} の期間にデータがないためスキップします")
                        except Exception as e:
                            if "No price data found" in str(e):
                                print(f"✓ {symbol}: {current_date.strftime('%Y-%m-%d')} の期間は取引なしのためスキップします")
                            else:
                                print(f"✓ {symbol}: {current_date.strftime('%Y-%m-%d')} の期間のデータ取得をスキップ: {str(e)}")
                    
                    if daily_data:
                        daily_df = pd.DataFrame([daily_data], index=[current_date])
                        new_data.append(daily_df)
                    
                    current_date = next_date
            
            if new_data:
                new_df = pd.concat(new_data)
                new_df.index.name = 'timestamp'
                
                # 既存のデータとマージ
                if existing_df is not None:
                    df = pd.concat([existing_df, new_df])
                    df = df[~df.index.duplicated(keep='last')]
                else:
                    df = new_df
                
                # データ型を明示的に設定し、NaNを処理
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                df.sort_index(inplace=True)
                df.to_csv(f'{self.base_path}/etf.csv')
                print("✓ Bitcoin ETFデータを保存しました")
                return df
            elif existing_df is not None:
                print("✓ 新規データなし - 既存データを使用")
                return existing_df
            else:
                print("✗ データが取得できませんでした")
                return None
        except Exception as e:
            print(f"✗ Bitcoin ETFデータの取得に失敗: {str(e)}")
            return existing_df if existing_df is not None else None

    def collect_all_data(self):
        """全てのデータを収集"""
        print("="*50)
        print("データ収集を開始...")
        print(f"期間: {self.start_date.strftime('%Y-%m-%d')} から {self.end_date.strftime('%Y-%m-%d')}")
        print("="*50)
        
        results = {
            'large_holders': self.get_large_holders_data(),
            'btcusd': self.get_btcusd_data(),
            'dxy': self.get_dxy_data(),
            'sp500': self.get_sp500_data(),
            'gold': self.get_gold_data(),
            'etf': self.get_etf_data(),
            'google_trends': self.get_google_trends_data(),
            'funding_rates': self.get_funding_rates(),
            'fear_greed': self.get_fear_greed_index(),
            'open_interest': self.get_open_interest(),
            'trading_volume': self.get_trading_volume(),
            'active_addresses': self.get_active_addresses(),
            'hash_rate': self.get_hash_rate()
        }
        
        success_count = sum(1 for v in results.values() if v is not None)
        total_count = len(results)
        
        print("\n" + "="*50)
        print(f"データ収集完了: {success_count}/{total_count} 成功")
        print("="*50)
        return results if success_count > 0 else None

    def is_market_open(self, date):
        """指定された日付が取引日かどうかを確認"""
        schedule = self.nyse.schedule(start_date=date, end_date=date)
        return not schedule.empty

def calculate_rsi(data, periods=14):
    """
    RSI（Relative Strength Index）を計算する
    
    Args:
        data (pd.Series): 価格データ
        periods (int): 期間（デフォルト: 14日）
    
    Returns:
        pd.Series: RSI値（0-100の範囲）
    """
    # 価格変化を計算
    delta = data.diff()
    
    # 上昇・下降を分離
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    
    # RSを計算
    rs = gain / loss
    
    # RSIを計算（0-100の範囲）
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_moving_averages(data, periods=[21, 50, 200]):
    """
    単純移動平均（SMA）と指数移動平均（EMA）を計算する
    
    Args:
        data (pd.Series): 価格データ
        periods (list): 期間のリスト（デフォルト: [21, 50, 200]日）
    
    Returns:
        dict: 各期間のSMAとEMAのDataFrame
    """
    mas = {}
    for period in periods:
        # SMAの計算
        sma = data.rolling(window=period).mean()
        # EMAの計算
        ema = data.ewm(span=period, adjust=False).mean()
        
        mas[f'SMA_{period}'] = sma
        mas[f'EMA_{period}'] = ema
    
    return pd.DataFrame(mas)

def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """
    MACD（Moving Average Convergence Divergence）を計算する
    
    Args:
        data (pd.Series): 価格データ
        fast_period (int): 短期EMAの期間（デフォルト: 12）
        slow_period (int): 長期EMAの期間（デフォルト: 26）
        signal_period (int): シグナルラインの期間（デフォルト: 9）
    
    Returns:
        tuple: (MACD, シグナルライン, ヒストグラム)
    """
    # 短期と長期のEMAを計算
    ema_fast = data.ewm(span=fast_period, adjust=False).mean()
    ema_slow = data.ewm(span=slow_period, adjust=False).mean()
    
    # MACDラインを計算
    macd_line = ema_fast - ema_slow
    
    # シグナルラインを計算
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    
    # ヒストグラムを計算
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def calculate_correlation(price1, price2, window=30):
    """
    2つの価格系列間の相関係数を計算する
    
    Args:
        price1 (pd.Series): 1つ目の価格データ
        price2 (pd.Series): 2つ目の価格データ
        window (int): 相関を計算する期間（デフォルト: 30日）
    
    Returns:
        pd.Series: 相関係数の時系列
    """
    # 両方のデータを結合してリサンプリング
    df = pd.DataFrame({'price1': price1, 'price2': price2})
    df = df.dropna()
    
    # 日次変化率を計算
    returns1 = df['price1'].pct_change()
    returns2 = df['price2'].pct_change()
    
    # 相関係数を計算
    correlation = returns1.rolling(window=window).corr(returns2)
    
    return correlation

def plot_market_data(results):
    if not results:
        print("プロット可能なデータがありません")
        return

    valid_results = {k: v for k, v in results.items() if v is not None and not v.empty}
    if not valid_results:
        print("プロット可能なデータがありません")
        return

    # グラフスタイルの設定
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.rcParams.update({
        'figure.figsize': (24, 16),
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10
    })

    # カラーパレットの設定
    colors = {
        'btcusd': '#f39c12',      # オレンジ（ビットコインの伝統的な色）
        'large_holders': '#2ecc71', # 緑
        'funding_rates': '#e74c3c', # 赤
        'fear_greed': '#f1c40f',   # 黄色
        'open_interest': '#9b59b6', # 紫
        'trading_volume': '#3498db', # 青
        'active_addresses': '#1abc9c', # ターコイズ
        'hash_rate': '#e67e22',    # 濃いオレンジ
        'dxy': '#3498db',          # 青（ドル関連）
        'sp500': '#2ecc71',        # 緑（株式市場）
        'gold': '#f1c40f',         # 金色
        'correlation': '#e74c3c',   # 赤（相関係数）
        'gbtc': '#8e44ad',         # 紫（ETF）
        'bito': '#2980b9',         # 濃い青（ETF）
        'sma_21': '#3498db',       # 青
        'sma_50': '#2ecc71',       # 緑
        'sma_200': '#e74c3c',      # 赤
        'ema_21': '#9b59b6',       # 紫
        'ema_50': '#f1c40f',       # 黄
        'ema_200': '#e67e22',      # オレンジ
        'macd': '#2ecc71',         # 緑
        'signal': '#e74c3c',       # 赤
        'google_trends': {
            'bitcoin': '#3498db',   # 青
            'BTC': '#2ecc71',      # 緑
            'crypto': '#e74c3c'    # 赤
        }
    }

    # メインの図を作成
    fig = plt.figure(figsize=(24, 16))
    
    # グリッドを設定（4行3列）- BTCUSDは左上の大きなスペースを使用
    gs = gridspec.GridSpec(4, 3, height_ratios=[1.5, 1, 1, 1])

    # BTCUSDとRSIとMACDのサブプロット領域を作成（3:1:1の比率）
    gs_btc = gridspec.GridSpecFromSubplotSpec(3, 1, subplot_spec=gs[0, 0], height_ratios=[3, 1, 1], hspace=0.1)
    
    # 他のグラフ用のaxesリストを作成
    other_axes = []
    for i in range(1, 3):  # 上段の残り2つ
        other_axes.append(plt.subplot(gs[0, i]))
    for i in range(3):     # 2段目3つ
        other_axes.append(plt.subplot(gs[1, i]))
    for i in range(3):     # 3段目3つ
        other_axes.append(plt.subplot(gs[2, i]))
    for i in range(3):     # 4段目3つ
        other_axes.append(plt.subplot(gs[3, i]))

    # 指標の順序を定義（BTCUSDを除く）
    indicator_order = ['dxy', 'sp500', 'gold', 'etf', 'google_trends', 'large_holders', 'funding_rates', 
                      'fear_greed', 'open_interest', 'trading_volume', 'active_addresses']

    # BTCUSDの描画
    if 'btcusd' in valid_results:
        df = valid_results['btcusd']
        # BTCUSDの価格チャート
        ax_price = plt.subplot(gs_btc[0])
        
        # 移動平均線の計算と描画
        mas = calculate_moving_averages(df['BTCUSD Price'])
        
        # 価格の描画
        ax_price.plot(df.index, df['BTCUSD Price'],
                     label='BTCUSD',
                     color=colors['btcusd'],
                     marker='o',
                     markersize=2,
                     linewidth=1.5,
                     alpha=0.7)
        
        # 移動平均線の描画
        line_styles = {'SMA': '-', 'EMA': '--'}
        for col in mas.columns:
            ma_type, period = col.split('_')
            ax_price.plot(df.index, mas[col],
                        label=f'{ma_type}({period})',
                        color=colors[f'{ma_type.lower()}_{period}'],
                        linestyle=line_styles[ma_type],
                        linewidth=1,
                        alpha=0.6)

        ax_price.set_title('BTCUSD Price with Moving Averages', pad=20, fontweight='bold')
        ax_price.set_ylabel('Price (USD)')
        ax_price.grid(True, alpha=0.3)
        ax_price.legend(loc='upper left', ncol=2)
        plt.setp(ax_price.get_xticklabels(), visible=False)

        # RSIチャート
        ax_rsi = plt.subplot(gs_btc[1])
        rsi = calculate_rsi(df['BTCUSD Price'])
        ax_rsi.plot(df.index, rsi,
                   label='RSI (14)',
                   color='#e74c3c',
                   marker='o',
                   markersize=2,
                   linewidth=1.5,
                   alpha=0.7)
        ax_rsi.axhline(y=70, color='r', linestyle='--', alpha=0.2)
        ax_rsi.axhline(y=30, color='g', linestyle='--', alpha=0.2)
        ax_rsi.fill_between(df.index, 70, 100, color='r', alpha=0.05)
        ax_rsi.fill_between(df.index, 0, 30, color='g', alpha=0.05)
        ax_rsi.set_ylim(0, 100)
        ax_rsi.set_ylabel('RSI')
        ax_rsi.grid(True, alpha=0.3)
        ax_rsi.legend(loc='upper left')
        ax_rsi.tick_params(axis='x', rotation=45)

        # 最新の値をプロット上に表示（RSI）
        last_rsi = rsi.iloc[-1]
        last_date = rsi.index[-1]
        ax_rsi.annotate(f'{last_rsi:.2f}',
                      xy=(last_date, last_rsi),
                      xytext=(10, 0),
                      textcoords='offset points',
                      va='center')

        # 最新の値をプロット上に表示（BTCUSD）
        last_price = df['BTCUSD Price'].iloc[-1]
        ax_price.annotate(f'{last_price:.2f}',
                        xy=(last_date, last_price),
                        xytext=(10, 0),
                        textcoords='offset points',
                        va='center')

        # MACDチャート
        ax_macd = plt.subplot(gs_btc[2])
        macd_line, signal_line, histogram = calculate_macd(df['BTCUSD Price'])
        
        # ヒストグラムを描画
        ax_macd.bar(df.index, histogram,
                   label='MACD Histogram',
                   color=['g' if x >= 0 else 'r' for x in histogram],
                   alpha=0.3,
                   width=1)
        
        # MACDラインとシグナルラインを描画
        ax_macd.plot(df.index, macd_line,
                    label='MACD (12,26)',
                    color='#2ecc71',
                    linewidth=1.5)
        ax_macd.plot(df.index, signal_line,
                    label='Signal (9)',
                    color='#e74c3c',
                    linewidth=1.5)
        
        # ゼロラインを追加
        ax_macd.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        
        ax_macd.set_ylabel('MACD')
        ax_macd.grid(True, alpha=0.3)
        ax_macd.legend(loc='upper left')
        ax_macd.tick_params(axis='x', rotation=45)

        # 最新の値をプロット上に表示（MACD）
        last_macd = macd_line.iloc[-1]
        last_signal = signal_line.iloc[-1]
        last_date = df.index[-1]
        
        ax_macd.annotate(f'MACD: {last_macd:.2f}',
                       xy=(last_date, last_macd),
                       xytext=(10, 10),
                       textcoords='offset points',
                       va='bottom')
        ax_macd.annotate(f'Signal: {last_signal:.2f}',
                       xy=(last_date, last_signal),
                       xytext=(10, -10),
                       textcoords='offset points',
                       va='top')

    # 他の指標の描画
    for idx, name in enumerate(indicator_order):
        if name in valid_results and valid_results[name] is not None:
            df = valid_results[name]
            ax = other_axes[idx]
            
            if name == 'google_trends':
                # Googleトレンドの描画
                for column in df.columns:
                    keyword = column.split()[0]  # 'bitcoin Trend' から 'bitcoin' を取得
                    color = colors['google_trends'].get(keyword.lower(), '#2c3e50')
                    ax.plot(df.index, df[column],
                           label=column,
                           color=color,
                           marker='o',
                           markersize=2,
                           linewidth=1.5,
                           alpha=0.7)
                
                ax.set_title('Google Search Trends', pad=20, fontweight='bold')
                ax.set_ylabel('Search Interest')
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis='x', rotation=45)
                ax.legend(loc='upper left')

                # 最新の値をプロット上に表示
                last_date = df.index[-1]
                for i, column in enumerate(df.columns):
                    last_value = df[column].iloc[-1]
                    ax.annotate(f'{column}: {last_value:.0f}',
                               xy=(last_date, last_value),
                               xytext=(10, 10 + i*20),
                               textcoords='offset points',
                               va='bottom')

            elif name == 'dxy':
                # DXY価格の描画（左軸）
                ax.plot(df.index, df['DXY Price'],
                       label='DXY',
                       color=colors['dxy'],
                       marker='o',
                       markersize=2,
                       linewidth=1.5,
                       alpha=0.7)
                
                # 相関係数の描画（右軸）
                if 'btcusd' in valid_results:
                    ax2 = ax.twinx()
                    correlation = calculate_correlation(valid_results['btcusd']['BTCUSD Price'], df['DXY Price'])
                    ax2.plot(correlation.index, correlation,
                            label='BTC-DXY Correlation (30D)',
                            color=colors['correlation'],
                            linewidth=1.5,
                            alpha=0.7)
                    
                    # 相関軸の設定
                    ax2.set_ylabel('Correlation')
                    ax2.set_ylim(-1, 1)
                    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.3)
                    
                    # 凡例の結合
                    lines1, labels1 = ax.get_legend_handles_labels()
                    lines2, labels2 = ax2.get_legend_handles_labels()
                    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                
                ax.set_title('DXY & BTC Correlation', pad=20, fontweight='bold')
                ax.set_ylabel('DXY Price')
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis='x', rotation=45)

                # 最新の値をプロット上に表示
                last_dxy = df['DXY Price'].iloc[-1]
                last_date = df.index[-1]
                ax.annotate(f'DXY: {last_dxy:.2f}',
                           xy=(last_date, last_dxy),
                           xytext=(10, 10),
                           textcoords='offset points',
                           va='bottom')
                
                if 'btcusd' in valid_results and correlation is not None:
                    last_corr = correlation.iloc[-1]
                    ax2.annotate(f'Corr: {last_corr:.2f}',
                               xy=(last_date, last_corr),
                               xytext=(10, -10),
                               textcoords='offset points',
                               va='top')

            elif name == 'sp500':
                # S&P500価格の描画（左軸）
                ax.plot(df.index, df['SP500 Price'],
                       label='S&P500',
                       color=colors['sp500'],
                       marker='o',
                       markersize=2,
                       linewidth=1.5,
                       alpha=0.7)
                
                # 相関係数の描画（右軸）
                if 'btcusd' in valid_results:
                    ax2 = ax.twinx()
                    correlation = calculate_correlation(valid_results['btcusd']['BTCUSD Price'], df['SP500 Price'])
                    ax2.plot(correlation.index, correlation,
                            label='BTC-SP500 Correlation (30D)',
                            color=colors['correlation'],
                            linewidth=1.5,
                            alpha=0.7)
                    
                    # 相関軸の設定
                    ax2.set_ylabel('Correlation')
                    ax2.set_ylim(-1, 1)
                    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.3)
                    
                    # 凡例の結合
                    lines1, labels1 = ax.get_legend_handles_labels()
                    lines2, labels2 = ax2.get_legend_handles_labels()
                    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                
                ax.set_title('S&P500 & BTC Correlation', pad=20, fontweight='bold')
                ax.set_ylabel('S&P500 Price')
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis='x', rotation=45)

                # 最新の値をプロット上に表示
                last_sp500 = df['SP500 Price'].iloc[-1]
                last_date = df.index[-1]
                ax.annotate(f'S&P500: {last_sp500:.2f}',
                           xy=(last_date, last_sp500),
                           xytext=(10, 10),
                           textcoords='offset points',
                           va='bottom')
                
                if 'btcusd' in valid_results and correlation is not None:
                    last_corr = correlation.iloc[-1]
                    ax2.annotate(f'Corr: {last_corr:.2f}',
                               xy=(last_date, last_corr),
                               xytext=(10, -10),
                               textcoords='offset points',
                               va='top')

            elif name == 'gold':
                # 金価格の描画（左軸）
                ax.plot(df.index, df['Gold Price'],
                       label='Gold',
                       color=colors['gold'],
                       marker='o',
                       markersize=2,
                       linewidth=1.5,
                       alpha=0.7)
                
                # 相関係数の描画（右軸）
                if 'btcusd' in valid_results:
                    ax2 = ax.twinx()
                    correlation = calculate_correlation(valid_results['btcusd']['BTCUSD Price'], df['Gold Price'])
                    ax2.plot(correlation.index, correlation,
                            label='BTC-Gold Correlation (30D)',
                            color=colors['correlation'],
                            linewidth=1.5,
                            alpha=0.7)
                    
                    # 相関軸の設定
                    ax2.set_ylabel('Correlation')
                    ax2.set_ylim(-1, 1)
                    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.3)
                    
                    # 凡例の結合
                    lines1, labels1 = ax.get_legend_handles_labels()
                    lines2, labels2 = ax2.get_legend_handles_labels()
                    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                
                ax.set_title('Gold & BTC Correlation', pad=20, fontweight='bold')
                ax.set_ylabel('Gold Price (USD)')
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis='x', rotation=45)

                # 最新の値をプロット上に表示
                last_gold = df['Gold Price'].iloc[-1]
                last_date = df.index[-1]
                ax.annotate(f'Gold: {last_gold:.2f}',
                           xy=(last_date, last_gold),
                           xytext=(10, 10),
                           textcoords='offset points',
                           va='bottom')
                
                if 'btcusd' in valid_results and correlation is not None:
                    last_corr = correlation.iloc[-1]
                    ax2.annotate(f'Corr: {last_corr:.2f}',
                               xy=(last_date, last_corr),
                               xytext=(10, -10),
                               textcoords='offset points',
                               va='top')

            elif name == 'etf':
                # ETFデータの描画
                # 価格の描画（左軸）
                for symbol in ['GBTC', 'BITO']:
                    if f'{symbol} Price' in df.columns:
                        ax.plot(df.index, df[f'{symbol} Price'],
                               label=f'{symbol} Price',
                               color=colors[symbol.lower()],
                               marker='o',
                               markersize=2,
                               linewidth=1.5,
                               alpha=0.7)
                
                # 資金流入の描画（右軸）
                ax2 = ax.twinx()
                for symbol in ['GBTC', 'BITO']:
                    if f'{symbol} Flow' in df.columns:
                        flow_data = df[f'{symbol} Flow'].rolling(window=7).mean()
                        ax2.plot(df.index, flow_data,
                                label=f'{symbol} Flow (7D MA)',
                                color=colors[symbol.lower()],
                                linestyle='--',
                                linewidth=1.5,
                                alpha=0.5)
                
                # グラフの装飾
                ax.set_title('Bitcoin ETF Prices & Flows', pad=20, fontweight='bold')
                ax.set_ylabel('Price (USD)')
                ax2.set_ylabel('Flow (USD)')
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis='x', rotation=45)
                
                # 凡例の結合
                lines1, labels1 = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                
                # 最新の値をプロット上に表示
                last_date = df.index[-1]
                y_offset = 0
                for symbol in ['GBTC', 'BITO']:
                    if f'{symbol} Price' in df.columns:
                        last_price = df[f'{symbol} Price'].iloc[-1]
                        last_flow = df[f'{symbol} Flow'].iloc[-1]
                        ax.annotate(f'{symbol} Price: ${last_price:,.2f}',
                                   xy=(last_date, last_price),
                                   xytext=(10, y_offset),
                                   textcoords='offset points',
                                   va='bottom')
                        y_offset += 20
                        ax2.annotate(f'{symbol} Flow: ${last_flow:,.0f}',
                                   xy=(last_date, last_flow),
                                   xytext=(10, y_offset),
                                   textcoords='offset points',
                                   va='bottom')
                        y_offset += 20

            else:
                # 他の指標の描画
                if len(df.columns) > 1:
                    for j, column in enumerate(df.columns):
                        ax.plot(df.index, df[column],
                               label=column,
                               color=plt.cm.Set2(j),
                               marker='o',
                               markersize=4,
                               linewidth=2,
                               alpha=0.7)
                else:
                    column = df.columns[0]
                    ax.plot(df.index, df[column],
                           label=column,
                           color=colors.get(name, '#2c3e50'),
                           marker='o',
                           markersize=4,
                           linewidth=2,
                           alpha=0.7)

                # 最新の値をプロット上に表示
                for column in df.columns:
                    last_value = df[column].iloc[-1]
                    last_date = df.index[-1]
                    ax.annotate(f'{last_value:.2f}',
                               xy=(last_date, last_value),
                               xytext=(10, 0),
                               textcoords='offset points',
                               va='center')

                # グラフの装飾
                title = name.replace('_', ' ').title()
                ax.set_title(title, pad=20, fontweight='bold')
                ax.grid(True, alpha=0.3)
                ax.set_xlabel('Timestamp')

                # y軸ラベルとレンジの設定
                if name == 'funding_rates':
                    ax.set_ylabel('Funding Rate (%)')
                    ax.set_ylim(bottom=min(df['Funding Rate'].min() * 1.1, 0))
                elif name == 'fear_greed':
                    ax.set_ylabel('Fear & Greed Index')
                    ax.set_ylim(0, 100)
                elif name == 'large_holders':
                    ax.set_ylabel('Total BTC Holdings')
                    min_val = df['Total Holdings'].min()
                    max_val = df['Total Holdings'].max()
                    margin = (max_val - min_val) * 0.1
                    ax.set_ylim(min_val - margin, max_val + margin)
                    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
                elif name == 'open_interest':
                    ax.set_ylabel('Open Interest (BTC)')
                    min_val = df['Open Interest'].min()
                    max_val = df['Open Interest'].max()
                    margin = (max_val - min_val) * 0.1
                    ax.set_ylim(min_val - margin, max_val + margin)
                    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
                elif name == 'trading_volume':
                    ax.set_ylabel('Volume (USD)')
                    ax.set_ylim(bottom=0)
                elif name == 'active_addresses':
                    ax.set_ylabel('Number of Addresses')
                    ax.set_ylim(bottom=0)
                elif name == 'hash_rate':
                    ax.set_ylabel('Hash Rate (TH/s)')
                    ax.set_ylim(bottom=0)

                # x軸の日付フォーマットを設定
                ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig('crypto_analysis.png', dpi=300, bbox_inches='tight', facecolor='white')
    print("グラフを'crypto_analysis.png'として保存しました")

def main():
    print("暗号通貨データの収集と分析を開始します...")
    collector = DataCollector()
    results = collector.collect_all_data()
    
    if results:
        plot_market_data(results)
    else:
        print("データ収集に失敗したため、分析を実行できません")

if __name__ == "__main__":
    main() 