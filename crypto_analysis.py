import requests
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import os
import seaborn as sns

class DataCollector:
    def __init__(self):
        self.base_path = 'market_data'
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        # 1年間のデータ取得用の日付設定
        self.end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.start_date = (self.end_date - relativedelta(years=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        print(f"データ収集期間: {self.start_date} から {self.end_date}")

    def load_existing_data(self, filename):
        """既存のCSVファイルからデータを読み込む"""
        filepath = os.path.join(self.base_path, filename)
        if os.path.exists(filepath):
            try:
                if filename in ['btcusd.csv', 'large_holders.csv']:
                    df = pd.read_csv(filepath, index_col='Date', parse_dates=True)
                else:
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
            df.index.name = 'Date'
            
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

    def collect_all_data(self):
        """全てのデータを収集"""
        print("="*50)
        print("データ収集を開始...")
        print(f"期間: {self.start_date.strftime('%Y-%m-%d')} から {self.end_date.strftime('%Y-%m-%d')}")
        print("="*50)
        
        results = {
            'large_holders': self.get_large_holders_data(),
            'btcusd': self.get_btcusd_data(),
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

def plot_market_data(results):
    """収集したデータをプロット"""
    if not results:
        print("プロット可能なデータがありません")
        return

    valid_results = {k: v for k, v in results.items() if v is not None and not v.empty}
    if not valid_results:
        print("プロット可能なデータがありません")
        return

    # BTCUSDを最初に、残りのデータを順番に並べる
    ordered_results = {}
    if 'btcusd' in valid_results:
        ordered_results['btcusd'] = valid_results['btcusd']
    ordered_results.update({k: v for k, v in valid_results.items() if k != 'btcusd'})
    valid_results = ordered_results

    # グラフスタイルの設定
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.rcParams.update({
        'figure.figsize': (20, 16),  # 図のサイズを大きくする
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10
    })
    
    # カラーパレットの設定
    colors = {
        'large_holders': '#2ecc71',      # 緑
        'btcusd': '#f39c12',            # オレンジ
        'funding_rates': '#e74c3c',      # 赤
        'fear_greed': '#f1c40f',         # 黄
        'open_interest': '#9b59b6',      # 紫
        'trading_volume': '#3498db',     # 青
        'active_addresses': '#1abc9c',   # ターコイズ
        'hash_rate': '#e67e22'           # オレンジ濃い
    }
    
    # 2列4行のサブプロットを作成
    fig, axs = plt.subplots(4, 2)
    axs = axs.flatten()  # 2次元配列を1次元に変換
    
    for i, (name, df) in enumerate(valid_results.items()):
        title = name.replace('_', ' ').title()
        color = colors.get(name, '#2c3e50')
        
        # データ型に応じてプロット方法を変更
        if len(df.columns) > 1:  # 複数の列がある場合
            for j, column in enumerate(df.columns):
                axs[i].plot(df.index, df[column], 
                          label=column, 
                          color=plt.cm.Set2(j), 
                          marker='o', 
                          markersize=4, 
                          linewidth=2, 
                          alpha=0.7)
        else:  # 単一の列の場合
            column = df.columns[0]
            axs[i].plot(df.index, df[column], 
                      label=column, 
                      color=color, 
                      marker='o', 
                      markersize=4, 
                      linewidth=2, 
                      alpha=0.7)
        
        # 最新の値をプロット上に表示
        for column in df.columns:
            last_value = df[column].iloc[-1]
            last_date = df.index[-1]
            axs[i].annotate(f'{last_value:.2f}', 
                          xy=(last_date, last_value),
                          xytext=(10, 0), 
                          textcoords='offset points',
                          va='center')
        
        # グラフの装飾
        axs[i].set_title(title, pad=20, fontweight='bold')
        axs[i].grid(True, alpha=0.3)
        axs[i].set_xlabel('Timestamp')
        
        # y軸ラベルとレンジの設定
        if name == 'funding_rates':
            axs[i].set_ylabel('Funding Rate (%)')
            axs[i].set_ylim(bottom=min(df['Funding Rate'].min() * 1.1, 0))
        elif name == 'fear_greed':
            axs[i].set_ylabel('Fear & Greed Index')
            axs[i].set_ylim(0, 100)
        elif name == 'large_holders':
            axs[i].set_ylabel('Total BTC Holdings')
            # Large Holdersの表示範囲を調整
            min_val = df['Total Holdings'].min()
            max_val = df['Total Holdings'].max()
            margin = (max_val - min_val) * 0.1  # 10%のマージン
            axs[i].set_ylim(min_val - margin, max_val + margin)
            # Y軸のフォーマットを設定（千単位でカンマ区切り）
            axs[i].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        elif name == 'btcusd':
            axs[i].set_ylabel('Price (USD)')
            axs[i].set_ylim(bottom=0)
        elif name == 'open_interest':
            axs[i].set_ylabel('Open Interest (BTC)')
            # Open Interestの表示範囲を調整
            min_val = df['Open Interest'].min()
            max_val = df['Open Interest'].max()
            margin = (max_val - min_val) * 0.1  # 10%のマージン
            axs[i].set_ylim(min_val - margin, max_val + margin)
            # Y軸のフォーマットを設定（千単位でカンマ区切り）
            axs[i].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        elif name == 'trading_volume':
            axs[i].set_ylabel('Volume (USD)')
            axs[i].set_ylim(bottom=0)
        elif name == 'active_addresses':
            axs[i].set_ylabel('Number of Addresses')
            axs[i].set_ylim(bottom=0)
        elif name == 'hash_rate':
            axs[i].set_ylabel('Hash Rate (TH/s)')
            axs[i].set_ylim(bottom=0)
        
        # 凡例の設定
        if df.shape[1] > 1:
            axs[i].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        else:
            axs[i].legend(loc='upper right')
        
        # x軸の日付フォーマットを設定
        axs[i].tick_params(axis='x', rotation=45)
    
    # 余分なサブプロットを非表示にする
    for i in range(len(valid_results), len(axs)):
        axs[i].set_visible(False)
            
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