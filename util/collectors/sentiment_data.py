import os
import requests
import pandas as pd
from pytrends.request import TrendReq
from .base_collector import BaseCollector

class SentimentDataCollector(BaseCollector):
    def __init__(self):
        super().__init__()
        # PyTrendsの初期化
        self.pytrends = TrendReq(hl='en-US', tz=360)

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