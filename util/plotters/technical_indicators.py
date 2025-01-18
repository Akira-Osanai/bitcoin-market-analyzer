import pandas as pd
from .base_plotter import BasePlotter

class TechnicalIndicators(BasePlotter):
    def calculate_rsi(self, data, periods=14):
        """RSI（Relative Strength Index）を計算する
        
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

    def calculate_moving_averages(self, data, periods=[21, 50, 200]):
        """単純移動平均（SMA）と指数移動平均（EMA）を計算する
        
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

    def calculate_macd(self, data, fast_period=12, slow_period=26, signal_period=9):
        """MACD（Moving Average Convergence Divergence）を計算する
        
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