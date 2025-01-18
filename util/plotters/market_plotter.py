import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from .base_plotter import BasePlotter
from .technical_indicators import TechnicalIndicators
from .correlation_plotter import CorrelationPlotter

class MarketPlotter(BasePlotter):
    def __init__(self):
        super().__init__()
        self.tech_indicators = TechnicalIndicators()
        self.corr_plotter = CorrelationPlotter()

    def calculate_market_signal(self, data):
        """市場シグナルを計算
        
        Args:
            data (dict): 各種市場データを含む辞書
        
        Returns:
            pd.Series: 市場シグナル（-2: 強い売り、-1: 売り、0: 中立、1: 買い、2: 強い買い）
        """
        if 'btcusd' not in data:
            return None

        btc_price = data['btcusd']['BTCUSD Price']
        signals = pd.Series(index=btc_price.index, dtype=float)

        # RSIによるシグナル（-1 to 1）
        rsi = self.tech_indicators.calculate_rsi(btc_price)
        rsi_signal = pd.Series(0, index=rsi.index)
        rsi_signal[rsi > 70] = -1  # 売られすぎ
        rsi_signal[rsi < 30] = 1   # 買われすぎ

        # MACDによるシグナル（-1 to 1）
        macd_line, signal_line, histogram = self.tech_indicators.calculate_macd(btc_price)
        macd_signal = pd.Series(0, index=macd_line.index)
        macd_signal[histogram > 0] = 1    # ゴールデンクロス
        macd_signal[histogram < 0] = -1   # デッドクロス

        # 移動平均によるシグナル（-1 to 1）
        mas = self.tech_indicators.calculate_moving_averages(btc_price)
        ma_signal = pd.Series(0, index=mas.index)
        ma_signal[btc_price > mas['SMA_200']] = 1     # 長期MAの上
        ma_signal[btc_price < mas['SMA_200']] = -1    # 長期MAの下

        # Fear & Greedインデックスによるシグナル（-1 to 1）
        if 'fear_greed' in data:
            fg = data['fear_greed']['Fear & Greed Value']
            fg_signal = pd.Series(0, index=fg.index)
            fg_signal[fg > 75] = -1   # 強気すぎ
            fg_signal[fg < 25] = 1    # 弱気すぎ
        else:
            fg_signal = pd.Series(0, index=btc_price.index)

        # 各シグナルの重み付け
        weights = {
            'rsi': 1.0,
            'macd': 1.5,
            'ma': 2.0,
            'fear_greed': 0.5
        }

        # 総合シグナルの計算
        total_signal = (
            weights['rsi'] * rsi_signal +
            weights['macd'] * macd_signal +
            weights['ma'] * ma_signal +
            weights['fear_greed'] * fg_signal
        ) / sum(weights.values())

        # シグナルを5段階に分類（-2 to 2）
        signals = pd.Series(0, index=total_signal.index)
        signals[total_signal <= -0.8] = -2    # 強い売り
        signals[(total_signal > -0.8) & (total_signal <= -0.3)] = -1  # 売り
        signals[(total_signal > -0.3) & (total_signal < 0.3)] = 0     # 中立
        signals[(total_signal >= 0.3) & (total_signal < 0.8)] = 1     # 買い
        signals[total_signal >= 0.8] = 2      # 強い買い

        return signals

    def plot_market_data(self, results):
        """市場データをプロット
        
        Args:
            results (dict): 各種市場データを含む辞書
        """
        if not results:
            print("プロット可能なデータがありません")
            return

        valid_results = {k: v for k, v in results.items() if v is not None and not v.empty}
        if not valid_results:
            print("プロット可能なデータがありません")
            return

        # シグナルの計算
        market_signals = self.calculate_market_signal(valid_results)

        # プロットスタイルの設定
        self.setup_plot_style()
        
        # グリッドの作成
        fig, gs, gs_btc, other_axes = self.create_grid()
        
        # BTCUSDのプロット（メイン、RSI、MACD）
        self.plot_btcusd_section(gs_btc, valid_results.get('btcusd'), market_signals)
        
        # その他のデータのプロット
        self.plot_other_data(other_axes, valid_results)
        
        # プロットの保存
        self.save_plot(fig)

    def plot_btcusd_section(self, gs_btc, btcusd_data, market_signals):
        """BTCUSDセクションのプロット
        
        Args:
            gs_btc: BTCUSDセクション用のGridSpec
            btcusd_data (pd.DataFrame): BTCUSDの価格データ
            market_signals (pd.Series): 市場シグナル
        """
        if btcusd_data is None:
            return

        # メインチャート
        ax_main = plt.subplot(gs_btc[0])
        
        # プロットの順序を調整
        # 1. データの範囲を設定
        ax_main.set_xlim(btcusd_data.index[0], btcusd_data.index[-1])
        min_price = btcusd_data['BTCUSD Price'].min()
        max_price = btcusd_data['BTCUSD Price'].max()
        price_margin = (max_price - min_price) * 0.1
        ax_main.set_ylim(min_price - price_margin, max_price + price_margin)
        
        # 2. シグナルの背景色を追加
        if market_signals is not None:
            self.add_signal_background(ax_main, market_signals)
        
        # 3. グリッドを描画
        ax_main.grid(True, alpha=0.3, zorder=1)
        
        # 4. 価格データをプロット
        ax_main.plot(btcusd_data.index, btcusd_data['BTCUSD Price'],
                    color=self.colors['btcusd'], label='BTCUSD', zorder=2)
        
        # 5. 移動平均線の追加
        mas = self.tech_indicators.calculate_moving_averages(btcusd_data['BTCUSD Price'])
        for period in [21, 50, 200]:
            ax_main.plot(mas.index, mas[f'SMA_{period}'],
                        color=self.colors[f'sma_{period}'],
                        label=f'SMA {period}', alpha=0.7, zorder=2)
        
        self.format_axis(ax_main, 'Bitcoin Price (USD)', ylabel='Price')
        ax_main.legend(loc='upper left')
        
        # RSIのプロット
        ax_rsi = plt.subplot(gs_btc[1])
        rsi = self.tech_indicators.calculate_rsi(btcusd_data['BTCUSD Price'])
        ax_rsi.plot(rsi.index, rsi, color=self.colors['btcusd'])
        ax_rsi.axhline(y=70, color='red', linestyle='--', alpha=0.5)
        ax_rsi.axhline(y=30, color='green', linestyle='--', alpha=0.5)
        ax_rsi.set_ylim(0, 100)
        self.format_axis(ax_rsi, 'RSI (14)', ylabel='RSI')
        
        # MACDのプロット
        ax_macd = plt.subplot(gs_btc[2])
        macd_line, signal_line, histogram = self.tech_indicators.calculate_macd(btcusd_data['BTCUSD Price'])
        ax_macd.plot(macd_line.index, macd_line, color=self.colors['macd'], label='MACD')
        ax_macd.plot(signal_line.index, signal_line, color=self.colors['signal'], label='Signal')
        ax_macd.bar(histogram.index, histogram, color=self.colors['btcusd'], alpha=0.3)
        self.format_axis(ax_macd, 'MACD', ylabel='MACD')
        ax_macd.legend(loc='upper left')

    def plot_other_data(self, axes, data):
        """その他のデータをプロット
        
        Args:
            axes (list): プロット用のAxesリスト
            data (dict): プロットするデータの辞書
        """
        ax_index = 0
        
        # 相関プロット
        if 'btcusd' in data:
            btc_price = data['btcusd']['BTCUSD Price']
            
            # DXYとの相関
            if 'dxy' in data and ax_index < len(axes):
                correlation = self.corr_plotter.calculate_correlation(
                    btc_price, data['dxy']['DXY Price'])
                self.corr_plotter.plot_correlation(
                    axes[ax_index], correlation, 'BTC-DXY Correlation', 'BTC', 'DXY')
                ax_index += 1
            
            # S&P500との相関
            if 'sp500' in data and ax_index < len(axes):
                correlation = self.corr_plotter.calculate_correlation(
                    btc_price, data['sp500']['SP500 Price'])
                self.corr_plotter.plot_correlation(
                    axes[ax_index], correlation, 'BTC-S&P500 Correlation', 'BTC', 'S&P500')
                ax_index += 1
        
        # その他のデータプロット
        plot_configs = [
            ('large_holders', 'Total Holdings', 'Large Holders'),
            ('funding_rates', 'Funding Rate', 'Funding Rates (%)'),
            ('fear_greed', 'Fear & Greed Value', 'Fear & Greed Index'),
            ('open_interest', 'Open Interest', 'Open Interest (BTC)'),
            ('trading_volume', 'Trading Volume', 'Volume (USD)'),
            ('active_addresses', 'Active Addresses', 'Number of Addresses'),
            ('hash_rate', 'Hash Rate', 'Hash Rate (TH/s)'),
            ('coinbase_premium', 'Coinbase Premium', 'Premium (%)'),
            ('etf', 'GBTC Price', 'GBTC Price (USD)')
        ]

        for name, column, title in plot_configs:
            if name in data and ax_index < len(axes):
                df = data[name]
                if column in df.columns:
                    axes[ax_index].plot(df.index, df[column],
                                      color=self.colors.get(name, '#333333'))
                    self.format_axis(axes[ax_index], title)
                    
                    # 特別な設定
                    if name == 'fear_greed':
                        axes[ax_index].set_ylim(0, 100)
                    elif name == 'open_interest':
                        axes[ax_index].yaxis.set_major_formatter(
                            plt.FuncFormatter(lambda x, p: format(int(x), ',')))
                    
                ax_index += 1 