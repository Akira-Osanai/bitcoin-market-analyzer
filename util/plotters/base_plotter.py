import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.gridspec as gridspec

class BasePlotter:
    def __init__(self):
        # カラーパレットの設定
        self.colors = {
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
            'coinbase_premium': '#16a085', # ターコイズ
            'google_trends': {
                'bitcoin': '#3498db',   # 青
                'BTC': '#2ecc71',      # 緑
                'crypto': '#e74c3c'    # 赤
            }
        }

    def setup_plot_style(self):
        """プロットのスタイルを設定"""
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams.update({
            'figure.figsize': (24, 20),
            'font.size': 10,
            'axes.titlesize': 12,
            'axes.labelsize': 10
        })

    def create_grid(self):
        """グリッドを作成"""
        fig = plt.figure(figsize=(24, 20))
        gs = gridspec.GridSpec(5, 3, height_ratios=[1.5, 1, 1, 1, 1])
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
        for i in range(3):     # 5段目3つ
            other_axes.append(plt.subplot(gs[4, i]))
        
        return fig, gs, gs_btc, other_axes

    def format_axis(self, ax, title, ylabel=None):
        """軸のフォーマットを設定"""
        ax.set_title(title)
        if ylabel:
            ax.set_ylabel(ylabel)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)

    def save_plot(self, fig, filename='crypto_analysis.png'):
        """プロットを保存"""
        plt.tight_layout()
        fig.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"グラフを'{filename}'として保存しました") 