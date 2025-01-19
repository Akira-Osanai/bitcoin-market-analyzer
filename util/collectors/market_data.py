import yfinance as yf
import pandas as pd
from datetime import timedelta
from .base_collector import BaseCollector

class MarketDataCollector(BaseCollector):
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
                df = yf.download(ticker, start=start, end=end + timedelta(days=1))
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
                        df = yf.download("DX-Y.NYB", start=current_date, end=next_date, progress=False)
                        if not df.empty:
                            df_close = df[['Close']].copy()
                            df_close.columns = ['DXY Price']
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
                        df = yf.download("^GSPC", start=current_date, end=next_date, progress=False)
                        if not df.empty:
                            df_close = df[['Close']].copy()
                            df_close.columns = ['SP500 Price']
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