import os
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas_market_calendars as mcal

class BaseCollector:
    def __init__(self):
        self.base_path = 'market_data'
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        # 1年間のデータ取得用の日付設定
        self.end_date = datetime.now()
        self.start_date = self.end_date - relativedelta(years=1)
        # 日付を00:00:00に設定
        self.end_date = self.end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        self.start_date = self.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        # NYSE（ニューヨーク証券取引所）のカレンダーを取得
        self.nyse = mcal.get_calendar('NYSE')
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
        """欠損している日付範囲を取得します。"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = self.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if existing_df is None or len(existing_df) == 0:
            print(f"新規データ収集期間: {start_date.date()} から {today.date()}")
            return [(start_date, today)]
        
        # 既存データの日付範囲を確認
        existing_dates = set(existing_df.index.date)
        all_dates = set(pd.date_range(start=start_date, end=today).date)
        missing_dates = sorted(all_dates - existing_dates)
        
        if not missing_dates:
            return []
        
        # 連続する日付範囲を特定
        ranges = []
        range_start = missing_dates[0]
        prev_date = missing_dates[0]
        
        for date in missing_dates[1:]:
            if (date - prev_date).days > 1:
                ranges.append((
                    datetime.combine(range_start, datetime.min.time()),
                    datetime.combine(prev_date, datetime.min.time())
                ))
                range_start = date
            prev_date = date
        
        ranges.append((
            datetime.combine(range_start, datetime.min.time()),
            datetime.combine(prev_date, datetime.min.time())
        ))
        
        print(f"データ収集が必要な期間:")
        for start, end in ranges:
            print(f"- {start.date()} から {end.date()}")
        
        return ranges

    def is_market_open(self, date):
        """指定された日付が取引日かどうかを確認"""
        schedule = self.nyse.schedule(start_date=date, end_date=date)
        return not schedule.empty 