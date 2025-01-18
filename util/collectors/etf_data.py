import yfinance as yf
import pandas as pd
from datetime import timedelta
from .base_collector import BaseCollector

class ETFDataCollector(BaseCollector):
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