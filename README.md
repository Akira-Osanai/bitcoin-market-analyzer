# Bitcoin Market Analysis Tool

ビットコイン市場の包括的な分析を行うためのツールです。価格データ、オンチェーン指標、市場センチメント、相関分析など、複数の指標を組み合わせて市場トレンドを分析します。

## 機能

- 複数の指標の自動データ収集と可視化
- 既存データの確認と必要なデータのみの取得
- 休場日（週末・祝日）のスキップ
- テクニカル指標の自動計算（RSI、MACD、移動平均）
- 相関分析（DXY、S&P500、Gold）
- ETFフロー分析
- グラフの自動生成と保存

## 収集する指標

### 価格指標
- BTCUSD価格データ
- 移動平均（21日、50日、200日）
- RSI（14日）
- MACD

### 相関指標
- DXY（米ドル指数）相関
- S&P500相関
- Gold相関

### オンチェーン指標
- 大口保有者データ
- アクティブアドレス数
- ハッシュレート

### 市場指標
- Fear & Greedインデックス
- ファンディングレート
- オープンインタレスト
- 取引量
- ETFフロー（GBTC、BITO）
- Googleトレンド（bitcoin、BTC、crypto）

## セットアップ

1. リポジトリのクローン:
```bash
git clone https://github.com/yourusername/bitcoin-market-analyzer.git
cd bitcoin-market-analyzer
```

2. 仮想環境の作成と有効化:
```bash
python -m venv venv
source venv/bin/activate  # Unix/macOS
# または
.\venv\Scripts\activate  # Windows
```

3. 依存パッケージのインストール:
```bash
pip install -r requirements.txt
```

## 使用方法

1. スクリプトの実行:
```bash
python crypto_analysis.py
```

2. 出力ファイル:
- 各指標のCSVファイルが `market_data/` ディレクトリに保存されます
- グラフは `crypto_analysis.png` として保存されます

## データ更新

- スクリプトは既存のCSVファイルをチェックし、必要な期間のデータのみを取得します
- 週末や祝日のデータは自動的にスキップされます
- 各APIの制限に応じて適切な待機時間が設定されています

## 分析ガイド

詳細な市場分析の方法については、[ANALYSIS_GUIDE.md](ANALYSIS_GUIDE.md)を参照してください。

## 注意事項

- CSVファイルはGitの管理対象外です（.gitignoreに設定済み）
- 一部のデータ取得にはAPIキーが必要な場合があります
- 投資判断は自己責任で行ってください

## ライセンス

MIT License

## プロジェクト構造

```
bitcoin-market-analyzer/
├── crypto_analysis.py      # メインスクリプト
├── requirements.txt        # 依存パッケージ
├── README.md              # プロジェクト説明
├── ANALYSIS_GUIDE.md      # 分析ガイド
└── util/
    ├── data_collector.py   # データ収集メインクラス
    ├── plot_market_data.py # プロット機能のエントリーポイント
    ├── collectors/        # データ収集モジュール
    │   ├── base_collector.py
    │   ├── market_data.py
    │   ├── onchain_data.py
    │   ├── derivative_data.py
    │   ├── sentiment_data.py
    │   ├── exchange_data.py
    │   └── etf_data.py
    └── plotters/          # プロット機能モジュール
        ├── base_plotter.py
        ├── technical_indicators.py
        ├── correlation_plotter.py
        └── market_plotter.py
```

### モジュール説明

#### データ収集モジュール
- `base_collector.py`: 基本的なデータ収集機能
- `market_data.py`: 価格データの収集（BTCUSD、DXY、S&P500、Gold）
- `onchain_data.py`: オンチェーンデータの収集
- `derivative_data.py`: デリバティブデータの収集
- `sentiment_data.py`: センチメントデータの収集
- `exchange_data.py`: 取引所データの収集
- `etf_data.py`: ETFデータの収集

#### プロットモジュール
- `base_plotter.py`: 基本的なプロット設定
- `technical_indicators.py`: テクニカル指標の計算
- `correlation_plotter.py`: 相関分析のプロット
- `market_plotter.py`: メインのプロット機能