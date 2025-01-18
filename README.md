# 暗号通貨分析ツール

このツールは、ビットコインの市場データを収集・分析・可視化するためのPythonスクリプトです。以下のデータを収集します：

- 大口保有者データ（CoinGecko API）
- 市場センチメント（CoinGecko API）
- 先物ファンディングレート（Binance API）
- Fear & Greed Index
- ビットコインの市場支配率

## セットアップ

1. 仮想環境の作成と有効化:
```bash
python -m venv venv
source venv/bin/activate  # Unix/macOS
# または
venv\Scripts\activate     # Windows
```

2. 必要なライブラリをインストール:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 使用方法

1. スクリプトを実行:
```bash
python crypto_analysis.py
```

スクリプトは以下の処理を行います：
- 各種市場データをAPIから取得
- CSVファイルとして`market_data`ディレクトリに保存
- 収集したデータを可視化したグラフを生成
- 結果を`crypto_analysis.png`として保存

## 出力ファイル

### CSVファイル（market_dataディレクトリ内）
- `large_holders.csv`: 大口保有者データ
- `market_sentiment.csv`: 市場センチメント
- `funding_rates.csv`: ファンディングレート
- `fear_greed.csv`: Fear & Greed Index
- `market_dominance.csv`: ビットコインの市場支配率

### グラフ
- `crypto_analysis.png`: 全データの時系列プロット