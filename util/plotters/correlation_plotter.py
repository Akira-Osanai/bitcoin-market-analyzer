import pandas as pd
from .base_plotter import BasePlotter

class CorrelationPlotter(BasePlotter):
    def calculate_correlation(self, price1, price2, window=30):
        """2つの価格系列間の相関係数を計算する
        
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

    def plot_correlation(self, ax, correlation, title, asset1_name, asset2_name):
        """相関係数をプロット
        
        Args:
            ax (matplotlib.axes.Axes): プロット対象のAxes
            correlation (pd.Series): 相関係数の時系列
            title (str): グラフのタイトル
            asset1_name (str): 資産1の名前
            asset2_name (str): 資産2の名前
        """
        ax.plot(correlation.index, correlation.values, 
                color=self.colors['correlation'], 
                label=f'{asset1_name} vs {asset2_name}')
        
        # 相関係数の範囲を-1から1に設定
        ax.set_ylim(-1, 1)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        
        # 軸のフォーマット
        self.format_axis(ax, title, ylabel='Correlation') 